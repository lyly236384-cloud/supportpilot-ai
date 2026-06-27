from __future__ import annotations

import os
import sys
import time
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Compare the rule-based mock engine vs the real DeepSeek LLM on the same eval
# set, to quantify where the LLM helps (paraphrase / implicit / ambiguous) and
# confirm safety holds under both. Requires DEEPSEEK_API_KEY in the environment.

# Prevent run_eval's import-time mock override from clearing our API key; this
# script controls the provider per run explicitly.
os.environ["EVAL_USE_REAL_LLM"] = "1"

from run_eval import load_cases, _summarize  # noqa: E402
from app.workflow.orchestrator import run_support_workflow  # noqa: E402


def _run_one(case: dict) -> dict:
    response = run_support_workflow(case["customer_id"], case["message"])
    actual_intent = response.intent.intent.value
    actual_action = response.action.value
    expected_source = case.get("expected_source")
    citation_sources = [c.source for c in response.citations]
    if expected_source:
        rag_hit = any(expected_source in s for s in citation_sources)
    else:
        rag_hit = not response.citations
    return {
        "id": case["id"],
        "category": case.get("category", "clear"),
        "message": case["message"],
        "expected_intent": case["expected_intent"],
        "actual_intent": actual_intent,
        "intent_pass": actual_intent == case["expected_intent"],
        "expected_action": case["expected_action"],
        "actual_action": actual_action,
        "action_pass": actual_action == case["expected_action"],
        "elapsed_ms": response.elapsed_ms,
        "citations_count": len(response.citations),
        "rag_hit": rag_hit,
    }


def run_with_provider(provider: str) -> dict:
    if provider == "deepseek":
        os.environ["LLM_PROVIDER"] = "deepseek"
    else:
        os.environ["LLM_PROVIDER"] = "mock"
        os.environ["DEEPSEEK_API_KEY"] = os.environ.get("DEEPSEEK_API_KEY", "")
    cases = load_cases()
    results = [_run_one(c) for c in cases]
    return _summarize(results)


def _fmt_pct(x: float) -> str:
    return f"{x:.0%}"


def main() -> None:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("DEEPSEEK_API_KEY not set — cannot run the real-LLM comparison.")
        return

    print("Running mock (rule) engine ...")
    saved_key = os.environ.get("DEEPSEEK_API_KEY", "")
    os.environ["DEEPSEEK_API_KEY"] = ""  # force pure mock
    mock_report = run_with_provider("mock")

    os.environ["DEEPSEEK_API_KEY"] = saved_key
    print("Running DeepSeek (real LLM) engine ... (this calls the API, slower)")
    t = time.time()
    llm_report = run_with_provider("deepseek")
    llm_secs = round(time.time() - t, 1)

    print("\n" + "=" * 60)
    print("Mock (rules)  vs  DeepSeek (LLM)  — same 20-case eval set")
    print("=" * 60)
    rows = [
        ("End-to-end accuracy", "end_to_end_accuracy"),
        ("Intent accuracy", "intent_accuracy"),
        ("Action accuracy", "action_accuracy"),
        ("RAG hit rate", "rag_hit_rate"),
        ("Safety escalation", "safety_escalation_rate"),
    ]
    print(f"{'Metric':<22}{'mock':>10}{'deepseek':>12}")
    for label, key_name in rows:
        print(f"{label:<22}{_fmt_pct(mock_report[key_name]):>10}{_fmt_pct(llm_report[key_name]):>12}")

    print("\nPer-category end-to-end accuracy:")
    print(f"{'Category':<16}{'mock':>10}{'deepseek':>12}")
    cats = sorted(set(mock_report["category_accuracy"]) | set(llm_report["category_accuracy"]))
    for cat in cats:
        m = mock_report["category_accuracy"].get(cat, {}).get("accuracy", 0)
        l = llm_report["category_accuracy"].get(cat, {}).get("accuracy", 0)
        print(f"{cat:<16}{_fmt_pct(m):>10}{_fmt_pct(l):>12}")

    print(f"\nDeepSeek run wall-clock: {llm_secs}s for {llm_report['total_cases']} cases")
    print(f"(mock avg {mock_report['avg_elapsed_ms']}ms/case, "
          f"deepseek avg {llm_report['avg_elapsed_ms']}ms/case)")


if __name__ == "__main__":
    main()
