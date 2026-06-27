import json

import pytest

from app.rag.chunk_loader import count_enabled_documents, invalidate_chunk_cache, load_knowledge_chunks
from app.rag.retriever import retrieve_knowledge


@pytest.fixture(autouse=True)
def reset_chunk_cache():
    invalidate_chunk_cache()
    yield
    invalidate_chunk_cache()


def test_disabled_document_excluded_from_chunks(tmp_path, monkeypatch):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    enabled = kb_dir / "enabled_doc.md"
    enabled.write_text("# 启用文档\n\n## 发货\n\n48 小时内发货。", encoding="utf-8")
    disabled = kb_dir / "disabled_doc.md"
    meta = {"status": "disabled", "title": "禁用文档"}
    disabled.write_text(
        f"<!-- supportpilot-meta: {json.dumps(meta, ensure_ascii=False)} -->\n\n"
        "# 禁用文档\n\n## 秘密\n\n不应被检索。",
        encoding="utf-8",
    )

    monkeypatch.setattr("app.rag.chunk_loader.KB_DIR", kb_dir)
    chunks = load_knowledge_chunks(force_reload=True)
    sources = {chunk.source for chunk in chunks}
    assert any("enabled_doc" in source for source in sources)
    assert not any("disabled_doc" in source for source in sources)
    assert count_enabled_documents() == 1


def test_disabled_document_not_retrieved(tmp_path, monkeypatch):
    kb_dir = tmp_path / "kb"
    kb_dir.mkdir()
    enabled = kb_dir / "shipping_policy.md"
    enabled.write_text(
        "# 物流政策\n\n## 发货时效\n\n现货订单支付成功后 48 小时内发货。",
        encoding="utf-8",
    )
    disabled = kb_dir / "secret_policy.md"
    meta = {"status": "disabled", "title": "内部政策"}
    disabled.write_text(
        f"<!-- supportpilot-meta: {json.dumps(meta, ensure_ascii=False)} -->\n\n"
        "# 内部政策\n\n## 投诉赔偿\n\n全额赔偿无需审批。",
        encoding="utf-8",
    )

    monkeypatch.setattr("app.rag.chunk_loader.KB_DIR", kb_dir)
    monkeypatch.setattr("app.config.KB_DIR", kb_dir)
    monkeypatch.setenv("RAG_RETRIEVER", "keyword")

    citations = retrieve_knowledge("投诉赔偿全额")
    sources = {c.source for c in citations}
    assert not any("secret_policy" in source for source in sources)
