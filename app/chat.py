"""Chat do Anvil: dúvidas sobre o Blender respondidas com a documentação oficial (RAG agêntico).

    streamlit run app/chat.py

Memória: cada conversa é uma thread do LangGraph salva em SQLite (data/memoria.sqlite), então o
assistente lembra do que foi falado mesmo depois de fechar o app.
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime

import streamlit as st
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from anvil_modeler.config import price_for, settings
from anvil_modeler.rag.assistente import Recursos, build_chat_graph

st.set_page_config(page_title="Anvil · assistente de Blender", page_icon="🔨", layout="centered")

NOS = {"guardrail_entrada": "Conferindo a pergunta", "agente": "Pensando", "ferramentas": "Buscando na documentação",
       "avaliar": "Avaliando os trechos encontrados", "reescrever": "Reformulando a busca",
       "guardrail_saida": "Conferindo a resposta"}
CONVERSAS = settings.memory_db.parent / "conversas.json"


# ----------------------------------------------------------- recursos ------
async def _carregar_mcp() -> list:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    servers = settings.mcp_servers()
    if "anvil" not in servers:
        return []
    tools = await MultiServerMCPClient({"anvil": servers["anvil"]}).get_tools()
    return [t for t in tools if t.name == "verificar_api"]


@st.cache_resource(show_spinner="Carregando o índice da documentação…")
def recursos(usar_mcp: bool) -> tuple[Recursos | None, str]:
    aviso = ""
    mcp = []
    if usar_mcp:
        try:
            mcp = asyncio.run(_carregar_mcp())
        except Exception as e:
            aviso = f"MCP do Blender indisponível ({str(e)[:80]}); o chat segue só com a documentação."
    try:
        return Recursos(settings, mcp_tools=mcp), aviso
    except FileNotFoundError as e:
        return None, str(e)


def conversas() -> list[dict]:
    try:
        return json.loads(CONVERSAS.read_text(encoding="utf-8"))
    except Exception:
        return []


def salvar_conversas(lista: list[dict]) -> None:
    CONVERSAS.parent.mkdir(parents=True, exist_ok=True)
    CONVERSAS.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")


def custo(usage: dict) -> float:
    total = 0.0
    for modelo, u in usage.items():
        p = price_for(modelo)
        if not p:
            continue
        cr = (u.get("input_token_details") or {}).get("cache_read", 0) or 0
        total += ((u.get("input_tokens", 0) - cr) * p[0] + cr * p[3] + u.get("output_tokens", 0) * p[1]) / 1e6
    return total


# ---------------------------------------------------------- grafo -----------
async def historico(rec: Recursos, thread: str) -> list:
    settings.memory_db.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(settings.memory_db)) as saver:
        snap = await build_chat_graph(rec, saver).aget_state({"configurable": {"thread_id": thread}})
        return (snap.values or {}).get("messages", [])


async def perguntar(rec: Recursos, thread: str, texto: str, status) -> tuple[list, dict]:
    cfg = {"configurable": {"thread_id": thread}}
    async with AsyncSqliteSaver.from_conn_string(str(settings.memory_db)) as saver:
        g = build_chat_graph(rec, saver)
        with get_usage_metadata_callback() as cb:
            async for upd in g.astream({"messages": [HumanMessage(texto)]}, cfg, stream_mode="updates"):
                for no, val in upd.items():
                    linha = (val or {}).get("trace", [""])[-1] if isinstance(val, dict) else ""
                    status.update(label=NOS.get(no, no) + "…")
                    status.write(f"**{no}** — {linha}" if linha else f"**{no}**")
        snap = await g.aget_state(cfg)
        return snap.values.get("messages", []), cb.usage_metadata


def mostrar(m, mostrar_trace: bool) -> None:
    if isinstance(m, HumanMessage):
        with st.chat_message("user"):
            st.markdown(m.content)
    elif isinstance(m, AIMessage) and not m.tool_calls and m.content:
        with st.chat_message("assistant", avatar="🔨"):
            st.markdown(m.content)
            meta = m.additional_kwargs or {}
            if mostrar_trace and meta.get("trace"):
                with st.expander("Como cheguei nesta resposta"):
                    for t in meta["trace"]:
                        st.markdown(f"- {t}")
                    if meta.get("skills"):
                        st.caption("Skills usadas: " + ", ".join(meta["skills"]))


# --------------------------------------------------------------- tela -------
with st.sidebar:
    st.title("🔨 Anvil")
    st.caption(f"Dúvidas sobre o Blender {settings.blender_version}, com a documentação oficial")
    lista = conversas()
    if "thread" not in st.session_state:
        st.session_state.thread = lista[0]["id"] if lista else None
    if st.button("➕ Nova conversa", use_container_width=True):
        st.session_state.thread = None
        st.rerun()
    for c in lista[:20]:
        rotulo = ("▶ " if c["id"] == st.session_state.thread else "") + c["titulo"]
        if st.button(rotulo, key=c["id"], use_container_width=True):
            st.session_state.thread = c["id"]
            st.rerun()
    st.divider()
    usar_mcp = st.toggle("Conferir nomes no Blender aberto (MCP)", value=settings.chat_mcp,
                         help="Usa a ferramenta verificar_api do servidor anvil-tools; precisa do Blender aberto.")
    mostrar_trace = st.toggle("Mostrar o caminho do agente", value=True)
    rec, aviso = recursos(usar_mcp)
    if rec:
        st.caption(f"Modelo: `{settings.rag_model}` · índice: {len(rec.index.chunks)} trechos "
                   f"({'BM25 + vetores' if rec.index.vectors is not None else 'só BM25'})")
    st.caption(f"Custo nesta sessão: US$ {st.session_state.get('gasto', 0.0):.4f}")

if aviso:
    st.warning(aviso)
if rec is None:
    st.error("Sem índice da documentação. No terminal: `python scripts/preparar_docs.py` e depois "
             "`python scripts/indexar_docs.py`.")
    st.stop()

thread = st.session_state.thread
if thread:
    for m in asyncio.run(historico(rec, thread)):
        mostrar(m, mostrar_trace)
else:
    st.markdown("### Pergunte qualquer coisa sobre o Blender\n"
                "Ex.: *Como deixo as bordas arredondadas?* · *Qual nó uso para textura de tijolo?* · "
                "*Me dá um script bpy que cria um cilindro com bevel*")

if texto := st.chat_input("Sua dúvida sobre o Blender…"):
    if not thread:
        thread = st.session_state.thread = uuid.uuid4().hex[:12]
        salvar_conversas([{"id": thread, "titulo": texto[:40] + ("…" if len(texto) > 40 else ""),
                           "criada": datetime.now().isoformat(timespec="seconds")}] + conversas())
    mostrar(HumanMessage(texto), mostrar_trace)
    with st.status("Pensando…", expanded=False) as status:
        try:
            msgs, usage = asyncio.run(perguntar(rec, thread, texto, status))
            st.session_state.gasto = st.session_state.get("gasto", 0.0) + custo(usage)
            status.update(label="Pronto", state="complete")
        except Exception as e:
            status.update(label="Erro", state="error")
            st.error(f"Falhou: {e}")
            st.stop()
    st.rerun()
