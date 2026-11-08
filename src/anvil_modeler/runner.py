"""Executa uma rodada completa: abre o MCP, roda o grafo, mede e salva o resultado."""
from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Awaitable, Callable

from langchain_core.callbacks import get_usage_metadata_callback

from .blender import OFFSET, BlenderClient, collection_name
import os

from .config import MODES, Settings, price_for, settings as default_settings
from .graph import build_graph

OnUpdate = Callable[[str, dict], Awaitable[None] | None]


def usage_summary(raw: dict) -> dict:
    """Tokens por modelo + total. Multiplique pelo preço de cada modelo para o custo."""
    per_model = {}
    for model, u in raw.items():
        details = u.get("input_token_details") or {}
        per_model[model] = {
            "input": u.get("input_tokens", 0),
            "output": u.get("output_tokens", 0),
            "cache_read": details.get("cache_read", 0),
            "cache_write": details.get("cache_creation", 0),
        }
    total = {k: sum(m[k] for m in per_model.values()) for k in ("input", "output", "cache_read", "cache_write")}
    # custo: o cache lido/escrito já vem dentro de "input"; cobramos a parte comum pelo preço cheio
    cost, unknown = 0.0, []
    for model, m in per_model.items():
        p = price_for(model)
        if p is None:
            unknown.append(model)
            continue
        plain = max(0, m["input"] - m["cache_read"] - m["cache_write"])
        c = (plain * p[0] + m["output"] * p[1] + m["cache_write"] * p[2] + m["cache_read"] * p[3]) / 1e6
        m["cost_usd"] = round(c, 6)
        cost += c
    out = {"per_model": per_model, "total": total, "cost_usd": round(cost, 6)}
    rate = os.getenv("ANVIL_USD_BRL")
    if rate:
        out["cost_brl"] = round(cost * float(rate), 4)
    if unknown:
        out["sem_preco"] = unknown
    return out


def make_run_id(asset_name: str, mode: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", asset_name.lower()).strip("-")
    return f"{slug}_{mode}_{datetime.now():%Y%m%d-%H%M%S}"


async def run_once(
    description: str,
    asset_name: str,
    mode: str = "full",
    concept_path: str | None = None,
    style: str | None = None,
    project: str | None = None,
    max_iters: int | None = None,
    run_id: str | None = None,
    on_update: OnUpdate | None = None,
    settings: Settings = default_settings,
) -> dict:
    if mode not in MODES:
        raise ValueError(f"Modo inválido: {mode}. Opções: {list(MODES)}")
    run_id = run_id or make_run_id(asset_name, mode)
    flags = MODES[mode]
    initial = {
        "run_id": run_id, "asset_name": asset_name, "description": description,
        "concept_path": concept_path, "iteration": 0, "attempts": [],
        "style": style or settings.default_style, "project": project or None,
        "scene_key": f"{asset_name}_{mode}",
        "max_iters": (max_iters or settings.max_iters) if flags["use_loop"] else 1,
        **flags,
    }

    with get_usage_metadata_callback() as usage_cb:
        async with BlenderClient(settings.mcp_servers()) as blender:
            graph = build_graph(blender, settings)
            final: dict = {}
            async for kind, chunk in graph.astream(initial, stream_mode=["updates", "values"]):
                if kind == "values":
                    final = chunk
                elif on_update:
                    for node, update in chunk.items():
                        r = on_update(node, update or {})
                        if hasattr(r, "__await__"):
                            await r
            try:
                metrics = await blender.metrics(initial["scene_key"])
            except Exception as e:
                metrics = {"error": str(e)}
            try:  # deixa cada modo lado a lado na cena, para comparar no Blender
                await blender.execute(OFFSET.format(coll=collection_name(initial["scene_key"]), slot=list(MODES).index(mode)))
            except Exception:
                pass

    attempts = final.get("attempts", [])
    from .geometria import budget_check, budget_for
    cat = (final.get("spec") or {}).get("category")
    if isinstance(metrics, dict) and "tris" in metrics:
        lo, hi = budget_for(settings.alvo, cat)
        metrics["orcamento"] = {"alvo": settings.alvo, "categoria": cat, "min": lo, "max": hi,
                                "aviso": budget_check(metrics["tris"], settings.alvo, cat)}
    result = {
        "run_id": run_id, "mode": mode, "asset_name": asset_name, "description": description,
        "style": initial["style"], "project": initial["project"],
        "concept_path": final.get("concept_path"), "spec": final.get("spec"),
        "iterations": len(attempts),
        "final_score": attempts[-1]["score"] if attempts else None,
        "final_render": attempts[-1]["render_path"] if attempts else None,
        "technical_errors": sum(1 for a in attempts if a.get("guard_error") or a.get("exec_error")),
        "metrics": metrics, "usage": usage_summary(usage_cb.usage_metadata),
        "attempts": attempts,
    }
    out_dir = settings.runs_dir / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "run.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    if attempts:
        (out_dir / "final_code.py").write_text(attempts[-1]["code"], encoding="utf-8")
    return result
