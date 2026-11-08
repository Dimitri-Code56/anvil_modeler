"""Monta o acervo do RAG a partir da documentação oficial do Blender (manual + referência da API Python).

Baixa só as páginas que o agente usa (modificadores, malha/bmesh, objeto, materiais e nós de shader),
converte o HTML em Markdown com a fonte no cabeçalho e grava em data/docs/. Só biblioteca padrão.

    python scripts/preparar_docs.py            # versão 5.2
    python scripts/preparar_docs.py --versao 4.2
"""
from __future__ import annotations

import argparse
import html
import json
import re
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UA = {"User-Agent": "anvil_modeler/0.1 (estudo academico; RAG de documentacao)"}

# capítulos do manual (prefixos de caminho) e páginas-semente
MANUAL_SEEDS = ["modeling/modifiers/index.html", "render/shader_nodes/index.html", "modeling/meshes/structure.html"]
MANUAL_PREFIXES = ("modeling/modifiers/", "render/shader_nodes/", "modeling/meshes/structure")
# páginas da API: tipos escolhidos por padrão de nome + páginas fixas
API_TYPE_PATTERNS = [r"Modifier$", r"^ShaderNode(Bsdf|Tex|Bump|Normal|Mix|Math|ValToRGB|Mapping|TexCoord|Output|Emission|ShaderToRGB|Separate|Combine|MapRange|RGB)"]
# fora do escopo de modelagem: modificadores de vídeo (sequencer), Grease Pencil, animação e som
API_EXCLUDE = r"^(LineStyle|Echo|Pitch|SoftBody|Surface|Volume|GreasePencil|Gpencil|Sequence|Strip|Sound|ColorBalance|WhiteBalance|HueCorrect|BrightContrast|Tonemap|Curves|Compositor|Mask|LineArt|Fmodifier|FModifier|Particle|Explode|Ocean|Cloth|Collision|DynamicPaint|Fluid|Softbody|MeshCache|MeshSequenceCache|Hook|Armature|LaplacianDeform|MeshDeform|SurfaceDeform|Corrective|UVWarp|UVProject|VertexWeight|DataTransfer|NormalEdit|Nodes)|(GpencilModifier)$"

API_FIXED = ["bmesh.ops.html", "bmesh.types.html", "bmesh.html", "mathutils.html",
             "bpy.types.Mesh.html", "bpy.types.Object.html", "bpy.types.Material.html", "bpy.types.ShaderNodeTree.html",
             "bpy.types.NodeLinks.html", "bpy.types.Nodes.html", "bpy.types.ObjectModifiers.html",
             "bpy.ops.mesh.html", "bpy.ops.object.html", "bpy.types.Curve.html", "bpy.types.SplineBezierPoints.html"]


def get(url: str) -> str:
    for tent in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read().decode("utf-8", "replace")
        except Exception:
            time.sleep(2 * (tent + 1))
    raise RuntimeError(f"falhou: {url}")


class ToMarkdown(HTMLParser):
    """Converte o conteúdo principal de uma página Sphinx em Markdown simples."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0          # profundidade dentro do <article>/<div role=main>
        self.out: list[str] = []
        self.skip = 0           # dentro de nav/script/style/headerlink
        self.pre = False
        self.title = ""

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""
        if self.depth == 0:
            if tag == "article" or a.get("role") == "main" or a.get("itemprop") == "articleBody":
                self.depth = 1
            return
        self.depth += 1
        if tag in ("script", "style", "nav") or "headerlink" in cls or "toctree-wrapper" in cls:
            self.skip += 1
            return
        if self.skip:
            return
        if tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n\n" + "#" * int(tag[1]) + " ")
        elif tag == "pre":
            self.pre = True
            self.out.append("\n```\n")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "li":
            self.out.append("\n- ")
        elif tag in ("p", "dl", "table", "div"):
            self.out.append("\n")
        elif tag == "dt":
            self.out.append("\n**")
        elif tag == "dd":
            self.out.append("\n  ")
        elif tag in ("td", "th"):
            self.out.append(" | ")
        elif tag == "br":
            self.out.append("\n")

    def handle_endtag(self, tag):
        if self.depth == 0:
            return
        if self.skip:
            if tag in ("script", "style", "nav", "a", "div", "span"):
                self.skip -= 1
            self.depth -= 1
            return
        if tag == "pre":
            self.pre = False
            self.out.append("\n```\n")
        elif tag == "code" and not self.pre:
            self.out.append("`")
        elif tag == "dt":
            self.out.append("**")
        elif tag in ("h1", "h2", "h3", "h4"):
            self.out.append("\n")
        self.depth -= 1

    def handle_data(self, data):
        if self.depth and not self.skip:
            self.out.append(data if self.pre else re.sub(r"\s+", " ", data))

    def markdown(self) -> str:
        txt = "".join(self.out)
        txt = re.sub(r"[ \t]+\n", "\n", txt)
        txt = re.sub(r"\n{3,}", "\n\n", txt)
        txt = txt.replace("¶", "").replace("\u200b", "")
        return txt.strip()


def page_title(raw: str) -> str:
    m = re.search(r"<title>(.*?)</title>", raw, re.S)
    t = html.unescape(m.group(1)).strip() if m else ""
    return re.split(r" [—\-|] Blender", t)[0].strip()


def save(dest: Path, url: str, raw: str, fonte: str, versao: str) -> dict:
    p = ToMarkdown(); p.feed(raw)
    body = p.markdown()
    title = page_title(raw)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(f"---\ntitulo: {title}\nfonte: {fonte}\nversao_blender: {versao}\nurl: {url}\n---\n\n{body}\n",
                    encoding="utf-8")
    return {"arquivo": str(dest.relative_to(ROOT)), "titulo": title, "fonte": fonte, "url": url, "chars": len(body)}


def crawl_manual(base: str, out: Path, versao: str, limite: int) -> list[dict]:
    fila, vistos, itens = list(MANUAL_SEEDS), set(), []
    while fila and len(itens) < limite:
        rel = fila.pop(0)
        if rel in vistos:
            continue
        vistos.add(rel)
        url = urllib.parse.urljoin(base, rel)
        raw = get(url)
        itens.append(save(out / "manual" / rel.replace(".html", ".md"), url, raw, "manual", versao))
        for href in re.findall(r'href="([^"#?]+\.html)', raw):
            nxt = urllib.parse.urljoin(url, href)
            if nxt.startswith(base):
                r = nxt[len(base):]
                if r.startswith(MANUAL_PREFIXES) and r not in vistos:
                    fila.append(r)
        time.sleep(0.15)
    return itens


def api_pages(base: str) -> list[str]:
    idx = get(base + "bpy.types.html")
    tipos = sorted(set(re.findall(r'href="(bpy\.types\.(\w+)\.html)"', idx)))
    escolhidos = [h for h, nome in tipos if any(re.search(p, nome) for p in API_TYPE_PATTERNS)
                  and not re.search(API_EXCLUDE, nome)]
    return API_FIXED + [h for h in escolhidos if h not in API_FIXED]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--versao", default="5.2")
    ap.add_argument("--limite-manual", type=int, default=200)
    ap.add_argument("--saida", default=str(ROOT / "data" / "docs"))
    a = ap.parse_args()
    out = Path(a.saida)
    man_base = f"https://docs.blender.org/manual/en/{a.versao}/"
    api_base = f"https://docs.blender.org/api/{a.versao}/"
    itens = crawl_manual(man_base, out, a.versao, a.limite_manual)
    for rel in api_pages(api_base):
        try:
            raw = get(api_base + rel)
        except RuntimeError as e:
            print(e); continue
        itens.append(save(out / "api" / rel.replace(".html", ".md"), api_base + rel, raw, "api", a.versao))
        time.sleep(0.15)
    (out / "INDEX.json").write_text(json.dumps(itens, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "CREDITOS.md").write_text(
        "# Créditos\n\nConteúdo extraído da documentação oficial do Blender (Blender Foundation):\n"
        f"- Manual do Blender {a.versao}: {man_base} (licença CC BY-SA 4.0)\n"
        f"- Referência da API Python do Blender {a.versao}: {api_base}\n"
        "Convertido para Markdown pelo scripts/preparar_docs.py, só os capítulos de modelagem, malha e materiais.\n",
        encoding="utf-8")
    print(f"{len(itens)} páginas em {out}  ({sum(i['chars'] for i in itens) / 1e6:.1f} M caracteres)")


if __name__ == "__main__":
    main()
