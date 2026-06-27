from __future__ import annotations

import math
import re
from collections import Counter

from app.models.schemas import Citation
from app.rag.base import BaseRetriever, KnowledgeChunk
from app.rag.chunk_loader import load_knowledge_chunks
from app.templates.loader import get_domain_terms

# Domain terms are supplied by the active SupportPilot template.


class VectorRetriever(BaseRetriever):
    """Dependency-free vector-style retriever using token vectors and cosine similarity."""

    def retrieve(self, query: str, top_k: int = 3) -> list[Citation]:
        query_vector = self._to_vector(query)
        scored: list[tuple[float, KnowledgeChunk]] = []

        for chunk in self._load_chunks():
            chunk_text = f"{chunk.title}\n{chunk.content}"
            score = self._cosine_similarity(query_vector, self._to_vector(chunk_text))
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        filtered = self._filter_weak_matches(scored)

        citations: list[Citation] = []
        for score, chunk in filtered[:top_k]:
            snippet = chunk.content.replace("\n", " ")[:220]
            citations.append(Citation(source=chunk.source, snippet=snippet, score=round(score, 3)))

        return citations

    def _filter_weak_matches(self, scored: list[tuple[float, KnowledgeChunk]]) -> list[tuple[float, KnowledgeChunk]]:
        if not scored:
            return []

        best_score = scored[0][0]
        min_score = max(0.12, best_score * 0.45)
        return [(score, chunk) for score, chunk in scored if score >= min_score]

    def _tokenize(self, text: str) -> list[str]:
        normalized = text.lower()
        tokens = re.findall(r"[a-zA-Z0-9_]+", normalized)
        tokens.extend(word for word in get_domain_terms() if word.lower() in normalized)
        return tokens

    def _to_vector(self, text: str) -> Counter[str]:
        return Counter(self._tokenize(text))

    def _cosine_similarity(self, left: Counter[str], right: Counter[str]) -> float:
        if not left or not right:
            return 0

        overlap = set(left) & set(right)
        numerator = sum(left[token] * right[token] for token in overlap)
        left_norm = math.sqrt(sum(value * value for value in left.values()))
        right_norm = math.sqrt(sum(value * value for value in right.values()))
        return numerator / (left_norm * right_norm) if left_norm and right_norm else 0

    def _load_chunks(self) -> list[KnowledgeChunk]:
        return load_knowledge_chunks()
