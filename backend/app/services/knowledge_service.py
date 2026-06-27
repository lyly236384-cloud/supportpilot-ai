from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

from app.config import KB_DIR
from app.models.schemas import (
    KnowledgeDocument,
    KnowledgeDocumentCreate,
    KnowledgeDocumentDetail,
    KnowledgeDocumentUpdate,
)


# Legacy/demo seed fallback categories. User-created documents should rely on
# the explicit category stored in the markdown meta comment.
CATEGORY_BY_PREFIX = {
    "complaint": "风险升级",
    "damaged": "异常处理",
    "exchange": "服务政策",
    "invoice": "财务流程",
    "refund": "服务政策",
    "return": "服务政策",
    "shipping": "履约规则",
    "support": "回复规范",
}

MAX_IMPORT_BYTES = 1_000_000
ALLOWED_IMPORT_SUFFIXES = {".md", ".markdown"}

META_PREFIX = "<!-- supportpilot-meta: "
META_SUFFIX = " -->"


def list_knowledge_documents() -> list[KnowledgeDocument]:
    documents: list[KnowledgeDocument] = []
    if not KB_DIR.exists():
        return documents

    usage_counts = aggregate_document_usage_counts()

    for path in sorted(KB_DIR.glob("*.md")):
        meta, content = _read_markdown(path)
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        title = meta.get("title") or _extract_title(lines, path.stem)
        documents.append(
            KnowledgeDocument(
                id=path.stem,
                title=title,
                category=meta.get("category") or _infer_category(path.stem),
                status=meta.get("status") or "enabled",
                source_type=meta.get("source_type") or "markdown",
                updated_at=_format_mtime(path.stat().st_mtime),
                usage_count=usage_counts.get(path.stem, 0),
                preview=_build_preview(lines, title),
            )
        )
    return documents


def get_knowledge_document(document_id: str) -> KnowledgeDocumentDetail:
    path = _document_path(document_id)
    meta, content = _read_markdown(path)
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    title = meta.get("title") or _extract_title(lines, path.stem)
    usage_counts = aggregate_document_usage_counts()
    return KnowledgeDocumentDetail(
        id=path.stem,
        title=title,
        category=meta.get("category") or _infer_category(path.stem),
        status=meta.get("status") or "enabled",
        source_type=meta.get("source_type") or "markdown",
        updated_at=_format_mtime(path.stat().st_mtime),
        usage_count=usage_counts.get(path.stem, 0),
        preview=_build_preview(lines, title),
        content=content,
    )


def aggregate_document_usage_counts() -> dict[str, int]:
    from app.storage import repository

    counts: Counter[str] = Counter()
    for row in repository.read_trace_rows():
        citations = row.get("citations") or []
        for citation in citations:
            source = citation.get("source") if isinstance(citation, dict) else ""
            document_id = _citation_source_to_document_id(source)
            if document_id:
                counts[document_id] += 1
    return dict(counts)


def _citation_source_to_document_id(source: str) -> str | None:
    file_part = source.split("#", 1)[0].strip()
    if not file_part:
        return None
    return Path(file_part).stem


def create_knowledge_document(payload: KnowledgeDocumentCreate) -> KnowledgeDocumentDetail:
    document_id = _generate_document_id(payload.title)
    path = KB_DIR / f"{document_id}.md"
    if path.exists():
        raise ValueError(f"Knowledge document already exists: {document_id}")
    _write_markdown(
        path=path,
        title=payload.title.strip(),
        category=payload.category.strip(),
        status=payload.status.strip() or "enabled",
        content=payload.content.strip(),
    )
    _invalidate_rag_cache()
    return get_knowledge_document(document_id)


def import_knowledge_markdown(
    *,
    filename: str,
    content_bytes: bytes,
    title: str | None = None,
    category: str | None = None,
    status: str = "enabled",
) -> KnowledgeDocumentDetail:
    suffix = Path(filename or "").suffix.lower()
    if suffix not in ALLOWED_IMPORT_SUFFIXES:
        raise ValueError("Only Markdown files (.md, .markdown) can be imported")
    if len(content_bytes) > MAX_IMPORT_BYTES:
        raise ValueError("Markdown file is too large; maximum size is 1MB")

    try:
        raw_content = content_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("Markdown file must be UTF-8 encoded") from exc

    meta, body = _parse_markdown(raw_content)
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    resolved_title = (title or meta.get("title") or _extract_title(lines, Path(filename).stem)).strip()
    document_id = _generate_document_id(resolved_title, fallback=Path(filename).stem)
    path = KB_DIR / f"{document_id}.md"
    if path.exists():
        raise ValueError(f"Knowledge document already exists: {document_id}")

    resolved_category = (category or meta.get("category") or _infer_category(document_id)).strip()
    resolved_status = (status or meta.get("status") or "enabled").strip()
    _write_markdown(
        path=path,
        title=resolved_title,
        category=resolved_category,
        status=resolved_status,
        content=body.strip(),
    )
    _invalidate_rag_cache()
    return get_knowledge_document(document_id)


def update_knowledge_document(
    document_id: str, payload: KnowledgeDocumentUpdate
) -> KnowledgeDocumentDetail:
    current = get_knowledge_document(document_id)
    path = _document_path(document_id)
    _write_markdown(
        path=path,
        title=(payload.title or current.title).strip(),
        category=(payload.category or current.category).strip(),
        status=(payload.status or current.status).strip(),
        content=(payload.content if payload.content is not None else current.content).strip(),
    )
    _invalidate_rag_cache()
    return get_knowledge_document(document_id)


def delete_knowledge_document(document_id: str) -> None:
    path = _document_path(document_id)
    if not path.exists():
        raise FileNotFoundError(document_id)
    path.unlink()
    _invalidate_rag_cache()


def reindex_knowledge_base():
    from datetime import datetime, timezone

    from app.config.settings import get_rag_retriever
    from app.models.schemas import KnowledgeReindexResponse
    from app.rag.chunk_loader import count_enabled_documents, invalidate_chunk_cache, load_knowledge_chunks

    invalidate_chunk_cache()
    chunks = load_knowledge_chunks(force_reload=True)
    return KnowledgeReindexResponse(
        document_count=count_enabled_documents(),
        chunk_count=len(chunks),
        retriever=get_rag_retriever(),
        indexed_at=datetime.now(timezone.utc).isoformat(),
    )


def _extract_title(lines: list[str], fallback: str) -> str:
    for line in lines:
        if line.startswith("# "):
            return line.removeprefix("# ").strip()
    return fallback.replace("_", " ").title()


def _infer_category(document_id: str) -> str:
    prefix = document_id.split("_", 1)[0]
    return CATEGORY_BY_PREFIX.get(prefix, "知识文档")


def _build_preview(lines: list[str], title: str) -> str:
    for line in lines:
        if not line.startswith("#"):
            return line[:120]
    return title


def _format_mtime(timestamp: float) -> str:
    from datetime import datetime, timezone

    return datetime.fromtimestamp(timestamp, timezone.utc).isoformat()


_SAFE_DOCUMENT_ID_RE = re.compile(r"^[a-zA-Z0-9_][-a-zA-Z0-9_]*$")


def _document_path(document_id: str) -> Path:
    """Resolve a document_id to a file path inside KB_DIR.

    Rejects any document_id that contains path traversal characters or does not
    conform to the expected slug format produced by _generate_document_id.
    """
    if not _SAFE_DOCUMENT_ID_RE.match(document_id):
        raise ValueError(f"Invalid document_id: {document_id!r}")
    path = (KB_DIR / f"{document_id}.md").resolve()
    if not str(path).startswith(str(KB_DIR.resolve())):
        raise ValueError(f"Path traversal blocked for document_id: {document_id!r}")
    if not path.exists():
        raise FileNotFoundError(document_id)
    return path


def _parse_markdown(raw_content: str) -> tuple[dict[str, str], str]:
    content = raw_content.strip()
    if content.startswith(META_PREFIX):
        first_line, _, remainder = content.partition("\n")
        if first_line.endswith(META_SUFFIX):
            try:
                meta = json.loads(first_line[len(META_PREFIX) : -len(META_SUFFIX)])
                return meta, remainder.strip()
            except json.JSONDecodeError:
                pass
    return {}, content


def _read_markdown(path: Path) -> tuple[dict[str, str], str]:
    return _parse_markdown(path.read_text(encoding="utf-8"))


def _write_markdown(path: Path, title: str, category: str, status: str, content: str) -> None:
    KB_DIR.mkdir(parents=True, exist_ok=True)
    body = _normalize_content(title, content)
    meta = json.dumps(
        {
            "title": title,
            "category": category,
            "status": status,
            "source_type": "markdown",
        },
        ensure_ascii=False,
    )
    path.write_text(f"{META_PREFIX}{meta}{META_SUFFIX}\n{body}\n", encoding="utf-8")


def _normalize_content(title: str, content: str) -> str:
    clean_content = content.strip()
    if clean_content.startswith("# "):
        return clean_content
    if clean_content:
        return f"# {title}\n\n{clean_content}"
    return f"# {title}"


def _generate_document_id(title: str, fallback: str = "knowledge_document") -> str:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized.lower()).strip("_")
    if slug:
        return slug
    normalized_fallback = unicodedata.normalize("NFKD", fallback).encode("ascii", "ignore").decode("ascii")
    fallback_slug = re.sub(r"[^a-zA-Z0-9]+", "_", normalized_fallback.lower()).strip("_")
    return fallback_slug or "knowledge_document"


def _invalidate_rag_cache() -> None:
    from app.rag.chunk_loader import invalidate_chunk_cache

    invalidate_chunk_cache()
