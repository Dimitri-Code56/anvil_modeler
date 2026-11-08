"""Comparativo sem harness vs com harness.

    python experiments/run_benchmark.py                      # todos os assets, todos os modos, 1 repetição
    python experiments/run_benchmark.py --modes baseline full --repeats 3 --only caixote_suprimentos

Saídas em runs/benchmark_<data>/: results.csv, results.json e grid.png
(linhas = assets, colunas = modos). A coluna `human_score` fica vazia
para vocês preencherem às cegas.
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import json
from datetime import datetime
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

from anvil_modeler.config import MODES, settings
from anvil_modeler.nodes import judge_render
from anvil_modeler.runner import run_once


async def ensure_concept(asset: dict, out_dir: Path) -> str | None:
    if asset.get("concept"):
        return asset["concept"]
    if settings.image_backend == "none":
        return None
    from anvil_modeler.image_gen import generate_concept
    from anvil_modeler.llm import get_llm, text_of
    from anvil_modeler.prompts import CONCEPT_PREFIX, CONCEPT_PROMPT

    style = asset.get("style") or settings.default_style
    msg = await get_llm(settings.fast_model, 300, settings.fast_provider).ainvoke(CONCEPT_PROMPT.format(description=asset["description"], style=style))
    path = out_dir / f"concept_{asset['name']}.png"
    return await asyncio.to_thread(generate_concept, CONCEPT_PREFIX + text_of(msg).strip(), path)


def build_grid(rows: list[dict], assets: list[str], modes: list[str], out: Path, cell: int = 256) -> None:
    label_w, label_h = 180, 28
    grid = Image.new("RGB", (label_w + cell * len(modes), label_h + cell * len(assets)), "white")
    draw = ImageDraw.Draw(grid)
    for j, m in enumerate(modes):
        draw.text((label_w + j * cell + 8, 8), m, fill="black")
    for i, a in enumerate(assets):
        draw.text((8, label_h + i * cell + cell // 2), a, fill="black")
        for j, m in enumerate(modes):
            match = [r for r in rows if r["asset"] == a and r["mode"] == m and r["render"]]
            if not match:
                continue
            r = match[0]  # primeira repetição
            img = Image.open(r["render"]).convert("RGB").resize((cell, cell))
            x, y = label_w + j * cell, label_h + i * cell
            grid.paste(img, (x, y))
            draw.rectangle([x, y, x + 70, y + 18], fill="black")
            draw.text((x + 4, y + 3), "-" if r["blind_score"] is None else f"{r['blind_score']:.1f}/5", fill="white")
    grid.save(out)


async def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--assets", default=str(Path(__file__).with_name("assets.yaml")))
    p.add_argument("--modes", nargs="+", default=list(MODES), choices=list(MODES))
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--only", nargs="*", help="rodar só estes assets")
    a = p.parse_args()

    assets = yaml.safe_load(Path(a.assets).read_text(encoding="utf-8"))["assets"]
    if a.only:
        assets = [x for x in assets if x["name"] in a.only]
    out_dir = settings.runs_dir / f"benchmark_{datetime.now():%Y%m%d-%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for asset in assets:
        concept = await ensure_concept(asset, out_dir)  # mesmo concept para todos os modos
        for mode in a.modes:
            for rep in range(a.repeats):
                print(f"▶ {asset['name']} | {mode} | rep {rep + 1}")
                res = await run_once(
                    asset["description"], asset["name"], mode, concept_path=concept,
                    style=asset.get("style"), project=asset.get("project"),
                )
                blind = None
                if res["final_render"] and settings.judge_enabled:
                    state = {"description": asset["description"], "concept_path": concept,
                             "style": res["style"], "project": res["project"]}
                    blind = (await judge_render(settings, state, res["final_render"])).score
                m = res["metrics"]
                rows.append({
                    "asset": asset["name"], "style": res["style"], "project": res["project"] or "",
                    "mode": mode, "rep": rep + 1, "run_id": res["run_id"],
                    "iterations": res["iterations"], "technical_errors": res["technical_errors"],
                    "loop_score": res["final_score"], "blind_score": blind, "human_score": "",
                    "objects": m.get("objects"), "faces": m.get("faces"), "raw_boxes": m.get("raw_boxes"),
                    "modifiers": m.get("modifiers"), "materials": m.get("materials"),
                    "nonmanifold_edges": m.get("nonmanifold_edges"),
                    "input_tokens": res["usage"]["total"]["input"], "output_tokens": res["usage"]["total"]["output"],
                    "render": res["final_render"],
                })
                (out_dir / "results.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")

    with open(out_dir / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    build_grid(rows, [x["name"] for x in assets], a.modes, out_dir / "grid.png")
    print(f"✔ Resultados em {out_dir}")


if __name__ == "__main__":
    asyncio.run(main())
