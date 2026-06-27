from __future__ import annotations

import re

from app.models.schemas import Citation
from app.rag.base import BaseRetriever, KnowledgeChunk
from app.rag.chunk_loader import load_knowledge_chunks
from app.templates.loader import get_domain_terms

# Domain terms are supplied by the active SupportPilot template.


class KeywordRetriever(BaseRetriever):
    def retrieve(self, query: str, top_k: int = 3) -> list[Citation]:
        query_tokens = self._tokenize(query)
        scored: list[tuple[float, KnowledgeChunk]] = []

        for chunk in self._load_chunks():
            score = self._score_chunk(query_tokens, chunk)
            if score > 0:
                scored.append((score, chunk))

        scored.sort(key=lambda item: item[0], reverse=True)
        filtered = self._filter_weak_matches(scored)

        citations: list[Citation] = []
        for score, chunk in filtered[:top_k]:
            snippet = chunk.content.replace("\n", " ")[:220]
            citations.append(Citation(source=chunk.source, snippet=snippet, score=round(score, 3)))

        return citations

    def _tokenize(self, text: str) -> set[str]:
        normalized = text.lower()
        tokens = set(re.findall(r"[a-zA-Z0-9_]+", normalized))
        tokens.update(word for word in get_domain_terms() if word.lower() in normalized)
        return tokens

    def _load_chunks(self) -> list[KnowledgeChunk]:
        return load_knowledge_chunks()

    def _filter_weak_matches(self, scored: list[tuple[float, KnowledgeChunk]]) -> list[tuple[float, KnowledgeChunk]]:
        if not scored:
            return []

        best_score = scored[0][0]
        min_score = max(2.0, best_score * 0.35)
        return [(score, chunk) for score, chunk in scored if score >= min_score]

    def _score_chunk(self, query_tokens: set[str], chunk: KnowledgeChunk) -> float:
        title_tokens = self._tokenize(chunk.title)
        content_tokens = self._tokenize(chunk.content)

        title_overlap = query_tokens & title_tokens
        content_overlap = query_tokens & content_tokens

        if not content_overlap and not title_overlap:
            return 0

        title_score = len(title_overlap) * 2.0
        content_score = len(content_overlap)
        coverage_score = len(content_overlap | title_overlap) / max(len(query_tokens), 1)
        return title_score + content_score + coverage_score
