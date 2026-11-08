"""Gera docs/grafo_harness.png a partir do grafo REAL (graph.py), como no notebook:

    Image(graph.get_graph().draw_mermaid_png())

Uso: python scripts/desenhar_grafo.py
Não precisa do Blender aberto nem de créditos da API: o grafo só é montado, não executado.
"""
import os
from pathlib import Path

os.environ.setdefault("ANTHROPIC_API_KEY", "nao-usada-so-para-montar-o-grafo")

from anvil_modeler.graph import build_graph  # noqa: E402

graph = build_graph(blender=None)  # o cliente MCP só é usado quando os nós rodam
out = Path(__file__).resolve().parents[1] / "docs" / "grafo_harness.png"
out.parent.mkdir(exist_ok=True)
out.write_bytes(graph.get_graph().draw_mermaid_png())
print(graph.get_graph().draw_mermaid())
print(f"✔ {out}")
