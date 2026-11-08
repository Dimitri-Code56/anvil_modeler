"""Skills em camadas, no mesmo formato do Claude (pasta/SKILL.md com name + description).

skills/
  base/<skill>/SKILL.md            sempre carregadas (padrão de qualidade)
  tecnicas/<skill>/SKILL.md        o planner escolhe pelo tipo de objeto (como modelar a forma)
  superficies/<skill>/SKILL.md     o planner escolhe pelo que o objeto é feito (tecido, pele, pelo, escama)
  materiais/<skill>/SKILL.md       sempre carregadas (biblioteca de materiais)
  estilos/<estilo>/SKILL.md        uma, escolhida pelo usuário
  projetos/<projeto>/<skill>/...   opcional; o planner escolhe dentro do projeto ativo

Divulgação progressiva, como o Claude faz: o planner vê só o catálogo
(nome + descrição) das camadas escolhíveis; só o conteúdo das skills
escolhidas entra no prompt do gerador de código.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

ALWAYS_LAYERS = ("base", "materiais")
CHOOSABLE_LAYERS = ("tecnicas", "superficies")
MAX_CHOSEN = 4   # skills escolhíveis por asset, na ordem do planner (mais que isso só pesa no contexto)


@dataclass
class Skill:
    name: str
    description: str
    layer: str               # base | tecnicas | superficies | materiais | estilos | projetos
    project: str | None      # nome do projeto (só na camada projetos)
    body: str


def _parse_frontmatter(fm: str) -> dict:
    try:
        data = yaml.safe_load(fm)
        if isinstance(data, dict):
            return data
    except yaml.YAMLError:
        pass
    # Tolerante como o Claude: "chave: valor" por linha, cortando no primeiro ":"
    data = {}
    for line in fm.splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def _split_frontmatter(text: str) -> tuple[dict, str]:
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        return _parse_frontmatter(fm), body.strip()
    return {}, text.strip()


def list_skills(skills_dir: Path) -> list[Skill]:
    out = []
    for path in sorted(skills_dir.rglob("SKILL.md")):
        rel = path.relative_to(skills_dir).parts
        if any(p.startswith("_") for p in rel):
            continue
        layer = rel[0]
        project = rel[1] if layer == "projetos" and len(rel) >= 4 else None
        meta, body = _split_frontmatter(path.read_text(encoding="utf-8"))
        out.append(Skill(meta.get("name", path.parent.name), meta.get("description", ""), layer, project, body))
    return out


def available_styles(skills_dir: Path) -> list[str]:
    return [s.name for s in list_skills(skills_dir) if s.layer == "estilos"]


def available_projects(skills_dir: Path) -> list[str]:
    return sorted({s.project for s in list_skills(skills_dir) if s.project})


def catalog_text(skills_dir: Path, project: str | None = None) -> str:
    """Catálogo das skills escolhíveis pelo planner: técnicas, superfícies (+ as do projeto ativo)."""
    lines = []
    for s in list_skills(skills_dir):
        if s.layer in CHOOSABLE_LAYERS or (project and s.project == project):
            tag = f"[projeto {s.project}] " if s.project else f"[{s.layer}] "
            lines.append(f"- {s.name}: {tag}{s.description}")
    return "\n".join(lines)


SCRIPT_MARKER = "## Modo script"


def body_for_mode(body: str, modo: str = "script") -> str:
    """Skills com duas versões: receitas de ferramentas (modo agente) e o guia de bpy (modo script).

    No modo script tiramos as seções "(modo agente)" — senão o modelo reimplementa as
    ferramentas como funções. No modo agente tiramos a seção de script.
    """
    pos = body.find(SCRIPT_MARKER)
    if modo == "agente":
        if pos >= 0:
            return body[:pos].rstrip().rstrip("-").rstrip()
        # skill sem receita de ferramentas (estilo, superfície, projeto): só título e avisos (> ...)
        return "\n".join(l for l in body.splitlines() if l.startswith(("# ", ">"))).strip()
    head, script = (body[:pos], body[pos:]) if pos >= 0 else (body, "")
    keep, skipping = [], False
    for line in head.splitlines():
        if line.startswith("## "):
            skipping = "modo agente" in line.lower()
        if not skipping:
            keep.append(line)
    head = "\n".join(keep).rstrip().rstrip("-").rstrip()
    if script:
        script = script.split("\n", 1)[1] if "\n" in script else ""
    return (head + "\n\n" + script.strip()).strip()


def compose_skills(skills_dir: Path, chosen: list[str], style: str, project: str | None = None,
                   modo: str = "script") -> str:
    """Monta o texto de skills do gerador: base → técnicas → superfícies → materiais → estilo → projeto."""
    skills = list_skills(skills_dir)
    import difflib
    names = [s.name for s in skills if s.layer in CHOOSABLE_LAYERS or s.layer == "projetos"]
    chosen_set = set()
    for c in chosen or []:
        n = str(c).strip().lower().replace("_", "-").replace(" ", "-")
        match = n if n in names else next(iter(difflib.get_close_matches(n, names, n=1, cutoff=0.6)), None)
        if match and len(chosen_set) < MAX_CHOSEN:
            chosen_set.add(match)
    order = {"base": 0, "tecnicas": 1, "superficies": 2, "materiais": 3, "estilos": 4, "projetos": 5}
    picked = [
        s for s in skills
        if s.layer in ALWAYS_LAYERS
        or (s.layer in CHOOSABLE_LAYERS and s.name in chosen_set)
        or (s.layer == "estilos" and s.name == style)
        or (s.layer == "projetos" and project and s.project == project and s.name in chosen_set)
    ]
    picked.sort(key=lambda s: order.get(s.layer, 9))
    blocks = []
    for s in picked:
        header = f"## Skill ({s.layer}): {s.name}"
        if s.layer == "projetos":
            header += f" — regras do projeto {s.project}, têm prioridade sobre as genéricas"
        blocks.append(f"{header}\n{body_for_mode(s.body, modo)}")
    return "\n\n".join(blocks)
