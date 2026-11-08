"""Mede a busca do RAG com perguntas de resposta conhecida (para o relatório).

    python scripts/avaliar_rag.py              # só busca: BM25 x vetorial x híbrida (grátis)
    python scripts/avaliar_rag.py --agentico   # + laço avaliar/reescrever com o modelo do RAG (custa centavos)

Métricas: acerto@3 (a página certa está entre os 3 primeiros trechos) e MRR (1/posição da primeira certa).
As perguntas são em português, do jeito que um usuário escreve; os documentos estão em inglês. É aí que a
reescrita da busca (com os termos da documentação) deve fazer diferença.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from datetime import datetime

from anvil_modeler.config import settings
from anvil_modeler.rag.embeddings import get_embedder
from anvil_modeler.rag.index import DocIndex

PERGUNTAS: list[tuple[str, list[str]]] = [
    ("Como deixo as bordas do objeto arredondadas?", ["bevel"]),
    ("Como espelhar metade de um modelo para o outro lado?", ["mirror"]),
    ("Como repetir um objeto várias vezes em linha?", ["array"]),
    ("Como fazer um furo num objeto usando outro objeto?", ["boolean"]),
    ("Como dar espessura a uma superfície fina?", ["solidify"]),
    ("Como suavizar a malha subdividindo as faces?", ["subsurf", "subdivision"]),
    ("Como reduzir o número de polígonos de um modelo?", ["decimate"]),
    ("Como criar uma mola girando um perfil em volta de um eixo?", ["screw"]),
    ("Como fazer uma textura de tijolos no material?", ["brick"]),
    ("Qual nó dá relevo na superfície sem mudar a geometria?", ["bump"]),
    ("Como controlar a escala e a rotação das coordenadas da textura?", ["mapping", "texture_coordinate", "texcoord"]),
    ("Como criar um cubo direto com bmesh em Python?", ["bmesh.ops"]),
    ("Como juntar vértices duplicados que estão no mesmo lugar?", ["weld", "bmesh.ops"]),
    ("Como torcer ou dobrar um objeto com modificador?", ["simple_deform", "simpledeform"]),
    ("Como fazer uma malha grudar na superfície de outro objeto?", ["shrinkwrap"]),
    ("Qual parâmetro do material controla o quanto ele brilha ou fica fosco?", ["principled"]),
]


def acerto(res: list[dict], esperado: list[str]) -> int:
    """Posição (1..n) do primeiro trecho da página certa, ou 0."""
    for r in res:
        arq = r["arquivo"].lower().replace("\\", "/")
        if any(e.lower() in arq for e in esperado):
            return r["rank"]
    return 0


def resumo(posicoes: list[int], k: int = 3) -> dict:
    n = len(posicoes)
    return {"acerto@3": round(sum(1 for p in posicoes if 0 < p <= k) / n, 3),
            "mrr": round(sum(1 / p for p in posicoes if p) / n, 3)}


async def agentico(idx: DocIndex, embed_query) -> list[dict]:
    from anvil_modeler.rag.assistente import Recursos, busca_agentica
    rec = Recursos(settings, index=idx, embed_query=embed_query)
    linhas = []
    for pergunta, esperado in PERGUNTAS:
        docs, consultas, avaliacoes = await busca_agentica(rec, pergunta)
        linhas.append({"pergunta": pergunta, "posicao": acerto(docs, esperado), "consultas": consultas,
                       "avaliacoes": avaliacoes})
        print(f"  {'✔' if 0 < linhas[-1]['posicao'] <= 3 else '✘'} {pergunta}  ->  {consultas[-1]}")
    return linhas


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--agentico", action="store_true", help="roda também o laço avaliar/reescrever (usa o modelo)")
    a = ap.parse_args()
    idx = DocIndex.load(settings.index_dir)
    emb = get_embedder(settings.embed_model, settings.ollama_url) if idx.vectors is not None else None
    embed_query = emb[1] if emb else None
    rel = {"data": datetime.now().isoformat(timespec="seconds"), "pedacos": len(idx.chunks), "modos": {}}

    modos = ["bm25"] + (["vetorial", "hibrida"] if embed_query else [])
    for modo in modos:
        pos = [acerto(idx.search(p, k=10, embed_query=embed_query, mode=modo), e) for p, e in PERGUNTAS]
        rel["modos"][modo] = {**resumo(pos), "posicoes": pos}
    if a.agentico:
        print("laço agêntico (avaliar → reescrever):")
        linhas = asyncio.run(agentico(idx, embed_query))
        rel["modos"]["agentico"] = {**resumo([l["posicao"] for l in linhas]), "detalhe": linhas}

    print(f"\n{'modo':<10} {'acerto@3':>9} {'MRR':>6}")
    for modo, r in rel["modos"].items():
        print(f"{modo:<10} {r['acerto@3']:>9.0%} {r['mrr']:>6.2f}")
    out = settings.index_dir.parent / "avaliacao_rag.json"
    out.write_text(json.dumps(rel, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nresultado salvo em {out}")


if __name__ == "__main__":
    main()
