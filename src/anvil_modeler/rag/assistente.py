"""Assistente de perguntas sobre o Blender: RAG agêntico em LangGraph.

    START → guardrail_entrada ─(bloqueado)→ END
                 │
                 ▼
              agente ──(chama ferramenta)──► ferramentas ──(buscou)──► avaliar ─(relevante)─► agente
                 │                               │                        │
                 │                          (skill/MCP)              (não relevante e
                 │                               └──► agente          reescritas < 2)
                 │                                                        ▼
                 │                                                   reescrever ──► avaliar
                 ▼
          guardrail_saida → END

- agente: o modelo decide se busca na documentação, carrega uma skill do catálogo ou chama uma
  ferramenta MCP (verificar_api no Blender aberto), ou se já responde.
- avaliar / reescrever: a parte "agêntica" do RAG; se os trechos não servem, a busca é reformulada
  (com os termos da documentação, em inglês) e refeita, no máximo 2 vezes.
- guardrails: entrada (regras + classificador barato) e saída (segredos, código perigoso, fontes).
- memória: checkpointer do LangGraph por thread_id (conversa), ver app/chat.py.
"""
from __future__ import annotations

import json
import re
from typing import Annotated, Any, Literal, Optional, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from ..guardrails import check_code
from ..llm import get_llm, structured, text_of
from ..skills import list_skills
from . import prompts
from .embeddings import get_embedder
from .index import DocIndex

MAX_REESCRITAS = 2
MAX_RODADAS = 4            # rodadas de ferramentas por pergunta (trava contra loop)
K_TRECHOS = 4
TRECHO_CHARS = 1400
SKILLS_SEMPRE = ("responder-com-fontes",)

# ---------------------------------------------------------------- guardrails --
INJECAO = [
    r"(ignor|desconsider|esque[cç]|sobrescrev)\w*\s.{0,40}(instru|regra|prompt|orienta|diretriz)",
    r"(prompt|instru[cç](ao|ão|oes|ões))\s+(do\s+|de\s+)?sistema|system\s*prompt",
    r"(^|[\s/\\'\"`])\.env\b|(api|secret)[\s_-]*key|chave\s+(da\s+|de\s+)?api|anthropic_api|token\s+de\s+acesso",
    r"\b(senha|password)s?\b",
    r"rm\s+-rf|format\s+c:|del\s+/[sq]|shutdown\s+/|mkfs",
]
SEGREDO = re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}|(?i:(api[_-]?key|secret|token)\s*[:=]\s*['\"]?[A-Za-z0-9_\-]{16,})")
RECUSA = {
    "fora_do_tema": "Eu só respondo dúvidas sobre o Blender e 3D. Pode perguntar sobre modelagem, modificadores, "
                    "malha, materiais e nós, ou scripts bpy.",
    "malicioso": "Não posso ajudar com isso. Se tiver alguma dúvida sobre o Blender (modelagem, materiais, scripts bpy), "
                 "é só perguntar.",
    "longo": "A mensagem ficou longa demais (limite de 4.000 caracteres). Pode resumir a dúvida?",
}


class Classificacao(BaseModel):
    categoria: Literal["blender", "saudacao", "fora_do_tema", "malicioso"]
    motivo: str = Field(description="uma frase curta")


class Avaliacao(BaseModel):
    relevante: bool
    motivo: str = Field(description="uma frase curta")


# ---------------------------------------------------- ferramentas do agente --
@tool
def buscar_documentacao(consulta: str) -> str:
    """Busca na documentação oficial do Blender (manual + API Python). Use termos em inglês da documentação,
    como nomes de modificadores, nós, operadores ou classes."""
    return ""


@tool
def carregar_skill(nome: str) -> str:
    """Carrega as instruções completas de uma skill do catálogo, pelo nome."""
    return ""


class ChatState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    pergunta: str
    categoria: str
    bloqueado: bool
    documentos: list[dict]      # trechos desta pergunta, na ordem das citações [1], [2]...
    consultas: list[str]
    reescritas: int
    rodadas: int
    ultima_busca: bool
    relevante: Optional[bool]
    skills: list[str]
    trace: list[str]


class Recursos:
    """Tudo que o grafo usa: índice, embeddings, modelo, skills e ferramentas MCP (opcionais)."""

    def __init__(self, settings, index: Optional[DocIndex] = None, llm: Any = None, mcp_tools: Optional[list] = None,
                 embed_query: Any = "auto"):
        self.settings = settings
        self.index = index if index is not None else DocIndex.load(settings.index_dir)
        if embed_query == "auto":
            emb = get_embedder(settings.embed_model, settings.ollama_url) if self.index.vectors is not None else None
            embed_query = emb[1] if emb else None
        self.embed_query = embed_query
        self.llm = llm if llm is not None else get_llm(settings.rag_model, 12000, settings.rag_provider)
        self.mcp_tools = list(mcp_tools or [])
        self.skills = {s.name: s for s in list_skills(settings.skills_dir) if s.layer == "assistente"}

    def buscar(self, consulta: str, k: int = K_TRECHOS) -> list[dict]:
        return self.index.search(consulta, k=k, embed_query=self.embed_query)

    def catalogo(self) -> str:
        return "\n".join(f"- {s.name}: {s.description}" for s in self.skills.values()) or "(vazio)"


# ------------------------------------------------------------- utilidades --
def _pergunta_atual(messages: list) -> tuple[int, str]:
    for i in range(len(messages) - 1, -1, -1):
        m = messages[i]
        if isinstance(m, HumanMessage):
            return i, text_of(m)
    return 0, ""


def _historico(messages: list, max_anteriores: int = 10) -> list:
    """Turnos anteriores só com pergunta e resposta final (sem ferramentas); o turno atual inteiro."""
    i, _ = _pergunta_atual(messages)
    antes = []
    for m in messages[:i]:
        if isinstance(m, HumanMessage):
            antes.append(HumanMessage(content=text_of(m)))
        elif isinstance(m, AIMessage) and not m.tool_calls and text_of(m).strip():
            antes.append(AIMessage(content=text_of(m)))
    return antes[-max_anteriores:] + list(messages[i:])


def _sem_thinking(msgs: list) -> list:
    """Cópia das mensagens sem os blocos 'thinking' das respostas anteriores do modelo."""
    out = []
    for m in msgs:
        if isinstance(m, AIMessage) and isinstance(m.content, list):
            blocos = [b for b in m.content if not (isinstance(b, dict) and b.get("type") in ("thinking", "redacted_thinking"))]
            out.append(AIMessage(content=blocos or "", tool_calls=m.tool_calls, id=m.id))
        else:
            out.append(m)
    return out


def formatar_trechos(resultados: list[dict], docs: list[dict]) -> tuple[str, list[dict]]:
    """Numera os trechos (reaproveitando o número de um trecho já citado nesta pergunta)."""
    docs = list(docs)
    ids = {d["id"]: n for n, d in enumerate(docs, 1)}
    linhas = []
    for r in resultados:
        n = ids.get(r["id"])
        if n is None:
            docs.append({k: r.get(k) for k in ("id", "arquivo", "titulo", "secao", "url", "fonte")})
            n = ids[r["id"]] = len(docs)
        corpo = r["texto"] if len(r["texto"]) <= TRECHO_CHARS else r["texto"][:TRECHO_CHARS] + " […]"
        linhas.append(f"[{n}] {r['titulo']} — {r['secao']} ({r.get('url', '')})\n{corpo}")
    return ("\n\n---\n\n".join(linhas) if linhas else "Nenhum trecho encontrado para essa busca."), docs


async def avaliar_trechos(llm, provider: str, pergunta: str, trechos: str) -> tuple[bool, str]:
    try:
        grader = structured(llm, Avaliacao, provider)
        av: Avaliacao = await grader.ainvoke([SystemMessage(prompts.AVALIADOR),
                                              HumanMessage(f"Pergunta: {pergunta}\n\nTrechos:\n{trechos[:6000]}")])
        return bool(av.relevante), av.motivo
    except Exception as e:                       # avaliador falhou: segue com o que tem
        return True, f"avaliação indisponível ({str(e)[:60]})"


async def reescrever_consulta(llm, pergunta: str, consultas: list[str]) -> str:
    msg = await llm.ainvoke([SystemMessage(prompts.REESCRITOR),
                             HumanMessage(f"Pergunta: {pergunta}\nBuscas que não serviram: {consultas}")])
    nova = text_of(msg).strip().splitlines()[0] if text_of(msg).strip() else pergunta
    return nova.strip().strip('"').strip("`")[:200]


async def busca_agentica(rec: Recursos, pergunta: str, consulta: Optional[str] = None,
                         max_reescritas: int = MAX_REESCRITAS) -> tuple[list[dict], list[str], list[bool]]:
    """O laço buscar → avaliar → reescrever fora do grafo (usado na avaliação do RAG)."""
    consultas, avaliacoes, docs = [], [], []
    q = consulta or pergunta
    for tentativa in range(max_reescritas + 1):
        res = rec.buscar(q)
        consultas.append(q)
        texto, _ = formatar_trechos(res, [])
        ok, _ = await avaliar_trechos(rec.llm, rec.settings.rag_provider, pergunta, texto)
        avaliacoes.append(ok)
        docs = res
        if ok or tentativa == max_reescritas:
            break
        q = await reescrever_consulta(rec.llm, pergunta, consultas)
    return docs, consultas, avaliacoes


# ------------------------------------------------------------------ grafo --
def build_chat_graph(rec: Recursos, checkpointer=None):
    s = rec.settings
    provider = s.rag_provider

    async def guardrail_entrada(state: ChatState) -> dict:
        _, texto = _pergunta_atual(state["messages"])
        reset = {"pergunta": texto, "documentos": [], "consultas": [], "reescritas": 0, "rodadas": 0,
                 "ultima_busca": False, "relevante": None, "skills": list(SKILLS_SEMPRE)}
        if len(texto) > 4000:
            cat, motivo = "longo", "mensagem longa demais"
        elif any(re.search(p, texto, re.I) for p in INJECAO):
            cat, motivo = "malicioso", "padrão de injeção ou pedido de segredo"
        else:
            try:
                c: Classificacao = await structured(rec.llm, Classificacao, provider).ainvoke(
                    [SystemMessage(prompts.CLASSIFICADOR), HumanMessage(texto)])
                cat, motivo = c.categoria, c.motivo
            except Exception as e:                # classificador indisponível: as regras acima já passaram
                cat, motivo = "blender", f"classificador indisponível ({str(e)[:60]})"
        if cat in ("fora_do_tema", "malicioso", "longo"):
            return {**reset, "categoria": cat, "bloqueado": True,
                    "messages": [AIMessage(content=RECUSA[cat], additional_kwargs={
                        "trace": [f"guardrail_entrada: bloqueado ({cat}: {motivo})"], "fontes": []})],
                    "trace": [f"guardrail_entrada: bloqueado ({cat}: {motivo})"]}
        return {**reset, "categoria": cat, "bloqueado": False, "trace": [f"guardrail_entrada: ok ({cat})"]}

    async def agente(state: ChatState) -> dict:
        rodadas = state.get("rodadas", 0)
        ferramentas = [buscar_documentacao, carregar_skill] + rec.mcp_tools
        extras = ""
        if rec.mcp_tools:
            extras = ("- `verificar_api(itens)`: confere no Blender aberto se nomes da API existem nesta versão "
                      "(use antes de entregar código com nomes que você não viu nos trechos).\n")
        # só as skills fixas entram no sistema: o prompt de sistema não pode mudar no meio da pergunta (o raciocínio
        # do modelo vem assinado contra ele e a API recusa se mudar). Skills carregadas chegam pelo resultado da ferramenta.
        carregadas = "\n\n".join(f"## Skill carregada: {n}\n{rec.skills[n].body}"
                                 for n in SKILLS_SEMPRE if n in rec.skills)
        system = prompts.ASSISTENTE.format(versao=s.blender_version, ferramentas_extras=extras,
                                           catalogo=rec.catalogo(),
                                           skills_carregadas=("\n" + carregadas) if carregadas else "")
        sys_msg = (SystemMessage(content=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}])
                   if provider == "anthropic" else SystemMessage(system))
        model = rec.llm.bind_tools(ferramentas) if rodadas < MAX_RODADAS else rec.llm
        msgs = [sys_msg] + _historico(state["messages"])
        try:
            ai = await model.ainvoke(msgs)
        except Exception as e:
            if "signature" not in str(e) or "thinking" not in str(e):
                raise
            # a API recusou um bloco de raciocínio assinado (ex.: prompt de sistema mudou entre versões do app):
            # remove os blocos de raciocínio antigos e tenta de novo, como a própria mensagem de erro sugere
            ai = await model.ainvoke(_sem_thinking(msgs))
        if not getattr(ai, "tool_calls", None) and not text_of(ai).strip():
            motivo = (getattr(ai, "response_metadata", {}) or {}).get("stop_reason", "?")
            ai = await rec.llm.ainvoke(_sem_thinking(msgs) + [HumanMessage(
                "Sua resposta saiu vazia (limite de tamanho). Escreva agora a resposta final em texto, mais curta: "
                "se for código, entregue só a estrutura principal e explique como estender.")])
            ai.additional_kwargs = {**(ai.additional_kwargs or {}), "vazia_antes": motivo}
        if not getattr(ai, "tool_calls", None) and provider != "anthropic":
            from ..agent import parse_text_calls          # modelo local escrevendo a chamada como texto
            nomes = {t.name for t in ferramentas}
            achadas = parse_text_calls(text_of(ai), nomes)
            if achadas:
                ai = AIMessage(content="", tool_calls=[{"name": c["name"], "args": c["args"], "id": f"txt_{rodadas}_{k}"}
                                                       for k, c in enumerate(achadas)])
        vazia = (ai.additional_kwargs or {}).get("vazia_antes")
        acao = (", ".join(f"{c['name']}({json.dumps(c['args'], ensure_ascii=False)[:80]})" for c in ai.tool_calls)
                if ai.tool_calls else ("respondeu" + (f" (2a tentativa; a 1a veio vazia: {vazia})" if vazia else "")))
        return {"messages": [ai], "rodadas": rodadas + (1 if ai.tool_calls else 0),
                "trace": state.get("trace", []) + [f"agente: {acao}"]}

    async def ferramentas(state: ChatState) -> dict:
        ai = state["messages"][-1]
        docs = list(state.get("documentos") or [])
        consultas = list(state.get("consultas") or [])
        skills = list(state.get("skills") or [])
        trace = list(state.get("trace", []))
        mcp = {t.name: t for t in rec.mcp_tools}
        tms, buscou = [], False
        for c in ai.tool_calls:
            args = c.get("args") or {}
            if c["name"] == "buscar_documentacao":
                q = str(args.get("consulta", ""))[:300] or state.get("pergunta", "")
                res = rec.buscar(q)
                texto, docs = formatar_trechos(res, docs)
                consultas.append(q)
                buscou = True
                trace.append(f"buscar_documentacao('{q}') -> {len(res)} trechos: "
                             + "; ".join(f"{r['titulo']} › {r['secao']}"[:70] for r in res[:3]))
            elif c["name"] == "carregar_skill":
                nome = str(args.get("nome", "")).strip()
                if nome in rec.skills:
                    texto = rec.skills[nome].body
                    if nome not in skills:
                        skills.append(nome)
                    trace.append(f"carregar_skill('{nome}')")
                else:
                    texto = f"Skill '{nome}' não existe. Catálogo:\n{rec.catalogo()}"
                    trace.append(f"carregar_skill('{nome}') -> não existe")
            elif c["name"] in mcp:
                try:
                    out = await mcp[c["name"]].ainvoke(args)
                    texto = text_of(out) if hasattr(out, "content") else (out if isinstance(out, str) else json.dumps(out, ensure_ascii=False, default=str))
                    trace.append(f"MCP {c['name']} -> ok")
                except Exception as e:
                    texto = f"ERRO: {str(e)[:400]} (o Blender está aberto com o servidor do add-on ligado?)"
                    trace.append(f"MCP {c['name']} -> erro")
            else:
                texto = f"Ferramenta '{c['name']}' não existe."
            tms.append(ToolMessage(content=str(texto)[:12000], tool_call_id=c["id"], name=c["name"]))
        return {"messages": tms, "documentos": docs, "consultas": consultas, "skills": skills,
                "ultima_busca": buscou, "trace": trace}

    async def avaliar(state: ChatState) -> dict:
        ultimo = next((m for m in reversed(state["messages"])
                       if isinstance(m, ToolMessage) and m.name == "buscar_documentacao"), None)
        ok, motivo = await avaliar_trechos(rec.llm, provider, state.get("pergunta", ""), text_of(ultimo) if ultimo else "")
        return {"relevante": ok, "trace": state.get("trace", []) + [f"avaliar: {'relevante' if ok else 'não serve'} ({motivo})"]}

    async def reescrever(state: ChatState) -> dict:
        n = state.get("reescritas", 0) + 1
        nova = await reescrever_consulta(rec.llm, state.get("pergunta", ""), state.get("consultas", []))
        res = rec.buscar(nova)
        texto, docs = formatar_trechos(res, state.get("documentos") or [])
        call_id = f"reescrita_{n}"
        ai = AIMessage(content="", tool_calls=[{"name": "buscar_documentacao", "args": {"consulta": nova}, "id": call_id}],
                       additional_kwargs={"harness": "reescrita"})
        tm = ToolMessage(content=texto, tool_call_id=call_id, name="buscar_documentacao")
        return {"messages": [ai, tm], "documentos": docs, "consultas": state.get("consultas", []) + [nova],
                "reescritas": n, "trace": state.get("trace", []) + [f"reescrever #{n}: '{nova}' -> {len(res)} trechos"]}

    async def guardrail_saida(state: ChatState) -> dict:
        last = state["messages"][-1]
        txt = text_of(last)
        trace = list(state.get("trace", []))
        avisos = []
        if not txt.strip():
            txt = ("Não consegui escrever a resposta desta vez (ela ficou longa demais). Tente pedir em partes, "
                   "por exemplo: primeiro as paredes, depois o telhado, depois o material de tijolo.")
            avisos.append("resposta vazia")
        limpo = SEGREDO.sub("[removido pelo guardrail]", txt)
        if limpo != txt:
            avisos.append("segredo removido")
        for code in re.findall(r"```(?:python|py)?\s*\n(.*?)```", limpo, re.S):
            erro = check_code(code, armadilhas=False)
            if erro:
                avisos.append(f"código: {erro}")
                limpo += (f"\n\n> ⚠️ Atenção: o código acima faz algo que o guardrail do Anvil bloquearia "
                          f"({erro}). Revise antes de rodar.")
        docs = state.get("documentos") or []
        citados = sorted({int(n) for n in re.findall(r"\[(\d+)\]", limpo) if 0 < int(n) <= len(docs)})
        usados = citados or list(range(1, min(len(docs), 3) + 1))
        fontes = [{"n": n, "titulo": docs[n - 1]["titulo"], "secao": docs[n - 1]["secao"], "url": docs[n - 1]["url"]}
                  for n in usados]
        agrupadas: dict[tuple, list[int]] = {}           # mesma página e seção: uma linha com os números juntos
        for f in fontes:
            agrupadas.setdefault((f["titulo"], f["secao"], f["url"]), []).append(f["n"])
        if fontes and "Fontes" not in limpo:
            limpo += "\n\n**Fontes:**\n" + "\n".join(
                f"- {''.join(f'[{n}]' for n in ns)} {tit}" + (f" — {sec}" if sec and sec != tit else "") + f": {url}"
                for (tit, sec, url), ns in agrupadas.items())
        if docs and not citados:
            avisos.append("resposta sem citações [n]")
        trace.append("guardrail_saida: " + ("; ".join(avisos) if avisos else "ok"))
        meta = {"trace": trace, "fontes": fontes, "consultas": state.get("consultas", []),
                "reescritas": state.get("reescritas", 0), "skills": state.get("skills", [])}
        return {"messages": [AIMessage(content=limpo, id=last.id, additional_kwargs=meta)], "trace": trace}

    g = StateGraph(ChatState)
    for nome, fn in (("guardrail_entrada", guardrail_entrada), ("agente", agente), ("ferramentas", ferramentas),
                     ("avaliar", avaliar), ("reescrever", reescrever), ("guardrail_saida", guardrail_saida)):
        g.add_node(nome, fn)
    g.add_edge(START, "guardrail_entrada")
    g.add_conditional_edges("guardrail_entrada", lambda st: END if st.get("bloqueado") else "agente", ["agente", END])
    g.add_conditional_edges("agente", lambda st: "ferramentas" if getattr(st["messages"][-1], "tool_calls", None)
                            else "guardrail_saida", ["ferramentas", "guardrail_saida"])
    g.add_conditional_edges("ferramentas", lambda st: "avaliar" if st.get("ultima_busca") else "agente",
                            ["avaliar", "agente"])
    g.add_conditional_edges("avaliar", lambda st: "agente" if st.get("relevante") or st.get("reescritas", 0) >= MAX_REESCRITAS
                            else "reescrever", ["agente", "reescrever"])
    g.add_edge("reescrever", "avaliar")
    g.add_edge("guardrail_saida", END)
    return g.compile(checkpointer=checkpointer)
