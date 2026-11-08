"""Nós do grafo. Cada nó recebe o estado e devolve só o que mudou."""
from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from . import prompts
from .blender import ADOPT, BlenderClient, collection_name
from .config import Settings
from .agent import make_agent_node
from .guardrails import check_code, repair_code
from .llm import get_llm, image_block, structured, text_of
from .blender_lib import PRESET_NAMES, prelude
from .skills import catalog_text, compose_skills
from .state import AnvilState


# --- saídas estruturadas -----------------------------------------------------
class Part(BaseModel):
    name: str
    shape: str = Field(description="forma/silhueta da peça")
    approx_size_m: str = Field(description="tamanho aproximado em metros, ex. '0.4 x 0.2 x 0.1'")
    technique: str = Field(description="técnica bpy/bmesh sugerida")
    material: str = Field(description="preset da biblioteca de materiais")
    detail_level: Literal["primaria", "secundaria", "terciaria"]


class ApiItem(BaseModel):
    kind: Literal["modifier", "shader_node", "operator", "bmesh_op", "enum", "property"]
    name: str = Field(description="identificador exato que o código vai usar")


class Spec(BaseModel):
    name: str
    category: Literal["hard_surface", "organic", "character", "architecture", "vehicle", "prop", "environment"]
    summary: str
    overall_dimensions_m: str = Field(description="dimensões totais em metros, ex. '0.45 x 0.50 x 0.90' (largura x profundidade x altura)")
    identifying_features: list[str] = Field(description="traços que fazem o objeto ser reconhecido de imediato")
    parts: list[Part]
    style_notes: list[str]
    api_plan: list[ApiItem] = Field(description="tudo da API do Blender que o código vai usar, para verificar antes")
    api_queries: list[str] = Field(description="2 a 4 consultas curtas à documentação bpy/bmesh")
    skills: list[str] = Field(description="nomes das skills do catálogo que se aplicam a este asset")


class Evaluation(BaseModel):
    score: float = Field(ge=1, le=5)
    approved: bool
    issues: list[str]
    feedback: str


def _reference_blocks(state: AnvilState) -> list:
    text = f"Descrição do asset: {state['description']}\nEstilo pedido: {state.get('style', 'realista')}"
    if state.get("project"):
        text += f"\nProjeto: {state['project']}"
    blocks: list = [{"type": "text", "text": text}]
    if state.get("concept_path"):
        blocks += [{"type": "text", "text": "Concept art de referência:"}, image_block(state["concept_path"])]
    return blocks


def _extract_code(text: str) -> str:
    m = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.S)
    return (m.group(1) if m else text).strip()


async def judge_render(settings: Settings, state: AnvilState, render_path: str) -> Evaluation:
    """Avaliação visual do render contra a referência (usada no loop e no benchmark)."""
    judge = structured(get_llm(settings.judge_model, 2000, settings.judge_provider), Evaluation, settings.judge_provider)
    content = _reference_blocks(state) + [
        {"type": "text", "text": "Render do modelo gerado:"}, image_block(render_path),
    ]
    ev: Evaluation = await judge.ainvoke([SystemMessage(prompts.JUDGE_SYSTEM), HumanMessage(content=content)])
    ev.approved = ev.score >= settings.approve_score
    return ev


def make_nodes(blender: BlenderClient, settings: Settings):
    llm = get_llm()

    def run_dir(state: AnvilState) -> Path:
        d = settings.runs_dir / state["run_id"]
        d.mkdir(parents=True, exist_ok=True)
        return d

    async def concept(state: AnvilState) -> dict:
        if state.get("concept_path") or settings.image_backend == "none":
            return {}
        from .image_gen import generate_concept

        msg = await get_llm(settings.fast_model, 300, settings.fast_provider).ainvoke(
            prompts.CONCEPT_PROMPT.format(description=state["description"], style=state.get("style", "realista"))
        )
        prompt = prompts.CONCEPT_PREFIX + text_of(msg).strip()
        out = run_dir(state) / "concept.png"
        path = await asyncio.to_thread(generate_concept, prompt, out)
        return {"concept_path": path}

    async def plan(state: AnvilState) -> dict:
        planner = structured(llm, Spec)
        spec: Spec = await planner.ainvoke(
            [SystemMessage(prompts.PLANNER_SYSTEM.format(
                catalog=catalog_text(settings.skills_dir, state.get("project")),
                presets=", ".join(PRESET_NAMES),
            ) + prompts.PLANNER_NUMBERS + (prompts.PLANNER_AGENT_HINT if state.get("use_agent") and settings.model_profile() == "fraco" else "")),
             HumanMessage(content=_reference_blocks(state))]
        )
        return {"spec": spec.model_dump()}

    async def verify_api(state: AnvilState) -> dict:
        """Confere ao vivo, no Blender aberto, os nomes que o código vai usar (evita erro de versão)."""
        items = (state.get("spec") or {}).get("api_plan", [])
        if not items:
            return {"api_sheet": "", "api_missing": []}
        try:
            data = await blender.introspect(items)
        except Exception as e:
            return {"api_sheet": f"(verificação de API indisponível: {e})", "api_missing": []}
        lines = [f"Blender {data.get('blender', '?')}: nomes conferidos ao vivo nesta instalação."]
        missing = []
        for r in data.get("items", []):
            head = f"{r['kind']} {r['name']}"
            if r.get("ok"):
                parts = []
                for key, label in (("inputs", "entradas"), ("outputs", "saídas"), ("params", "parâmetros"),
                                   ("props", "propriedades"), ("values", "valores"), ("type", "tipo")):
                    if r.get(key):
                        val = r[key] if isinstance(r[key], str) else ", ".join(r[key])
                        parts.append(f"{label}: {val}")
                if r.get("doc"):
                    parts.append("assinatura: " + r["doc"].strip().splitlines()[0][:160])
                if r.get("note"):
                    parts.append("obs: " + r["note"])
                lines.append(f"OK  {head} | " + " | ".join(parts))
            else:
                missing.append(r["name"])
                sug = ", ".join(r.get("suggest") or []) or "nenhum parecido"
                lines.append(f"NÃO EXISTE  {head} | parecidos: {sug}" + (f" | erro: {r['error']}" if r.get("error") else ""))
        return {"api_sheet": "\n".join(lines), "api_missing": missing}

    async def retrieve(state: AnvilState) -> dict:
        # documentação focada: as consultas do planner + o que a verificação ao vivo não encontrou
        queries = (state.get("spec") or {}).get("api_queries", [])[:4] + list(state.get("api_missing") or [])[:3]
        chunks = []
        for q in queries:
            try:
                hits = await blender.search_docs(q, max_results=2)
                chunks.append(f"### {q}\n{hits[:1500]}")
            except Exception as e:  # docs são opcionais, não derrubam a execução
                chunks.append(f"### {q}\n(falha na busca: {e})")
        return {"docs_context": "\n\n".join(chunks)}

    def is_pure(state: AnvilState) -> bool:
        return not any(state.get(k) for k in ("use_skills", "use_rag", "use_loop", "use_agent"))

    async def code(state: AnvilState) -> dict:
        if is_pure(state):
            content: list = [{"type": "text", "text": prompts.BASELINE_USER.format(description=state["description"])}]
            if state.get("concept_path"):
                content += [{"type": "text", "text": "Referência:"}, image_block(state["concept_path"])]
            msg = await llm.ainvoke([HumanMessage(content=content)])
            return {
                "code": _extract_code(text_of(msg)), "iteration": state.get("iteration", 0) + 1,
                "guard_error": None, "exec_error": None, "render_path": None, "evaluation": None,
            }
        spec = state.get("spec")
        skills = ""
        if state.get("use_skills"):
            from .geometria import budget_line
            skills = "\n\n# " + budget_line(settings.alvo, (spec or {}).get("category")) + \
                "\n\n# Regras de modelagem e estilo (skills)\n" + compose_skills(
                settings.skills_dir, (spec or {}).get("skills", []),
                state.get("style", "realista"), state.get("project"),
            )
        previous = ""
        if state.get("iteration", 0) > 0:
            problem = (
                state.get("guard_error") or state.get("exec_error")
                or (state.get("evaluation") or {}).get("feedback", "")
            )
            previous = prompts.PREVIOUS_ATTEMPT.format(
                iteration=state["iteration"], code=state.get("code", ""), problem=problem
            )
        user_text = prompts.CODER_USER.format(
            asset_name=state["asset_name"],
            description=state["description"],
            style=state.get("style", "realista"),
            project=f"\nProjeto: {state['project']}" if state.get("project") else "",
            spec=f"\nEspecificação:\n```json\n{json.dumps(spec, ensure_ascii=False, indent=2)}\n```" if spec else "",
            api=f"\n\nFicha de API verificada:\n{state['api_sheet']}" if state.get("api_sheet") else "",
            docs=f"\n\nTrechos da documentação do Blender:\n{state['docs_context']}" if state.get("docs_context") else "",
            previous=previous,
        )
        content: list = [{"type": "text", "text": user_text}]
        if state.get("concept_path"):
            content += [{"type": "text", "text": "Concept art:"}, image_block(state["concept_path"])]
        it = state.get("iteration", 0)
        coder = get_llm(None, 16000, None, min(0.9, 0.2 + 0.3 * it)) if it > 0 else llm
        messages = [SystemMessage(prompts.CODER_SYSTEM.format(skills=skills)), HumanMessage(content=content)]
        msg = await coder.ainvoke(messages)
        new_code = _extract_code(text_of(msg))
        if it > 0 and new_code.strip() == (state.get("code") or "").strip():
            # o modelo repetiu o código que falhou: pede de novo, com mais variação
            msg = await get_llm(None, 16000, None, 0.9).ainvoke(messages + [msg, HumanMessage(
                content="Você repetiu exatamente o código que falhou. Mude a parte que causa o problema e reescreva o script.")])
            new_code = _extract_code(text_of(msg))
        return {
            "code": new_code,
            "iteration": state.get("iteration", 0) + 1,
            "guard_error": None, "exec_error": None, "render_path": None, "evaluation": None,
        }

    async def guard(state: AnvilState) -> dict:
        if is_pure(state):
            # sem harness: só a segurança (não apagar/salvar/importar fora da lista), sem consertos nem armadilhas
            return {"guard_error": check_code(state["code"], armadilhas=False)}
        code, fixes = repair_code(state["code"])
        for f in fixes:
            print(f"[guard] reparo: {f}")
        return {"code": code, "guard_error": check_code(code)}

    async def execute(state: AnvilState) -> dict:
        # a biblioteca de materiais vai colada antes do script; corrigimos os números
        # de linha do traceback para baterem com o código que o modelo escreveu
        lib = prelude(state.get("style", "realista")) + "\n__anvil_before = set(bpy.data.objects.keys())\n"
        offset = lib.count("\n")
        try:
            await blender.prepare_scene(state.get("scene_key") or state["asset_name"])
            key = state.get("scene_key") or state["asset_name"]
            await blender.execute(lib + state["code"] + ADOPT.format(coll=collection_name(key)))
            return {"exec_error": None}
        except Exception as e:
            msg = re.sub(
                r"line (\d+)",
                lambda m: f"line {int(m.group(1)) - offset}" if int(m.group(1)) > offset else m.group(0),
                str(e),
            )
            return {"exec_error": f"Erro ao executar no Blender:\n{msg[-2500:]}"}

    async def render(state: AnvilState) -> dict:
        out = run_dir(state) / f"iter_{state['iteration']:02d}.png"
        try:
            path = await blender.render(state.get("scene_key") or state["asset_name"], str(out), settings.render_res)
            return {"render_path": path}
        except Exception as e:
            return {"exec_error": f"Erro ao renderizar:\n{str(e)[-1500:]}"}

    async def evaluate(state: AnvilState) -> dict:
        error = state.get("guard_error") or state.get("exec_error")
        if error or not state.get("render_path"):
            ev = {"score": 1, "approved": False, "issues": ["falha técnica"], "feedback": error or "Sem render."}
        elif not settings.judge_enabled:
            # sem juiz: render saiu sem erro → aceita; a avaliação visual fica com você
            ev = {"score": None, "approved": True, "issues": [], "feedback": "Juiz desligado: render gerado sem erros."}
        else:
            ev = (await judge_render(settings, state, state["render_path"])).model_dump()
        attempt = {
            "iteration": state["iteration"], "code": state["code"],
            "guard_error": state.get("guard_error"), "exec_error": state.get("exec_error"),
            "render_path": state.get("render_path"),
            "score": ev["score"], "approved": ev["approved"], "feedback": ev["feedback"],
        }
        return {"evaluation": ev, "attempts": [attempt]}

    return {
        "concept": concept, "plan": plan, "verify_api": verify_api, "retrieve": retrieve, "code": code,
        "guard": guard, "execute": execute, "render": render, "evaluate": evaluate,
        "agente": make_agent_node(settings),
    }
