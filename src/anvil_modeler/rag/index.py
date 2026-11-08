"""Índice híbrido da documentação: BM25 (palavra-chave) + vetores (embeddings), unidos por RRF.

Por que os dois: a busca vetorial acha "como arredondar as bordas" (sentido), a BM25 acha
`BevelModifier.segments` (nome exato). Documentação de API precisa das duas.

Arquivos em data/index/: chunks.jsonl, vectors.npy (float32, normalizados) e meta.json.
Sem vetores (Ollama desligado), a busca cai para BM25 sozinha.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Optional

import numpy as np

EmbedFn = Callable[[list[str]], list[list[float]]]

_WORD = re.compile(r"[A-Za-z][A-Za-z0-9_]*|\d+")
_CAMEL = re.compile(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+")
STOP = {"the", "a", "an", "of", "to", "in", "and", "or", "is", "for", "on", "with", "as", "by", "be", "this", "that",
        "it", "are", "from", "at", "de", "da", "do", "das", "dos", "e", "o", "os", "as", "um", "uma", "para", "com",
        "como", "que", "no", "na", "em", "se", "por", "type", "default"}


def tokenize(text: str) -> list[str]:
    """Palavras + partes de identificadores: BevelModifier -> bevelmodifier, bevel, modifier; use_clamp -> use, clamp."""
    out: list[str] = []
    for w in _WORD.findall(text):
        lw = w.lower()
        if lw not in STOP and len(lw) > 1:
            out.append(lw)
        parts = [p.lower() for seg in w.split("_") for p in _CAMEL.findall(seg)]
        if len(parts) > 1:
            out.extend(p for p in parts if p not in STOP and len(p) > 1)
    return out


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.tf = [Counter(d) for d in docs]
        self.len = np.array([len(d) for d in docs], dtype=np.float32)
        self.avg = float(self.len.mean()) if len(docs) else 1.0
        df = Counter(t for d in self.tf for t in d)
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: list[str]) -> np.ndarray:
        s = np.zeros(len(self.tf), dtype=np.float32)
        for t in set(query):
            idf = self.idf.get(t)
            if idf is None:
                continue
            for i, tf in enumerate(self.tf):
                f = tf.get(t)
                if f:
                    s[i] += idf * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * self.len[i] / self.avg))
        return s


class DocIndex:
    def __init__(self, chunks: list[dict], vectors: Optional[np.ndarray] = None, meta: Optional[dict] = None):
        self.chunks = chunks
        self.vectors = vectors
        self.meta = meta or {}
        self.bm25 = BM25([tokenize(c["texto"]) for c in chunks])

    # ---- persistência ----------------------------------------------------
    def save(self, out_dir: Path) -> None:
        out = Path(out_dir)
        out.mkdir(parents=True, exist_ok=True)
        with open(out / "chunks.jsonl", "w", encoding="utf-8") as f:
            for c in self.chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        if self.vectors is not None:
            np.save(out / "vectors.npy", self.vectors.astype(np.float32))
        (out / "meta.json").write_text(json.dumps(self.meta, ensure_ascii=False, indent=1), encoding="utf-8")

    @classmethod
    def load(cls, index_dir: Path) -> "DocIndex":
        d = Path(index_dir)
        if not (d / "chunks.jsonl").exists():
            raise FileNotFoundError(f"Índice não encontrado em {d}. Rode: python scripts/indexar_docs.py")
        chunks = [json.loads(l) for l in (d / "chunks.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
        vec = np.load(d / "vectors.npy") if (d / "vectors.npy").exists() else None
        meta = json.loads((d / "meta.json").read_text(encoding="utf-8")) if (d / "meta.json").exists() else {}
        return cls(chunks, vec, meta)

    # ---- busca -----------------------------------------------------------
    def search(self, query: str, k: int = 5, embed_query: Optional[Callable[[str], list[float]]] = None,
               mode: str = "hibrida", pool: int = 50) -> list[dict]:
        """mode: hibrida | bm25 | vetorial. Devolve os pedaços com 'score' e 'rank'."""
        ranks: list[list[int]] = []
        if mode in ("hibrida", "bm25"):
            s = self.bm25.scores(tokenize(query))
            top = [int(i) for i in np.argsort(-s)[:pool] if s[i] > 0]
            ranks.append(top)
        if mode in ("hibrida", "vetorial") and self.vectors is not None and embed_query is not None:
            try:
                q = np.asarray(embed_query(query), dtype=np.float32)
                q /= (np.linalg.norm(q) or 1.0)
                sims = self.vectors @ q
                ranks.append([int(i) for i in np.argsort(-sims)[:pool]])
            except Exception:
                pass                                            # sem embeddings: segue só com BM25
        if not ranks:
            return []
        fused: dict[int, float] = {}
        for lst in ranks:                                       # Reciprocal Rank Fusion
            for r, i in enumerate(lst):
                fused[i] = fused.get(i, 0.0) + 1.0 / (60 + r)
        best = sorted(fused, key=lambda i: -fused[i])[:k]
        return [{**self.chunks[i], "score": round(fused[i], 5), "rank": n + 1} for n, i in enumerate(best)]


def build_index(chunks: list[dict], embed_docs: Optional[EmbedFn] = None, batch: int = 32,
                progress: Optional[Callable[[int, int], None]] = None, meta: Optional[dict] = None) -> DocIndex:
    vectors = None
    if embed_docs is not None:
        rows: list[list[float]] = []
        for i in range(0, len(chunks), batch):
            rows.extend(embed_docs([c["texto"] for c in chunks[i:i + batch]]))
            if progress:
                progress(min(i + batch, len(chunks)), len(chunks))
        vectors = np.asarray(rows, dtype=np.float32)
        vectors /= np.linalg.norm(vectors, axis=1, keepdims=True).clip(min=1e-9)
    return DocIndex(chunks, vectors, meta)
