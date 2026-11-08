"""Indexa a documentação de data/docs em data/index (pedaços + vetores do nomic-embed-text + BM25).

    python scripts/indexar_docs.py               # com embeddings (Ollama ligado + `ollama pull nomic-embed-text`)
    python scripts/indexar_docs.py --sem-vetores # só busca por palavra-chave (BM25)
"""
from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime

from anvil_modeler.config import settings
from anvil_modeler.rag.chunking import load_chunks
from anvil_modeler.rag.embeddings import get_embedder
from anvil_modeler.rag.index import build_index


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sem-vetores", action="store_true", help="não calcula embeddings (só BM25)")
    ap.add_argument("--max-chars", type=int, default=1600, help="tamanho máximo de cada pedaço")
    ap.add_argument("--lote", type=int, default=32)
    a = ap.parse_args()

    t0 = time.time()
    chunks = load_chunks(settings.docs_dir, max_chars=a.max_chars)
    if not chunks:
        sys.exit(f"Nenhum documento em {settings.docs_dir}. Rode antes: python scripts/preparar_docs.py")
    print(f"{len(chunks)} pedaços de {len({c['arquivo'] for c in chunks})} páginas "
          f"(média {sum(len(c['texto']) for c in chunks) // len(chunks)} caracteres)")

    embed_docs = None
    if not a.sem_vetores:
        emb = get_embedder(settings.embed_model, settings.ollama_url)
        if emb is None:
            sys.exit('langchain-ollama não instalado: pip install -e ".[dev]"  (ou use --sem-vetores)')
        embed_docs, embed_query = emb
        try:
            dim = len(embed_query("teste"))
        except Exception as e:
            sys.exit(f"Não consegui gerar embeddings com '{settings.embed_model}' em {settings.ollama_url}: {e}\n"
                     f"Ligue o Ollama (sudo systemctl start ollama) e baixe o modelo (ollama pull {settings.embed_model}),"
                     " ou rode com --sem-vetores.")
        print(f"embeddings: {settings.embed_model} ({dim} dimensões)")

    def progresso(feito: int, total: int) -> None:
        pct = feito * 100 // total
        barra = "#" * (pct // 4)
        el = time.time() - t0
        resta = el / feito * (total - feito) if feito else 0
        print(f"\r[{barra:<25}] {feito}/{total} pedaços  {pct:3d}%  falta ~{resta:.0f}s ", end="", flush=True)

    idx = build_index(chunks, embed_docs, batch=a.lote, progress=progresso if embed_docs else None,
                      meta={"criado": datetime.now().isoformat(timespec="seconds"), "pedacos": len(chunks),
                            "embed_model": settings.embed_model if embed_docs else None,
                            "max_chars": a.max_chars, "docs": str(settings.docs_dir)})
    if embed_docs:
        print()
    idx.save(settings.index_dir)
    print(f"índice salvo em {settings.index_dir} em {time.time() - t0:.0f}s "
          f"({'híbrido: BM25 + vetores' if idx.vectors is not None else 'só BM25'})")


if __name__ == "__main__":
    main()
