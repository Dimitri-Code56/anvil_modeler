"""Uso: anvil "descrição" --name carro --mode full [--style realista] [--project elpis] [--concept img.png]"""
from __future__ import annotations

import argparse
import asyncio
import json

from .config import MODES, settings
from .runner import run_once
from .skills import available_projects, available_styles


def main() -> None:
    p = argparse.ArgumentParser(prog="anvil")
    p.add_argument("description")
    p.add_argument("--name", required=True, help="nome do asset (vira prefixo dos objetos)")
    p.add_argument("--mode", default="full", choices=list(MODES))
    p.add_argument("--concept", help="caminho de um concept art pronto (pula o gerador)")
    p.add_argument("--max-iters", type=int)
    p.add_argument("--style", choices=available_styles(settings.skills_dir), help="padrão: realista")
    p.add_argument("--project", choices=available_projects(settings.skills_dir), help="regras de um projeto (opcional)")
    p.add_argument("--sem-juiz", action="store_true", help="desliga o juiz visual (loop só para erros técnicos)")
    p.add_argument("--max-usd", type=float, help="teto de custo do agente por run, em US$ (ex.: 2)")
    p.add_argument("--alvo", choices=["jogo", "completo"], help="orçamento de polígonos: jogo (padrão) ou completo (render)")
    p.add_argument("--perfil", choices=["auto", "forte", "fraco"], help="modo agente: forte escreve bpy, fraco usa as ferramentas prontas")
    a = p.parse_args()
    if a.sem_juiz:
        settings.judge_enabled = False
    if a.perfil:
        settings.perfil = a.perfil
    if a.alvo:
        settings.alvo = a.alvo
    if a.max_usd is not None:
        settings.max_usd = a.max_usd

    def log(node: str, update: dict) -> None:
        ev = update.get("evaluation")
        extra = f" nota={ev['score']}" if ev and ev.get("score") is not None else ""
        err = update.get("exec_error") or update.get("guard_error")
        print(f"[{node}]{extra}" + (f" ERRO: {[l for l in err.strip().splitlines() if l.strip()][-1][:200]}" if err else ""))

    result = asyncio.run(run_once(
        a.description, a.name, a.mode, concept_path=a.concept, style=a.style,
        project=a.project, max_iters=a.max_iters, on_update=log,
    ))
    print(json.dumps({k: result[k] for k in ("run_id", "iterations", "final_score", "metrics", "usage")}, indent=2, ensure_ascii=False))
    orc = (result.get("metrics") or {}).get("orcamento") or {}
    if orc:
        print(f"Triângulos: {result['metrics'].get('tris')} (orçamento {orc['alvo']}: {orc['min']}–{orc['max']})"
              + (f"  AVISO: {orc['aviso']}" if orc.get("aviso") else ""))
    u = result["usage"]
    custo = f"US$ {u.get('cost_usd', 0):.4f}" + (f" (R$ {u['cost_brl']:.2f})" if "cost_brl" in u else "")
    print(f"\nTokens: {u['total']['input']} de entrada, {u['total']['output']} de saída. Custo deste asset: {custo}"
          + (f"  [sem preço cadastrado: {', '.join(u['sem_preco'])}]" if u.get("sem_preco") else ""))
    print(f"O modelo ficou no Blender, na coleção ANVIL_{a.name}_{a.mode}. Renders e código em runs/{result['run_id']}/")


if __name__ == "__main__":
    main()
