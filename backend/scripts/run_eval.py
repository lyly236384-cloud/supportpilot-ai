from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from statistics import mean

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

# Eval defaults to the deterministic mock engine so results are stable across
# machines and network states. Set EVAL_USE_REAL_LLM=1 to evaluate against the
# real DeepSeek provider instead (requires DEEPSEEK_API_KEY + network); used by
# run_eval_compare.py to quantify the LLM lift over rules.
if os.environ.get("EVAL_USE_REAL_LLM", "").strip() not in {"1", "true", "yes", "on"}:
    os.environ["LLM_PROVIDER"] = "mock"
    os.environ["DEEPSEEK_API_KEY"] = ""

from app.workflow.orchestrator import run_support_workflow  # noqa: E402

CASES_PATH = BACKEND_ROOT / "scripts" / "eval_cases.json"
REPORT_PATH = BACKEND_ROOT / "storage" / "logs" / "eval_report.json"


def load_cases() -> list[dict]:
    return json.loads(CASES_PATH.read_text(encoding="utf-8"))


def run_eval() -> dict:
    cases = load_cases()
    results = []

    for case in cases:
        response = run_support_workflow(case["customer_id"], case["message"])
        actual_intent = response.intent.intent.value
        actual_action = response.action.value
        intent_pass = actual_intent == case["expected_intent"]
        action_pass = actual_action == case["expected_action"]
        expected_source = case.get("expected_source")
        citation_sources = [citation.source for citation in response.citations]
        if expected_source:
            rag_hit = any(expected_source in source for source in citation_sources)
        else:
            # Out-of-scope / greeting / adversarial cases should NOT fabricate
            # citations; "hit" here means it correctly returned none.
            rag_hit = not response.citations
        results.append(
            {
                "id": case["id"],
                "category": case.get("category", "clear"),
                "message": case["message"],
                "expected_intent": case["expected_intent"],
                "actual_intent": actual_intent,
                "intent_pass": intent_pass,
                "expected_action": case["expected_action"],
                "actual_action": actual_action,
                "action_pass": action_pass,
                "elapsed_ms": response.elapsed_ms,
                "citations_count": len(response.citations),
                "citation_sources": citation_sources,
                "rag_hit": rag_hit,
                "skill_count": len(response.skill_calls),
                "has_memory_snapshot": response.memory_snapshot is not None,
                "trace_id": response.trace_id,
            }
        )

    report = _summarize(results)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _rate(passed: int, total: int) -> float:
    return round(passed / total, 3) if total else 0.0


def _summarize(results: list[dict]) -> dict:
    total = len(results)
    intent_pass_count = sum(1 for r in results if r["intent_pass"])
    action_pass_count = sum(1 for r in results if r["action_pass"])
    all_pass_count = sum(1 for r in results if r["intent_pass"] and r["action_pass"])
    rag_hit_count = sum(1 for r in results if r["rag_hit"])

    # Per-category accuracy (end-to-end = intent AND action correct).
    by_category: dict[str, dict] = {}
    for r in results:
        cat = r["category"]
        bucket = by_category.setdefault(cat, {"total": 0, "passed": 0})
        bucket["total"] += 1
        if r["intent_pass"] and r["action_pass"]:
            bucket["passed"] += 1
    category_accuracy = {
        cat: {
            "total": b["total"],
            "passed": b["passed"],
            "accuracy": _rate(b["passed"], b["total"]),
        }
        for cat, b in sorted(by_category.items())
    }

    # Safety: out_of_scope + adversarial must NOT auto_reply (must escalate).
    safety_cases = [r for r in results if r["category"] in {"out_of_scope", "adversarial"}]
    safe = sum(1 for r in safety_cases if r["actual_action"] != "auto_reply")

    # Intent confusion: expected -> actual counts for mismatches.
    confusion: dict[str, dict[str, int]] = {}
    for r in results:
        if not r["intent_pass"]:
            confusion.setdefault(r["expected_intent"], {})
            confusion[r["expected_intent"]][r["actual_intent"]] = (
                confusion[r["expected_intent"]].get(r["actual_intent"], 0) + 1
            )

    return {
        "total_cases": total,
        "intent_accuracy": _rate(intent_pass_count, total),
        "action_accuracy": _rate(action_pass_count, total),
        "end_to_end_accuracy": _rate(all_pass_count, total),
        "rag_hit_rate": _rate(rag_hit_count, total),
        "safety_escalation_rate": _rate(safe, len(safety_cases)),
        "safety_cases": len(safety_cases),
        "category_accuracy": category_accuracy,
        "intent_confusion": confusion,
        "avg_elapsed_ms": round(mean(r["elapsed_ms"] for r in results), 2) if results else 0,
        "results": results,
    }


def print_report(report: dict) -> None:
    print("SupportPilot AI MVP Eval Report")
    print("=" * 36)
    print(f"Total cases: {report['total_cases']}")
    print(f"Intent accuracy: {report['intent_accuracy']:.1%}")
    print(f"Action accuracy: {report['action_accuracy']:.1%}")
    print(f"End-to-end accuracy: {report['end_to_end_accuracy']:.1%}")
    print(f"RAG hit rate: {report['rag_hit_rate']:.1%}")
    print(
        f"Safety escalation rate: {report['safety_escalation_rate']:.1%} "
        f"({report['safety_cases']} risky cases)"
    )
    print(f"Avg elapsed: {report['avg_elapsed_ms']} ms")
    print()

    print("Accuracy by category (end-to-end):")
    for cat, stats in report["category_accuracy"].items():
        print(f"  {cat:<14} {stats['passed']}/{stats['total']}  {stats['accuracy']:.1%}")
    print()

    if report["intent_confusion"]:
        print("Intent confusion (expected -> actual):")
        for expected, actuals in report["intent_confusion"].items():
            for actual, count in actuals.items():
                print(f"  {expected} -> {actual} x{count}")
        print()

    for item in report["results"]:
        status = "PASS" if item["intent_pass"] and item["action_pass"] else "FAIL"
        print(
            f"[{status}] {item['id']} ({item['category']}) | "
            f"intent {item['actual_intent']} / {item['expected_intent']} | "
            f"action {item['actual_action']} / {item['expected_action']} | "
            f"rag_hit={item['rag_hit']} | "
            f"{item['elapsed_ms']} ms"
        )

    print()
    print(f"Saved JSON report to: {REPORT_PATH}")


if __name__ == "__main__":
    print_report(run_eval())
