"""Gera docs/grafo_harness.png a partir do grafo REAL (graph.py), como no notebook:

    Image(graph.get_graph().draw_mermaid_png())

Uso: python scripts/desenhar_grafo.py
Não precisa do Blender aberto nem de créditos da API: o grafo só é montado, não executado.
"""
import os
from pathlib import Path

os.environ.setdefault("ANTHROPIC_API_KEY", "nao-usada-so-para-montar-o-grafo")

from anvil_modeler.graph import build_graph  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

graph = build_graph(blender=None)  # o cliente MCP só é usado quando os nós rodam
out = ROOT / "docs" / "grafo_harness.png"
out.parent.mkdir(exist_ok=True)
out.write_bytes(graph.get_graph().draw_mermaid_png())
print(graph.get_graph().draw_mermaid())
print(f"✔ {out}")

# --- grafo do assistente de perguntas (o agente do chat, com guardrails, avaliar/reescrever) ---
try:
    from anvil_modeler.config import settings
    from anvil_modeler.rag.assistente import Recursos, build_chat_graph

    rec = Recursos(settings)                     # usa o índice que já vem no repositório
    chat = build_chat_graph(rec, checkpointer=None)
    out2 = ROOT / "docs" / "grafo_chat.png"
    out2.write_bytes(chat.get_graph().draw_mermaid_png())
    print(chat.get_graph().draw_mermaid())
    print(f"✔ {out2}")
except Exception as e:                           # sem índice/modelo: o PNG do harness já saiu
    print(f"✘ grafo do chat não gerado ({str(e)[:120]})")
