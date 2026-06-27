import pytest

from app.models.schemas import Intent
from app.rag.query_rewriter import rewrite_query
from app.rag.retriever import retrieve_knowledge


def test_rewrite_query_adds_intent_terms():
    rewritten = rewrite_query("包裹到哪了", Intent.LOGISTICS_QUESTION)
    assert "物流" in rewritten
    assert "包裹到哪了" in rewritten


def test_rewrite_query_expands_colloquial_phrase():
    rewritten = rewrite_query("我想七天无理由退货")
    assert "退货" in rewritten
    assert "退款" in rewritten


def test_rewrite_query_deduplicates_terms():
    rewritten = rewrite_query("发票抬头写错了", Intent.INVOICE_QUESTION)
    assert rewritten.count("发票") == 1


def test_retrieve_knowledge_uses_rewrite_with_intent(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "keyword")
    monkeypatch.setenv("RAG_QUERY_REWRITE", "true")
    citations = retrieve_knowledge("什么时候能收到货？", intent=Intent.LOGISTICS_QUESTION)
    assert citations
    assert any("shipping_policy" in citation.source for citation in citations)


def test_rewrite_query_for_retrieval_uses_llm_when_enabled(monkeypatch):
    from app.rag.query_rewriter import rewrite_query_for_retrieval

    monkeypatch.setenv("RAG_QUERY_REWRITE_LLM", "true")
    monkeypatch.setattr("app.services.llm_client.is_deepseek_enabled", lambda: True)
    monkeypatch.setattr(
        "app.services.llm_client.rewrite_search_query_with_llm",
        lambda query, intent=None: "物流 发货 时效",
    )

    rewritten = rewrite_query_for_retrieval("什么时候能收到货？", Intent.LOGISTICS_QUESTION)
    assert "物流" in rewritten
    assert "什么时候能收到货" in rewritten


def test_rewrite_query_for_retrieval_falls_back_without_llm(monkeypatch):
    from app.rag.query_rewriter import rewrite_query_for_retrieval

    monkeypatch.setenv("RAG_QUERY_REWRITE_LLM", "false")
    rewritten = rewrite_query_for_retrieval("什么时候能收到货？", Intent.LOGISTICS_QUESTION)
    assert "物流" in rewritten


def test_retrieve_knowledge_can_disable_rewrite(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "keyword")
    monkeypatch.setenv("RAG_QUERY_REWRITE", "false")
    citations = retrieve_knowledge("什么时候能收到货？", intent=Intent.LOGISTICS_QUESTION)
    assert isinstance(citations, list)
