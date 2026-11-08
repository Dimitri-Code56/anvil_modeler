"""Montagem do grafo LangGraph.

concept → [plan → verify_api → retrieve]* → code → guard → execute → render → evaluate
modo agente: concept → plan → agente (loop de ferramentas MCP) → render → evaluate
                                  ↑                                   │
                                  └──── (loop: reprovado e iter < N) ─┘
* plan só com use_skills; verify_api (nomes conferidos ao vivo no Blender) e retrieve só com use_rag.
Erros de guardrail/execução/render pulam direto para evaluate,
que registra a tentativa e decide se volta para code.
"""
from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from .blender import BlenderClient
from .config import Settings, settings as default_settings
from .nodes import make_nodes
from .state import AnvilState


def build_graph(blender: BlenderClient, settings: Settings = default_settings):
    n = make_nodes(blender, settings)
    g = StateGraph(AnvilState)
    for name, fn in n.items():
        g.add_node(name, fn)

    g.add_edge(START, "concept")
    g.add_conditional_edges("concept", lambda s: "plan" if s.get("use_skills") or s.get("use_agent") else "code",
                            ["plan", "code"])
    g.add_conditional_edges(
        "plan",
        lambda s: "agente" if s.get("use_agent") else ("verify_api" if s.get("use_rag") else "code"),
        ["agente", "verify_api", "code"],
    )
    # modo agente: o loop fica dentro do nó (chamada → resultado → próxima chamada)
    g.add_conditional_edges("agente", lambda s: "evaluate" if s.get("exec_error") else "render", ["evaluate", "render"])
    g.add_edge("verify_api", "retrieve")
    g.add_edge("retrieve", "code")
    g.add_edge("code", "guard")
    g.add_conditional_edges("guard", lambda s: "evaluate" if s.get("guard_error") else "execute", ["evaluate", "execute"])
    g.add_conditional_edges("execute", lambda s: "evaluate" if s.get("exec_error") else "render", ["evaluate", "render"])
    g.add_edge("render", "evaluate")

    def after_evaluate(s: AnvilState) -> str:
        approved = (s.get("evaluation") or {}).get("approved", False)
        if s.get("use_loop") and not approved and s.get("iteration", 0) < s.get("max_iters", 1):
            return "code"
        return END

    g.add_conditional_edges("evaluate", after_evaluate, ["code", END])
    return g.compile()
