import pytest

from app.rag.keyword_retriever import KeywordRetriever
from app.rag.retriever import get_retriever, retrieve_knowledge
from app.rag.vector_retriever import VectorRetriever
from app.rag.hybrid_retriever import HybridRetriever


def test_get_default_retriever(monkeypatch):
    monkeypatch.delenv("RAG_RETRIEVER", raising=False)
    assert isinstance(get_retriever(), HybridRetriever)


def test_get_keyword_retriever(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "keyword")
    assert isinstance(get_retriever(), KeywordRetriever)


def test_get_vector_retriever(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "vector")
    assert isinstance(get_retriever(), VectorRetriever)


def test_get_hybrid_retriever(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "hybrid")
    assert isinstance(get_retriever(), HybridRetriever)


def test_unknown_retriever_raises_error(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "unknown")
    with pytest.raises(ValueError):
        get_retriever()


def test_retrieve_shipping_policy():
    citations = retrieve_knowledge("我的快递什么时候发货？")
    assert citations
    assert "shipping_policy" in citations[0].source


def test_retrieve_return_policy():
    citations = retrieve_knowledge("我想退货，七天无理由怎么申请？")
    assert citations
    sources = {c.source for c in citations}
    assert any("return_policy" in source for source in sources)


def test_retrieve_invoice_policy():
    citations = retrieve_knowledge("发票抬头写错了，可以修改吗？")
    assert citations
    assert "invoice_policy" in citations[0].source


def test_retrieve_damaged_goods_sop():
    citations = retrieve_knowledge("收到的杯子碎了，外包装也变形了")
    assert citations
    sources = {c.source for c in citations}
    assert any("damaged_goods_sop" in source for source in sources)


def test_retrieve_complaint_escalation():
    citations = retrieve_knowledge("我要投诉你们并要求赔偿")
    assert citations
    sources = {c.source for c in citations}
    assert any("complaint_escalation" in source for source in sources)


def test_vector_retriever_returns_relevant_shipping_citation(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "vector")
    citations = retrieve_knowledge("订单已经发货了，还能修改收货地址吗？")
    assert citations
    assert any("shipping_policy" in c.source for c in citations)


def test_vector_retriever_returns_relevant_refund_citation(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "vector")
    citations = retrieve_knowledge("退款已经通过了，多久能到账？")
    assert citations
    assert any("refund_policy" in c.source for c in citations)


def test_hybrid_retriever_fuses_keyword_and_vector_results(monkeypatch):
    monkeypatch.setenv("RAG_RETRIEVER", "hybrid")
    citations = retrieve_knowledge("我要投诉你们并要求赔偿")
    assert citations
    assert any("complaint_escalation" in c.source for c in citations)


# --- Dense (embedding) retriever -------------------------------------------
# These require the optional ML stack (fastembed + faiss). When it is missing
# or the model cannot be loaded, the dense retriever is unavailable and we skip
# rather than fail, mirroring the production graceful-degradation behavior.

def _dense_or_skip():
    pytest.importorskip("fastembed")
    pytest.importorskip("faiss")
    from app.rag.dense_retriever import get_dense_retriever

    retriever = get_dense_retriever()
    if retriever is None:
        pytest.skip("dense retriever unavailable (model not loadable offline)")
    return retriever


def test_dense_retriever_semantic_match_without_shared_keywords():
    # "快递一直不动" shares no surface tokens with "物流更新延迟"; only a
    # semantic retriever should connect them.
    retriever = _dense_or_skip()
    citations = retriever.retrieve("快递一直不动怎么办", top_k=3)
    assert citations
    assert any("shipping_policy" in c.source for c in citations)
    assert citations[0].score > 0.45


def test_dense_retriever_rejects_unrelated_greeting():
    # Embeddings always return a nearest chunk; the absolute threshold must
    # filter out off-topic greetings so they don't get spurious citations.
    retriever = _dense_or_skip()
    assert retriever.retrieve("你好", top_k=3) == []
