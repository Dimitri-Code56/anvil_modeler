"""Embeddings locais pelo Ollama (nomic-embed-text): grátis e rodam na sua GPU.

A Anthropic não oferece modelo de embeddings; o modelo que conversa (Haiku ou local) recebe os
pedaços como texto, então pode ser de outra empresa. O nomic pede prefixos diferentes para
documento e pergunta ("search_document:" / "search_query:").
"""
from __future__ import annotations

from typing import Callable, Optional


def get_embedder(model: str, base_url: str) -> Optional[tuple[Callable, Callable]]:
    """(embed_docs, embed_query) ou None se o langchain-ollama não estiver instalado."""
    try:
        from langchain_ollama import OllamaEmbeddings
    except ImportError:
        return None
    emb = OllamaEmbeddings(model=model, base_url=base_url)
    nomic = "nomic" in model

    def embed_docs(texts: list[str]) -> list[list[float]]:
        return emb.embed_documents([("search_document: " + t) if nomic else t for t in texts])

    def embed_query(text: str) -> list[float]:
        return emb.embed_query(("search_query: " + text) if nomic else text)

    return embed_docs, embed_query
