"""anvil-tools: servidor MCP próprio do Anvil (requisito: servidor desenvolvido pela dupla).

Fala direto com a ponte do add-on MCP do Blender (TCP, porta 9876: JSON terminado em byte nulo)
e expõe ferramentas de modelagem de ALTO NÍVEL: o modelo escolhe a ferramenta e preenche
medidas; o código bpy já testado fica aqui dentro. Isso reduz o contexto e os erros, o que
importa muito para modelos locais pequenos.

Rodar:  anvil-tools            (stdio, para o Anvil / qualquer cliente MCP)
Convenções: Z para cima, frente para -Y, chão em z = 0, medidas em metros.
"""
from __future__ import annotations

import json
import os
import socket
from datetime import datetime
from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from ..blender import ADOPT, INTROSPECT, WOOD_ALIGN, METRICS, PREP_SCENE, RENDER_TO, STAGE_SCENE, collection_name, to_blender_path
from ..blender_lib import PRESET_NAMES, STUDIO_LIB, prelude
from ..config import settings
from ..geometria import check as check_geometry
from ..guardrails import check_code, repair_code
from . import codegen

HOST = os.getenv("ANVIL_BLENDER_HOST", "localhost")
PORT = int(os.getenv("ANVIL_BLENDER_PORT", "9876"))
STATE: dict = {"asset": None, "colecao": None, "estilo": settings.default_style}
# material como texto (não enum): o schema de cada ferramenta fica bem menor, o que importa
# para o contexto de modelos locais; a biblioteca valida e aceita apelidos ("madeira" → wood)
Material = Optional[str]

mcp = FastMCP(
    "anvil-tools",
    instructions=(
        "Ferramentas para modelar no Blender peça por peça. Comece com iniciar_asset. "
        "Convenções: Z para cima, frente para -Y, chão em z=0, medidas em METROS. "
        "Posições são o CENTRO da peça (revolucao: centro da base). Depois de criar peças, use "
        "listar_objetos para conferir tamanhos e posições, e renderizar para ver o resultado. "
        "Materiais (preset): " + ", ".join(PRESET_NAMES) + "."
    ),
)


def _send(code: str, timeout: float = 180.0):
    payload = (json.dumps({"type": "execute", "code": code, "strict_json": False}) + "\0").encode("utf-8")
    try:
        with socket.create_connection((HOST, PORT), timeout=timeout) as s:
            s.sendall(payload)
            buf = b""
            while not buf.endswith(b"\0"):
                chunk = s.recv(65536)
                if not chunk:
                    break
                buf += chunk
    except OSError as e:
        raise RuntimeError(f"Não consegui falar com o Blender em {HOST}:{PORT} ({e}). O Blender está aberto com a ponte MCP ligada?")
    resp = json.loads(buf.rstrip(b"\0").decode("utf-8") or "{}")
    if resp.get("status") == "error":
        raise RuntimeError(str(resp.get("message", "erro no Blender"))[-1500:])
    return resp.get("result")


def _run(snippet: str):
    return _send(prelude(STATE["estilo"]) + "\n" + snippet)


def _col() -> str:
    if not STATE["colecao"]:
        raise RuntimeError("Nenhum asset iniciado. Chame iniciar_asset(nome) primeiro.")
    return STATE["colecao"]


def _pontos(pontos, dim: int, minimo: int, campo: str = "pontos") -> list:
    if not isinstance(pontos, list) or len(pontos) < minimo:
        raise ValueError(f"{campo}: precisa de pelo menos {minimo} pontos")
    for k, pt in enumerate(pontos):
        if not isinstance(pt, (list, tuple)) or len(pt) != dim or not all(isinstance(v, (int, float)) for v in pt):
            raise ValueError(f"{campo}[{k}] = {pt!r} é inválido: cada ponto deve ter {dim} números")
    return pontos


@mcp.tool()
def iniciar_asset(nome: str, estilo: Literal["realista", "cel-shading"] = "realista") -> dict:
    """Começa (ou recomeça do zero) um asset: cria/limpa a coleção dele no Blender. Chame antes de tudo."""
    codegen.nome_valido(nome)
    col = collection_name(nome)
    _send(PREP_SCENE.format(coll=col))
    STATE.update(asset=nome, colecao=col, estilo=estilo)
    return {"asset": nome, "colecao": col, "estilo": estilo}


@mcp.tool()
def caixa(nome: str, tamanho: list[float], posicao: list[float], rotacao_graus: list[float] = [0, 0, 0],
          chanfro: float = 0.005, material: Material = None, cor: Optional[list[float]] = None) -> dict:
    """Caixa com cantos chanfrados. tamanho=[x,y,z] em metros; posicao = centro. Bom para tábuas, tampos, travessas."""
    return _run(codegen.caixa(_col(), nome, tamanho, posicao, rotacao_graus, chanfro, material, cor))


@mcp.tool()
def cilindro(nome: str, raio: float, altura: float, posicao: list[float], eixo: Literal["X", "Y", "Z"] = "Z",
             raio_topo: Optional[float] = None, segmentos: int = 32, rotacao_graus: list[float] = [0, 0, 0],
             material: Material = None, cor: Optional[list[float]] = None) -> dict:
    """Cilindro (ou cone, com raio_topo diferente). posicao = centro. Bom para pernas retas, canos, eixos."""
    return _run(codegen.cilindro(_col(), nome, raio, altura, posicao, eixo, raio_topo, segmentos, rotacao_graus, 0.003, material, cor))


@mcp.tool()
def perfil_extrudado(nome: str, pontos: list[list[float]], espessura: float, plano: Literal["XZ", "XY", "YZ"] = "XZ",
                     posicao: list[float] = [0, 0, 0], rotacao_graus: list[float] = [0, 0, 0], chanfro: float = 0.005,
                     material: Material = None, cor: Optional[list[float]] = None) -> dict:
    """Desenha uma silhueta 2D (pontos [u,v] em ordem, sem repetir o primeiro) e dá espessura.
    plano XZ = vista de frente (u=x, v=z), XY = vista de cima (u=x, v=y), YZ = vista de lado (u=y, v=z).
    É a ferramenta principal para peças com forma própria (encosto, lateral de móvel, chapa recortada)."""
    _pontos(pontos, 2, 3)
    return _run(codegen.perfil_extrudado(_col(), nome, pontos, espessura, plano, posicao, rotacao_graus, chanfro, material, cor))


@mcp.tool()
def revolucao(nome: str, perfil: list[list[float]], posicao: list[float] = [0, 0, 0], segmentos: int = 24,
              material: Material = None, cor: Optional[list[float]] = None) -> dict:
    """Peça torneada: perfil = lista de [raio, altura] de baixo para cima, girado em volta do eixo Z.
    posicao = centro da BASE. Bom para pernas torneadas, vasos, garrafas, colunas, puxadores."""
    _pontos(perfil, 2, 2, "perfil")
    return _run(codegen.revolucao(_col(), nome, perfil, posicao, segmentos, [0, 0, 0], material, cor))


@mcp.tool()
def massa_organica(nome: str, partes: list[dict], detalhe: Optional[float] = None, suavidade: int = 10,
                   textura: float = 0.0, material: Material = None, cor: Optional[list[float]] = None) -> dict:
    """Forma orgânica contínua a partir de elipsoides sobrepostos, fundidos e suavizados (animais, rochas,
    troncos, almofadas). partes = [{"centro": [x,y,z], "raios": [rx,ry,rz], "rotacao_graus": [rx,ry,rz]}, ...].
    As partes precisam se sobrepor para fundir. textura (metros, ex. 0.002) dá relevo de pelo/rocha."""
    return _run(codegen.massa_organica(_col(), nome, partes, detalhe, suavidade, textura, material, cor))


@mcp.tool()
def tubo_por_curva(nome: str, pontos: list[list[float]], raio: float, suave: bool = True,
                   material: Material = None, cor: Optional[list[float]] = None) -> dict:
    """Tubo que passa pelos pontos [x,y,z] (curva). Bom para canos, cabos, alças, armações de metal."""
    _pontos(pontos, 3, 2)
    return _run(codegen.tubo_por_curva(_col(), nome, pontos, raio, suave, material, cor))


@mcp.tool()
def cortar(alvo: str, forma: Literal["caixa", "cilindro"], posicao: list[float], tamanho: Optional[list[float]] = None,
           raio: Optional[float] = None, altura: Optional[float] = None, eixo: Literal["X", "Y", "Z"] = "Z",
           rotacao_graus: list[float] = [0, 0, 0]) -> dict:
    """Abre um buraco/recorte no objeto alvo com uma caixa (tamanho) ou cilindro (raio, altura, eixo)."""
    return _run(codegen.cortar(_col(), alvo, forma, tamanho, raio, altura, posicao, rotacao_graus, eixo))


@mcp.tool()
def espelhar(nome: str, eixo: Literal["X", "Y", "Z"] = "X", novo_nome: Optional[str] = None) -> dict:
    """Cria uma cópia espelhada do objeto do outro lado do eixo (ex.: perna direita → esquerda)."""
    return _run(codegen.espelhar(_col(), nome, eixo, novo_nome))


@mcp.tool()
def repetir(nome: str, quantidade: int, deslocamento: list[float]) -> dict:
    """Repete o objeto N vezes, cada cópia deslocada por [dx,dy,dz] (ripas, degraus, parafusos)."""
    return _run(codegen.repetir(_col(), nome, quantidade, deslocamento))


@mcp.tool()
def aplicar_material(nome: str, material: str, cor: Optional[list[float]] = None) -> dict:
    """Troca o material do objeto por um preset da biblioteca (cor opcional [r,g,b] de 0 a 1)."""
    return _run(codegen.aplicar_material(_col(), nome, material, cor))


@mcp.tool()
def suavizar(nome: str, nivel: int = 2) -> dict:
    """Arredonda o objeto (subdivisão). Bom para peças macias: almofadas, estofados, formas orgânicas."""
    return _run(codegen.suavizar(_col(), nome, nivel))


@mcp.tool()
def remover(nome: str) -> dict:
    """Apaga um objeto DESTE asset (para refazer uma peça errada)."""
    return _run(codegen.remover(_col(), nome))


@mcp.tool()
def mover(nome: str, posicao: list[float], rotacao_graus: Optional[list[float]] = None) -> dict:
    """Move uma peça já criada para outra posição (mesma convenção da criação). Mais barato que remover e recriar."""
    return _run(codegen.mover(_col(), nome, posicao, rotacao_graus))


@mcp.tool()
def conferir() -> dict:
    """Confere a geometria do asset: peças abaixo do chão, soltas no ar, escondidas dentro de outras,
    um material só. Devolve os problemas com a correção sugerida."""
    data = _run(codegen.caixas_mundo(_col()))
    objs = (data or {}).get("objetos", [])
    return {"objetos": objs, "problemas": check_geometry(objs)}


@mcp.tool()
def listar_objetos() -> dict:
    """Lista as peças do asset com posição, dimensões e materiais. Use para conferir o que já fez."""
    return _run(codegen.listar_objetos(_col()))


@mcp.tool()
def renderizar() -> dict:
    """Renderiza o asset no estúdio (câmera 3/4, chão, luz) e devolve o caminho da imagem."""
    col = _col()
    out_dir = settings.runs_dir / "agente"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{STATE['asset']}_{datetime.now():%Y%m%d-%H%M%S}.png"
    _send(WOOD_ALIGN.format(coll=col) + STUDIO_LIB + STAGE_SCENE.format(coll=col, res=settings.render_res)
          + RENDER_TO.format(path=to_blender_path(str(out)), coll=col))
    return {"imagem": str(out)}


@mcp.tool()
def metricas() -> dict:
    """Métricas de geometria do asset: objetos, faces, caixas cruas, materiais, arestas com defeito."""
    return _send(METRICS.format(coll=_col()))


@mcp.tool()
def verificar_api(itens: list[dict]) -> dict:
    """Confere no Blender aberto se nomes da API existem nesta versão. itens = [{"kind": "modifier"|"shader_node"|
    "operator"|"bmesh_op"|"enum"|"property", "name": "..."}]. Devolve nomes reais e sugestões."""
    safe = [{"kind": str(i.get("kind", "")), "name": str(i.get("name", ""))} for i in itens][:30]
    return _send("import json\nITEMS = json.loads(" + repr(json.dumps(safe)) + ")\n" + INTROSPECT)


@mcp.tool()
def executar_python(codigo: str) -> dict:
    """Último recurso: roda um trecho bpy no asset (passa pelo guardrail). Prefira as ferramentas acima."""
    col = _col()
    codigo, _reparos = repair_code(codigo)
    erro = check_code(codigo)
    if erro:
        raise RuntimeError("Bloqueado pelo guardrail: " + erro)
    before = "\n__anvil_before = set(bpy.data.objects.keys())\n"
    return _run(before + codigo + ADOPT.format(coll=col))


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
