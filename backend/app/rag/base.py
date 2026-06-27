from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.config import KB_DIR
from app.models.schemas import Citation


@dataclass(frozen=True)
class KnowledgeChunk:
    source: str
    chunk_id: str
    title: str
    content: str


class BaseRetriever(ABC):
    @abstractmethod
    def retrieve(self, query: str, top_k: int = 3) -> list[Citation]:
        """Return the most relevant knowledge citations for a user query."""
