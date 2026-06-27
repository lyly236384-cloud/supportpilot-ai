"""Clean all storage data, then run a single feishu-enabled test to leave exactly 1 trace."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from app.config import SQLITE_PATH, TRACE_PATH, QUEUE_PATH, TICKETS_PATH, LOG_DIR

# 1. Delete all data files
METRICS_PATH = LOG_DIR / "metrics_snapshot.json"
for p in [SQLITE_PATH, TRACE_PATH, QUEUE_PATH, TICKETS_PATH, METRICS_PATH]:
    if p.exists():
        p.unlink()
        print(f"Deleted: {p.name}")

# 2. Re-init storage (creates fresh SQLite tables)
from app.storage.repository import init_storage
init_storage()
print("Storage re-initialized")

# 3. Run the feishu test case (product_damage → creates ticket + sends feishu notification)
from app.workflow.orchestrator import run_support_workflow
response = run_support_workflow("shop_001", "收到的杯子碎了，外包装也变形了")
print(f"\n✅ Single trace created:")
print(f"  Trace: {response.trace_id}")
print(f"  Action: {response.action.value}")
if response.ticket:
    print(f"  Ticket: {response.ticket.ticket_id}")
print(f"  Notification: {response.notification}")

# 4. Verify
from app.services.metrics_service import get_metrics
m = get_metrics()
print(f"\n📊 Metrics now: total={m.total_conversations} auto={m.auto_reply_count} handoff={m.handoff_count} ticket={m.ticket_count}")
