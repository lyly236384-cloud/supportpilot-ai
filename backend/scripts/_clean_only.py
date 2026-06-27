"""Delete all data files and re-init an empty database."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pathlib import Path
from app.config import SQLITE_PATH, TRACE_PATH, QUEUE_PATH, TICKETS_PATH, LOG_DIR

METRICS_PATH = LOG_DIR / "metrics_snapshot.json"
files = [SQLITE_PATH, TRACE_PATH, QUEUE_PATH, TICKETS_PATH, METRICS_PATH]
for p in files:
    if p.exists():
        p.unlink()
        print(f"Deleted: {p.name}")

from app.storage.repository import init_storage
init_storage()
print("Empty database created.")

from app.services.metrics_service import get_metrics
m = get_metrics()
print(f"Verify: total={m.total_conversations} auto={m.auto_reply_count} handoff={m.handoff_count} ticket={m.ticket_count}")
