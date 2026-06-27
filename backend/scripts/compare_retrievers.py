from __future__ import annotations

import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.rag.retriever import retrieve_knowledge  # noqa: E402

QUERIES = [
    "我的快递什么时候发货？",
    "我想退货，七天无理由怎么申请？",
    "发票抬头写错了，可以修改吗？",
    "收到的杯子碎了，外包装也变形了",
    "我要投诉你们并要求赔偿",
    "订单已经发货了，还能修改收货地址吗？",
]

STRATEGIES = ["keyword", "vector"]


def compare_retrievers(top_k: int = 3) -> None:
    original_strategy = os.getenv("RAG_RETRIEVER")

    for query in QUERIES:
        print("=" * 80)
        print(f"Query: {query}")

        for strategy in STRATEGIES:
            os.environ["RAG_RETRIEVER"] = strategy
            citations = retrieve_knowledge(query, top_k=top_k)
            print(f"\n[{strategy}]")

            if not citations:
                print("  No citations found")
                continue

            for index, citation in enumerate(citations, start=1):
                print(f"  {index}. {citation.source} | score={citation.score}")
                print(f"     {citation.snippet[:120]}")

        print()

    if original_strategy is None:
        os.environ.pop("RAG_RETRIEVER", None)
    else:
        os.environ["RAG_RETRIEVER"] = original_strategy


if __name__ == "__main__":
    compare_retrievers()
