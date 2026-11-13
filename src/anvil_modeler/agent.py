"""Modo agente: o modelo monta o asset chamando as ferramentas do anvil-tools (MCP).

Dois perfis (ANVIL_PERFIL / --perfil):
- fraco (padrão no Ollama): ferramentas de alto nível (caixa, revolucao...) + conferência de geometria,
  consertos automáticos e cobranças do harness. Compensa um modelo que erra conta e API.
- forte (padrão na API): o modelo escreve o próprio bpy com executar_python e confere quando quiser;
  o harness só mantém o guardrail de segurança. Não trata um modelo bom como fraco.

Em vez de escrever um script bpy inteiro, o modelo escolhe uma ferramenta, preenche os parâmetros,
lê o resultado (ok ou ERRO) e decide a próxima chamada. O código bpy fica dentro das ferramentas,
já testado. Para caber no contexto de modelos locais, o histórico enviado a cada rodada é só:
sistema + pedido + resumo do progresso + as últimas rodadas de chamada.
"""
from __future__ import annotations

import json
import os
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

from . import prompts
from .blender import _to_text, extract_json
from .geometria import check as check_geometry, plan_dims
from .blender_lib import PRESET_NAMES
from .llm import get_llm, image_block, text_of
from .skills import compose_skills

# o harness cuida destas: iniciar a coleção, renderizar; e o modelo não roda Python solto
HIDDEN = {"iniciar_asset", "executar_python", "renderizar", "verificar_api", "conferir"}
# depois destas, o harness confere a geometria sozinho e põe os problemas no progresso
CHANGES = {"caixa", "cilindro", "perfil_extrudado", "revolucao", "massa_organica", "tubo_por_curva",
           "espelhar", "repetir", "remover", "mover", "cortar", "suavizar"}
MAX_FIX_REMINDERS = 5
MAX_REBUILDS = 3       # a mesma peça criada mais vezes que isso: o harness manda seguir em frente
# perfil forte: escreve o próprio bpy; só as ferramentas de execução e conferência
STRONG_TOOLS = {"executar_python", "listar_objetos", "conferir", "metricas", "verificar_api", "renderizar"}


def _strip_images(tms: list) -> list:
    """Renders antigos saem do histórico (só o último fica como imagem): imagem custa tokens a cada rodada."""
    out = []
    for m in tms:
        if isinstance(m.content, list):
            out.append(ToolMessage(content="(render anterior: veja o mais recente)", tool_call_id=m.tool_call_id, name=m.name))
        else:
            out.append(m)
    return out
CREATE = {"caixa", "cilindro", "perfil_extrudado", "revolucao", "massa_organica", "tubo_por_curva"}
KEEP_TURNS = 6          # rodadas recentes mantidas no histórico
MAX_CALLS_PER_TURN = 6
MAX_ERRORS_IN_ROW = 6

# modelos pequenos soltam um "quase-JSON": chaves e valores sem aspas
# (ex.: {"name": buscar_documentacao, "arguments": {"consulta": Bevel modifier segments}})
_CHAVE_NUA = re.compile(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_\-]*)(\s*:)")
# valor nu simples depois de qualquer dois-pontos (não-string, não-número, não-objeto, não-negativo)
_VALOR_NU = re.compile(r'(:\s*)([^"\{\[\d\s,:\}\]\-][^,:\}\]]*)(\s*[,}\]])')


def _conserta_json(t: str) -> str:
    """Tenta transformar o quase-JSON de um modelo pequeno em JSON válido (aspas faltando).
    Só roda quando o parse estrito falhou; se o resultado ainda não parsear, nada muda."""
    t = _VALOR_NU.sub(lambda m: m.group(1) + '"' + m.group(2).strip().strip('`\'"') + '"' + m.group(3), t)
    t = _CHAVE_NUA.sub(lambda m: m.group(1) + '"' + m.group(2) + '"' + m.group(3), t)
    return t


def _bloco_json(t: str, i: int) -> str:
    """O trecho de t a partir de i até o } que fecha o { de i (contagem simples de chaves)."""
    prof = 0
    for j in range(i, len(t)):
        if t[j] == "{":
            prof += 1
        elif t[j] == "}":
            prof -= 1
            if prof == 0:
                return t[i:j + 1]
    return t[i:]


def parse_text_calls(text: str, names: set[str]) -> list[dict]:
    """Modelos locais às vezes escrevem a chamada como JSON no texto em vez de usar tool_calls.

    Aceita também o formato "quase JSON" em que o nome vem SEM aspas (comum no qwen2.5):
    {"name": buscar_documentacao, "arguments": {"consulta": "..."}}
    Nesse caso o objeto inteiro não é JSON válido: o nome sai por regex e os argumentos
    (que são um objeto JSON válido) são lidos a partir da chave certa.
    """
    import re
    calls, dec, i = [], json.JSONDecoder(), 0
    while True:
        i = text.find("{", i)
        if i < 0:
            break
        try:
            obj, end = dec.raw_decode(text, i)
        except ValueError:
            i += 1
            continue
        if isinstance(obj, dict):
            c = _texto_para_chamada(obj, names)
            if c:
                calls.append(c)
        i = end
    if calls:
        return calls
    m = re.search(r'"(?:name|tool|function)"\s*:\s*([A-Za-z_][\w.]*)\s*,\s*"'
                  r'(?:arguments|args|parameters)"\s*:\s*', text)
    if not m:
        return []
    abre = text.find("{", m.end() - 1)
    if m.group(1) not in names or abre < 0:
        return []
    try:
        args, _fim = dec.raw_decode(text, abre)
    except ValueError:
        return []
    return [{"name": m.group(1), "args": args}] if isinstance(args, dict) else []


def _texto_para_chamada(obj: dict, names: set[str]) -> dict | None:
    name = obj.get("name") or obj.get("tool") or obj.get("function")
    args = obj.get("arguments", obj.get("args", obj.get("parameters")))
    if isinstance(args, str):
        try:
            args = json.loads(args)
        except ValueError:
            args = None
    if name in names and isinstance(args, dict):
        return {"name": name, "args": args}
    return None


def _short(value, n: int = 500) -> str:
    s = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    return s if len(s) <= n else s[:n] + "…"


def _norm(s: str) -> str:
    import unicodedata
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in s if ch.isalnum())


def pending_parts(spec: dict | None, pieces: dict[str, str]) -> list[str]:
    """Peças do plano sem nenhuma peça criada com nome parecido (perna_fd conta para 'Pernas')."""
    stop = {"de", "do", "da", "dos", "das", "e", "com", "para", "the", "of"}
    made_words = {_norm(w) for n in pieces for w in str(n).replace("-", "_").split("_") if len(_norm(w)) >= 2}
    out = []
    for p in (spec or {}).get("parts") or []:
        words = [_norm(w) for w in str(p.get("name", "")).split() if _norm(w) and _norm(w) not in stop]
        if words and not any(pw.startswith(m) or m.startswith(pw[:4]) for pw in words for m in made_words):
            out.append(str(p.get("name")))
    return out


def plan_text(spec: dict | None) -> str:
    if not spec:
        return "(sem plano: decomponha você mesmo em peças com medidas reais)"
    lines = [f"Dimensões totais (m): {spec.get('overall_dimensions_m')}"]
    if spec.get("identifying_features"):
        lines.append("Traços identificadores: " + "; ".join(spec["identifying_features"]))
    for p in spec.get("parts") or []:
        lines.append(f"- {p.get('name')}: {p.get('shape')}, ~{p.get('approx_size_m')} m, "
                     f"ferramenta {p.get('technique')}, material {p.get('material')}")
    return "\n".join(lines)


def make_agent_node(settings):
    async def agente(state) -> dict:
        servers = settings.mcp_servers()
        if "anvil" not in servers:
            return {"iteration": 1, "code": "", "guard_error": None,
                    "exec_error": "config/mcp_servers.json não tem o servidor 'anvil' (anvil-tools)."}
        key = state.get("scene_key") or state["asset_name"]
        style = state.get("style", "realista")
        spec = state.get("spec") or {}
        weak = settings.model_profile() == "fraco"
        print(f"[agente] perfil {'fraco (ferramentas prontas + conferências)' if weak else 'forte (escreve bpy)'}")
        skills = compose_skills(settings.skills_dir, spec.get("skills", []), style, state.get("project"),
                                modo="agente" if weak else "script")
        from .geometria import budget_line
        system = (prompts.AGENT_SYSTEM if weak else prompts.AGENT_SYSTEM_FORTE).format(
            presets=", ".join(PRESET_NAMES),
            skills="\n\n# " + budget_line(settings.alvo, spec.get("category"))
                   + (("\n\n# Receitas (skills)\n" + skills) if skills else ""),
        )
        task = prompts.AGENT_USER.format(asset_name=state["asset_name"], description=state["description"],
                                         style=style, plan=plan_text(spec))
        log: list[str] = []
        pieces: dict[str, str] = {}       # nome → ferramenta
        posicoes: dict[str, list] = {}    # nome → última posicao pedida (para sugerir a correção)
        problems: list[str] = []
        dims = plan_dims(spec.get("overall_dimensions_m"))
        n_calls = n_errors = errors_in_row = reminders = 0
        seen_calls: set[str] = set()      # criações idênticas não se repetem (evita loop criar/remover)
        rebuilds: dict[str, int] = {}
        auto_notes: list[str] = []
        created_ok = False                # perfil forte: algum executar_python deu certo
        cut_count = 0                     # respostas cortadas pelo limite de saída
        from .config import price_for
        price = price_for(settings.model, settings.provider)
        spent = 0.0                       # custo estimado do agente neste run (US$)
        nudge = ""

        client = MultiServerMCPClient({"anvil": servers["anvil"]})
        async with client.session("anvil") as session:
            tools = await load_mcp_tools(session)
            by_name = {t.name: t for t in tools}
            if "iniciar_asset" not in by_name:
                return {"iteration": 1, "code": "", "guard_error": None,
                        "exec_error": f"anvil-tools sem iniciar_asset. Ferramentas: {sorted(by_name)}"}
            await by_name["iniciar_asset"].ainvoke({"nome": key, "estilo": style})
            exposed = [t for t in tools if (t.name not in HIDDEN if weak else t.name in STRONG_TOOLS)]
            exposed_names = {t.name for t in exposed}
            model = get_llm().bind_tools(exposed)
            turns: list[tuple[AIMessage, list[ToolMessage]]] = []

            async def conferir() -> list[str]:
                try:
                    data = extract_json(_to_text(await by_name["conferir"].ainvoke({}))) or {}
                    objs = data.get("objetos", [])
                    # conserto automático: peça abaixo do chão sobe até apoiar (sempre certo, sem gastar o modelo)
                    for o in objs:
                        nm, dz, p = o["objeto"], -o["min"][2], posicoes.get(o["objeto"])
                        if dz > 0.01 and p and len(p) == 3 and "mover" in by_name:
                            newp = [p[0], p[1], round(p[2] + dz, 4)]
                            await by_name["mover"].ainvoke({"nome": nm, "posicao": newp})
                            posicoes[nm] = newp
                            o["min"][2] += dz
                            o["max"][2] += dz
                            note = f"o harness subiu {nm} {dz:.2f} m para apoiar no chão (posicao z = {newp[2]:.3f})"
                            auto_notes.append(note)
                            log.append("# " + note)
                            print(f"[agente] auto: {note}")
                    return check_geometry(objs, dims, posicoes)
                except Exception as e:
                    return [f"(conferência indisponível: {str(e)[:120]})"]

            for step in range(settings.agent_max_steps):
                progress = (f"\n\n## Progresso\nChamadas feitas: {n_calls}. Erros: {n_errors}." + nudge) if not weak else (
                            "\n\n## Progresso\nPeças criadas: "
                            + (", ".join(f"{k} ({v})" for k, v in pieces.items()) or "nenhuma")
                            + f"\nChamadas feitas: {n_calls}. Erros: {n_errors}."
                            + (("\nAjustes automáticos (já feitos, não refaça): " + "; ".join(auto_notes[-3:]))
                               if auto_notes else "")
                            + (("\nPeças do plano que ainda FALTAM: " + ", ".join(pending_parts(spec, pieces)))
                               if pieces and pending_parts(spec, pieces) else "")
                            + (("\nProblemas detectados pelo harness (corrija com mover/remover antes de terminar):\n"
                                + "\n".join(f"- {p}" for p in problems)) if problems and pieces else "")
                            + nudge)
                sys_msg = (SystemMessage(content=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}])
                           if settings.provider == "anthropic" else SystemMessage(system))
                if not weak and state.get("concept_path"):
                    # perfil forte enxerga: a referência vai junto, num bloco fixo (fica no cache);
                    # o progresso, que muda a cada rodada, vem depois
                    ref = [{"type": "text", "text": "Imagem de referência: modele seguindo ela (forma, proporções, "
                                                    "partes, materiais)."},
                           image_block(state["concept_path"]),
                           {"type": "text", "text": task, **({"cache_control": {"type": "ephemeral"}}
                                                             if settings.provider == "anthropic" else {})}]
                    msgs = [sys_msg, HumanMessage(content=ref), HumanMessage(progress.strip() or "Comece.")]
                else:
                    msgs = [sys_msg, HumanMessage(task + progress)]
                recent = turns[-KEEP_TURNS:]
                last_img = max((k for k, (_, tms) in enumerate(recent) if any(isinstance(m.content, list) for m in tms)),
                               default=-1)
                for k, (ai_k, tms) in enumerate(recent):
                    msgs += [ai_k, *(tms if k == last_img else _strip_images(tms))]
                ai = await model.ainvoke(msgs)
                um = getattr(ai, "usage_metadata", None) or {}
                if price and um:
                    cr = (um.get("input_token_details") or {}).get("cache_read", 0) or 0
                    spent += ((um.get("input_tokens", 0) - cr) * price[0] + cr * price[3]
                              + um.get("output_tokens", 0) * price[1]) / 1e6
                if settings.max_usd and spent > settings.max_usd:
                    print(f"[agente] teto de custo atingido: US$ {spent:.3f} > US$ {settings.max_usd:.2f}; parando")
                    log.append(f"# parado: teto de custo (US$ {spent:.3f})")
                    break
                calls = list(getattr(ai, "tool_calls", None) or [])
                if not calls:
                    parsed = parse_text_calls(text_of(ai), exposed_names)
                    calls = [{"name": c["name"], "args": c["args"], "id": f"call_{step}_{k}"} for k, c in enumerate(parsed)]
                if not calls and not weak:
                    # modelo escreveu o código como texto (```python) em vez de chamar a ferramenta
                    import re as _re
                    m = _re.search(r"```(?:python)?\s*\n(.*?)```", text_of(ai), _re.S)
                    if m and "bpy" in m.group(1):
                        calls = [{"name": "executar_python", "args": {"codigo": m.group(1)}, "id": f"call_{step}_txt"}]
                cut = (getattr(ai, "response_metadata", {}) or {}).get("stop_reason") in ("max_tokens", "length")
                calls = [dict(c, id=c.get("id") or f"call_{step}_{k}") for k, c in enumerate(calls[:MAX_CALLS_PER_TURN])]
                if cut:
                    print("[agente] resposta cortada por tamanho: pedindo o código em partes menores")
                    log.append("# resposta cortada por tamanho (limite de saída)")
                    if not calls or any(c["name"] == "executar_python" and not str((c.get("args") or {}).get("codigo", "")).strip()
                                        for c in calls):
                        cut_count += 1
                        if cut_count > 2:
                            log.append("# parado: respostas cortadas em sequência")
                            break
                        nudge = ("\nSua última resposta foi CORTADA por ser longa demais e nada foi executado. "
                                 "Chame executar_python com só UMA parte do asset agora (no máximo ~150 linhas); "
                                 "o resto vem nas próximas chamadas.")
                        continue
                if not calls:
                    if not weak:
                        if not created_ok and not nudge:
                            nudge = "\nVocê ainda não criou nada. Chame executar_python com o código do asset."
                            continue
                        log.append(f"# fim: {text_of(ai).strip()[:80]}")
                        break
                    if not pieces and not nudge:
                        nudge = ("\nVocê ainda não criou nenhuma peça. Chame as ferramentas agora, começando pela "
                                 "primeira peça do plano; não escreva código nem explicação.")
                        continue
                    faltam = pending_parts(spec, pieces)
                    if (faltam or problems) and pieces and reminders < MAX_FIX_REMINDERS:
                        reminders += 1
                        nudge = ("\nAinda NÃO terminou: " + ("faltam as peças " + ", ".join(faltam) + ". Crie a próxima agora. "
                                 if faltam else "") + ("Corrija os problemas da lista (mover/remover)." if problems else ""))
                        continue
                    log.append(f"# fim: {text_of(ai).strip()[:80]}")
                    break
                nudge = ""
                ai = AIMessage(content="", tool_calls=calls)
                tms = []
                for c in calls:
                    n_calls += 1
                    tool = by_name.get(c["name"])
                    args = c.get("args") or {}
                    sig = c["name"] + json.dumps(args, sort_keys=True, ensure_ascii=False)
                    nome_c = str(args.get("nome", ""))
                    try:
                        if tool is None or c["name"] not in exposed_names:
                            raise ValueError(f"ferramenta '{c['name']}' não existe aqui. Use: {sorted(exposed_names)}")
                        if weak and c["name"] in CREATE:
                            faltam_txt = ", ".join(pending_parts(spec, pieces)) or "nenhuma (confira e responda FIM)"
                            if sig in seen_calls:
                                raise ValueError("chamada IDÊNTICA a uma que você já fez: recriar igual dá o mesmo resultado. "
                                                 "Mude os parâmetros (use a correção sugerida com mover) ou passe para a "
                                                 f"próxima peça. Faltam: {faltam_txt}")
                            if rebuilds.get(nome_c, 0) >= MAX_REBUILDS:
                                raise ValueError(f"{nome_c} já foi criada {rebuilds[nome_c]} vezes. Deixe como está e siga "
                                                 f"para a próxima peça. Faltam: {faltam_txt}")
                        raw = _to_text(await tool.ainvoke(args))
                        out = _short(raw)
                        ok = True
                        if c["name"] in CREATE:
                            seen_calls.add(sig)
                            rebuilds[nome_c] = rebuilds.get(nome_c, 0) + 1
                    except Exception as e:  # o erro volta para o modelo corrigir
                        out = "ERRO: " + _short(str(e), 600)
                        ok = False
                    if ok:
                        errors_in_row = 0
                        created_ok = created_ok or c["name"] == "executar_python"
                        nome = str(args.get("nome", ""))
                        if isinstance(args.get("posicao"), list) and nome:
                            posicoes[nome] = args["posicao"]
                        elif c["name"] in ("perfil_extrudado", "revolucao") and nome:
                            posicoes[nome] = [0, 0, 0]   # padrão da ferramenta
                        if c["name"] in CREATE and nome:
                            pieces[nome] = c["name"]
                        elif c["name"] == "espelhar" and nome:
                            pieces[str(args.get("novo_nome") or nome + " espelhado")] = "espelhar"
                        elif c["name"] == "repetir" and nome:
                            pieces[f"{nome} x{args.get('quantidade')}"] = "repetir"
                        elif c["name"] == "remover":
                            pieces.pop(nome, None)
                            posicoes.pop(nome, None)
                    else:
                        n_errors += 1
                        errors_in_row += 1
                    print(f"[agente] {c['name']}({_short(args, 120)}) -> {'ok' if ok else out[:160]}")
                    log.append(f"{c['name']}({json.dumps(args, ensure_ascii=False)})  # {'ok' if ok else out[:300]}")
                    content = out
                    if ok and c["name"] == "renderizar" and settings.provider == "anthropic":
                        # o modelo VÊ o próprio render (o Haiku enxerga imagens): fecha o ciclo modelar → olhar → corrigir
                        img = (extract_json(raw) or {}).get("imagem")
                        if img and os.path.exists(img):
                            ref = " e com a imagem de referência" if state.get("concept_path") else ""
                            content = [{"type": "text", "text": "Render atual do asset. Compare com o pedido" + ref +
                                        ": silhueta, proporções, peças soltas ou mal encaixadas, o que falta."},
                                       image_block(img)]
                            log.append(f"# render visto pelo modelo: {img}")
                    tms.append(ToolMessage(content=content, tool_call_id=c["id"], name=c["name"]))
                turns.append((ai, tms))
                if weak and "conferir" in by_name and any(c["name"] in CHANGES for c in calls):
                    problems = await conferir()
                if errors_in_row >= MAX_ERRORS_IN_ROW:
                    log.append(f"# parado: {errors_in_row} erros seguidos")
                    break
            else:
                log.append(f"# parado: limite de {settings.agent_max_steps} rodadas")

        header = (f"# modo agente (perfil {'fraco' if weak else 'forte'}): {n_calls} chamadas, {n_errors} erros"
                  + (f", {len(pieces)} peças" if weak else "") + "\n")
        faltam = pending_parts(spec, pieces) if weak else []
        if faltam:
            header += "# peças do plano que não foram feitas: " + ", ".join(faltam) + "\n"
            print(f"[agente] peças que faltaram: {', '.join(faltam)}")
        if problems:
            header += "# problemas que sobraram:\n" + "".join(f"#   - {p}\n" for p in problems)
            for p in problems:
                print(f"[agente] problema restante: {p}")
        return {
            "iteration": 1, "code": header + "\n".join(log), "guard_error": None,
            "exec_error": None if (pieces if weak else created_ok) else "O agente não criou nenhuma peça.",
        }

    return agente
