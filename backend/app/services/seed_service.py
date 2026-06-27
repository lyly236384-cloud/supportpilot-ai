from __future__ import annotations

from app.storage import repository
from app.workflow.orchestrator import run_support_workflow

DEMO_SEED_MESSAGES: list[tuple[str, str]] = [
    ("shop_001", "我的快递什么时候发货？"),
    ("shop_002", "订单已经发货了，还能修改收货地址吗？"),
    ("shop_003", "我想退货，七天无理由怎么申请？"),
    ("shop_001", "收到的杯子碎了，外包装也变形了"),
    ("shop_003", "我要投诉你们并要求赔偿"),
    ("shop_004", "我的发票抬头写错了怎么办？"),
    ("shop_005", "物流显示签收了但我没收到货"),
    ("shop_002", "想换一个颜色，怎么操作？"),
]


def seed_demo_data(*, force: bool = False) -> dict:
    """Run demo workflow scenarios to populate traces / metrics / queue / tickets.

    Idempotent by default: skips if traces already exist, unless ``force=True``.
    """
    existing = repository.read_trace_rows()
    if not force and len(existing) > 0:
        return {
            "status": "skipped",
            "reason": f"已有 {len(existing)} 条 trace，跳过种子数据。使用 force=true 强制重新生成。",
            "count": 0,
        }

    results: list[dict] = []
    for customer_id, message in DEMO_SEED_MESSAGES:
        response = run_support_workflow(customer_id, message)
        results.append({
            "trace_id": response.trace_id,
            "action": response.action.value,
            "customer_id": response.customer_id,
        })

    return {
        "status": "ok",
        "count": len(results),
        "results": results,
    }
