from __future__ import annotations

import json
from pathlib import Path

from app.config import KB_DIR
from app.rag.base import KnowledgeChunk

META_PREFIX = "<!-- supportpilot-meta: "
META_SUFFIX = " -->"

_cache: list[KnowledgeChunk] | None = None
_cache_signature: tuple[tuple[str, float], ...] | None = None


def invalidate_chunk_cache() -> None:
    global _cache, _cache_signature
    _cache = None
    _cache_signature = None


def load_knowledge_chunks(*, force_reload: bool = False) -> list[KnowledgeChunk]:
    global _cache, _cache_signature

    signature = _kb_signature()
    if not force_reload and _cache is not None and _cache_signature == signature:
        return _cache

    chunks: list[KnowledgeChunk] = []
    if not KB_DIR.exists():
        _cache = chunks
        _cache_signature = signature
        return chunks

    for path in sorted(KB_DIR.glob("*.md")):
        if not _is_document_enabled(path):
            continue
        content = _read_body(path)
        for index, (title, chunk) in enumerate(_split_markdown_sections(content)):
            chunks.append(
                KnowledgeChunk(
                    source=f"{path.name}#{title}",
                    chunk_id=f"{path.name}#{index + 1}",
                    title=title,
                    content=chunk,
                )
            )

    _cache = chunks
    _cache_signature = signature
    return chunks


def count_enabled_documents() -> int:
    if not KB_DIR.exists():
        return 0
    return sum(1 for path in KB_DIR.glob("*.md") if _is_document_enabled(path))


def _kb_signature() -> tuple[tuple[str, float], ...]:
    if not KB_DIR.exists():
        return tuple()
    return tuple(sorted((path.name, path.stat().st_mtime) for path in KB_DIR.glob("*.md")))


def _is_document_enabled(path: Path) -> bool:
    meta = _read_meta(path)
    return meta.get("status", "enabled") != "disabled"


def _read_meta(path: Path) -> dict[str, str]:
    raw_content = path.read_text(encoding="utf-8").strip()
    if raw_content.startswith(META_PREFIX):
        first_line, _, _ = raw_content.partition("\n")
        if first_line.endswith(META_SUFFIX):
            try:
                return json.loads(first_line[len(META_PREFIX) : -len(META_SUFFIX)])
            except json.JSONDecodeError:
                return {}
    return {}


def _read_body(path: Path) -> str:
    raw_content = path.read_text(encoding="utf-8").strip()
    if raw_content.startswith(META_PREFIX):
        first_line, _, remainder = raw_content.partition("\n")
        if first_line.endswith(META_SUFFIX):
            return remainder.strip()
    return raw_content


def _split_markdown_sections(content: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    current_title = "全文"
    current_lines: list[str] = []

    for line in content.splitlines():
        if line.startswith("## "):
            if current_lines:
                sections.append((current_title, "\n".join(current_lines).strip()))
            current_title = line.removeprefix("## ").strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        sections.append((current_title, "\n".join(current_lines).strip()))

    return [(title, body) for title, body in sections if body]
