from __future__ import annotations

import threading

from app.models.schemas import Citation
from app.rag.base import BaseRetriever, KnowledgeChunk
from app.rag.chunk_loader import _kb_signature, load_knowledge_chunks

# Real dense retrieval: bge-small-zh-v1.5 sentence embeddings + FAISS inner-product
# index. Embeddings are L2-normalized so inner product equals cosine similarity.
#
# This module degrades gracefully: if fastembed / faiss are unavailable or the
# model cannot be loaded (offline, no cache), get_dense_retriever() returns None
# and callers fall back to the dependency-free lexical retrievers. That keeps the
# default `mock` setup runnable without the heavy ML stack installed.

_DEFAULT_MODEL = "BAAI/bge-small-zh-v1.5"

_lock = threading.Lock()
_singleton: "DenseRetriever | None" = None
_init_failed = False


class DenseRetriever(BaseRetriever):
    """Embedding-based retriever backed by FAISS cosine similarity."""

    def __init__(self, model_name: str = _DEFAULT_MODEL) -> None:
        # Imported lazily so the package only loads when dense retrieval is used.
        import faiss  # noqa: F401
        from fastembed import TextEmbedding

        import numpy as np

        self._np = np
        self._faiss = faiss
        self._model = TextEmbedding(model_name)
        self._index = None
        self._chunks: list[KnowledgeChunk] = []
        self._signature: tuple | None = None
        self._build_lock = threading.Lock()

    def _embed(self, texts: list[str]):
        vectors = list(self._model.embed(texts))
        matrix = self._np.asarray(vectors, dtype="float32")
        # L2-normalize so FAISS inner product == cosine similarity.
        norms = self._np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return matrix / norms

    def _ensure_index(self) -> None:
        signature = _kb_signature()
        if self._index is not None and self._signature == signature:
            return

        with self._build_lock:
            # Re-check inside the lock to avoid rebuilding on concurrent calls.
            if self._index is not None and self._signature == signature:
                return

            chunks = load_knowledge_chunks()
            if not chunks:
                self._index = None
                self._chunks = []
                self._signature = signature
                return

            texts = [f"{chunk.title}\n{chunk.content}" for chunk in chunks]
            embeddings = self._embed(texts)
            dim = embeddings.shape[1]
            index = self._faiss.IndexFlatIP(dim)
            index.add(embeddings)

            self._index = index
            self._chunks = chunks
            self._signature = signature

    def retrieve(self, query: str, top_k: int = 3) -> list[Citation]:
        self._ensure_index()
        if self._index is None or not self._chunks:
            return []

        from app.config.settings import get_rag_dense_min_score

        min_score = get_rag_dense_min_score()
        query_vector = self._embed([query])
        limit = min(top_k, len(self._chunks))
        scores, indices = self._index.search(query_vector, limit)

        citations: list[Citation] = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0:
                continue
            # Reject semantically unrelated chunks; embeddings always return a
            # nearest match even for off-topic queries (e.g. greetings).
            if float(score) < min_score:
                continue
            chunk = self._chunks[idx]
            snippet = chunk.content.replace("\n", " ")[:220]
            citations.append(
                Citation(source=chunk.source, snippet=snippet, score=round(float(score), 3))
            )
        return citations


def get_dense_retriever() -> "DenseRetriever | None":
    """Return a shared DenseRetriever, or None when the ML stack is unavailable.

    The first successful call loads the embedding model (and downloads it once if
    not cached). Failures are remembered so we don't repeatedly pay the import /
    download cost on every request when the environment can't support it.
    """
    global _singleton, _init_failed

    if _singleton is not None:
        return _singleton
    if _init_failed:
        return None

    with _lock:
        if _singleton is not None:
            return _singleton
        if _init_failed:
            return None
        try:
            _singleton = DenseRetriever()
            return _singleton
        except Exception:
            _init_failed = True
            return None
