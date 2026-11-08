"""Corta os documentos em pedaços por seção, guardando de onde cada pedaço veio.

Cada página em data/docs tem um cabeçalho (titulo, fonte, versao_blender, url) e corpo em Markdown.
O corte segue os títulos (#, ##, ###): um pedaço é uma seção, com o caminho de títulos junto
("Bevel Modifier > Options > Limit Method"), para a busca e para a citação. Seção longa é dividida
por parágrafos; bloco de código nunca é partido no meio.
"""
from __future__ import annotations

import re
from pathlib import Path

FRONT = re.compile(r"^---\n(.*?)\n---\n", re.S)
HEADING = re.compile(r"^(#{1,4})\s+(.*\S)\s*$")


def parse_doc(text: str) -> tuple[dict, str]:
    m = FRONT.match(text)
    if not m:
        return {}, text
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, _, v = line.partition(":")
            meta[k.strip()] = v.strip()
    return meta, text[m.end():]


def _blocks(lines: list[str]) -> list[str]:
    """Parágrafos separados por linha em branco; bloco ``` ... ``` é um bloco só."""
    out, cur, fence = [], [], False
    for ln in lines:
        if ln.strip().startswith("```"):
            fence = not fence
            cur.append(ln)
            continue
        if not fence and not ln.strip():
            if cur:
                out.append("\n".join(cur))
                cur = []
            continue
        cur.append(ln)
    if cur:
        out.append("\n".join(cur))
    return out


def _sections(body: str) -> list[tuple[list[str], list[str]]]:
    """(caminho de títulos, linhas) para cada seção, ignorando # dentro de código."""
    path: list[str] = []
    sections: list[tuple[list[str], list[str]]] = [([], [])]
    fence = False
    for ln in body.splitlines():
        if ln.strip().startswith("```"):
            fence = not fence
        m = None if fence else HEADING.match(ln)
        if m:
            level = len(m.group(1))
            path = path[: level - 1] + [m.group(2).strip()]
            sections.append((list(path), []))
        else:
            sections[-1][1].append(ln)
    return [(p, ls) for p, ls in sections if any(x.strip() for x in ls) or p]


def chunk_doc(arquivo: str, text: str, max_chars: int = 1600, min_chars: int = 250) -> list[dict]:
    meta, body = parse_doc(text)
    titulo = meta.get("titulo") or Path(arquivo).stem
    base = {"arquivo": arquivo.replace("\\", "/"), "titulo": titulo, "fonte": meta.get("fonte", ""),
            "url": meta.get("url", ""), "versao": meta.get("versao_blender", "")}
    pieces: list[tuple[str, str]] = []          # (seção, texto)
    for path, lines in _sections(body):
        secao = " > ".join(path) if path else titulo
        cur = ""
        for b in _blocks(lines):
            if len(b) > max_chars and "```" not in b:          # parágrafo enorme: corta por frase
                for i in range(0, len(b), max_chars):
                    pieces.append((secao, b[i:i + max_chars]))
                continue
            if cur and len(cur) + len(b) + 2 > max_chars:
                pieces.append((secao, cur))
                cur = ""
            cur = f"{cur}\n\n{b}" if cur else b
        if cur.strip():
            pieces.append((secao, cur))
        elif path and not lines:
            pieces.append((secao, ""))
    # junta pedaços muito curtos com o seguinte do mesmo documento (título solto, seção de uma linha)
    merged: list[tuple[str, str]] = []
    for secao, txt in pieces:
        if merged and len(merged[-1][1]) < min_chars and len(merged[-1][1]) + len(txt) <= max_chars:
            s0, t0 = merged[-1]
            merged[-1] = (s0, (t0 + f"\n\n### {secao}\n" + txt).strip())
        else:
            merged.append((secao, txt))
    chunks = []
    for k, (secao, txt) in enumerate(merged):
        if not txt.strip():
            continue
        chunks.append({**base, "id": f"{base['arquivo']}#{k}", "secao": secao,
                       "texto": f"{titulo} — {secao}\n\n{txt.strip()}"})
    return chunks


def load_chunks(docs_dir: Path, max_chars: int = 1600) -> list[dict]:
    root = Path(docs_dir).resolve().parents[1] if Path(docs_dir).name == "docs" else Path(docs_dir)
    out: list[dict] = []
    for p in sorted(Path(docs_dir).rglob("*.md")):
        if p.name.upper() in ("CREDITOS.MD", "README.MD") or any(part.startswith("_") for part in p.parts):
            continue
        try:
            rel = str(p.resolve().relative_to(root))
        except ValueError:
            rel = str(p)
        out.extend(chunk_doc(rel, p.read_text(encoding="utf-8"), max_chars=max_chars))
    return out
