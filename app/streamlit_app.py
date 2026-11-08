"""Interface: streamlit run app/streamlit_app.py"""
from __future__ import annotations

import asyncio
from pathlib import Path

import streamlit as st

from anvil_modeler.config import MODES, settings
from anvil_modeler.runner import make_run_id, run_once
from anvil_modeler.skills import available_projects, available_styles

st.set_page_config(page_title="Anvil Modeler", page_icon="🔨", layout="wide")
st.title("🔨 Anvil Modeler")
st.caption("Descrição + concept art → modelo no Blender, com loop de verificação visual.")

with st.sidebar:
    mode = st.selectbox("Modo do harness", list(MODES), index=list(MODES).index("full"))
    max_iters = st.slider("Máx. iterações (loop)", 1, 6, settings.max_iters)
    styles = available_styles(settings.skills_dir)
    style = st.selectbox("Estilo", styles, index=styles.index(settings.default_style) if settings.default_style in styles else 0)
    project = st.selectbox("Projeto (regras específicas)", ["(nenhum)"] + available_projects(settings.skills_dir))
    project = None if project == "(nenhum)" else project
    st.json(MODES[mode])
    settings.judge_enabled = st.toggle("Juiz visual", value=settings.judge_enabled)

asset_name = st.text_input("Nome do asset", "carro_sedan")
description = st.text_area(
    "Descrição",
    "Sedan compacto vermelho de quatro portas, faróis afilados, rodas de liga leve de cinco raios "
    "e vidros escurecidos.",
    height=120,
)
upload = st.file_uploader("Concept art (opcional — se vazio, gera localmente)", type=["png", "jpg", "jpeg"])

if st.button("Modelar", type="primary", disabled=not (asset_name and description)):
    run_id = make_run_id(asset_name, mode)
    concept_path = None
    if upload:
        d = settings.runs_dir / run_id
        d.mkdir(parents=True, exist_ok=True)
        concept_path = str(d / f"concept{Path(upload.name).suffix}")
        Path(concept_path).write_bytes(upload.getvalue())

    status = st.status("Rodando o grafo...", expanded=True)
    gallery = st.container()

    def on_update(node: str, update: dict) -> None:
        status.write(f"✔ `{node}`")
        if update.get("concept_path"):
            gallery.image(update["concept_path"], caption="Concept", width=320)
        if update.get("spec"):
            with gallery.expander("Especificação (planner)"):
                st.json(update["spec"])
        for att in update.get("attempts", []):
            c1, c2 = gallery.columns([1, 1])
            if att.get("render_path"):
                c1.image(att["render_path"], caption=f"Tentativa {att['iteration']}")
            nota = "sem juiz" if att.get("score") is None else f"{att['score']:.1f} / 5"
            c2.metric(f"Nota (tentativa {att['iteration']})", nota)
            c2.write(att.get("guard_error") or att.get("exec_error") or att.get("feedback"))
            with c2.expander("Código"):
                st.code(att["code"], language="python")

    result = asyncio.run(run_once(
        description, asset_name, mode, concept_path=concept_path, style=style, project=project,
        max_iters=max_iters, run_id=run_id, on_update=on_update,
    ))
    status.update(label="Concluído", state="complete")
    st.subheader("Métricas de geometria")
    st.json(result["metrics"])
