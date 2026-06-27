import json

import pytest

from app.rag.chunk_loader import invalidate_chunk_cache
from app.services.knowledge_service import reindex_knowledge_base


@pytest.fixture(autouse=True)
def reset_chunk_cache():
    invalidate_chunk_cache()
    yield
    invalidate_chunk_cache()


def test_reindex_refreshes_chunk_cache(tmp_path, monkeypatch):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    doc = kb_dir / "new_policy.md"
    doc.write_text("# 新政策\n\n## 说明\n\n重新索引后可见。", encoding="utf-8")

    monkeypatch.setattr("app.rag.chunk_loader.KB_DIR", kb_dir)
    monkeypatch.setattr("app.config.KB_DIR", kb_dir)

    result = reindex_knowledge_base()
    assert result.document_count == 1
    assert result.chunk_count >= 1
    assert result.retriever
