from __future__ import annotations

from pathlib import Path

APP_DIR = Path(__file__).resolve().parents[1]
BACKEND_ROOT = APP_DIR.parent

DATA_DIR = BACKEND_ROOT / "data"
KB_DIR = DATA_DIR / "kb"
MOCK_DATA_DIR = DATA_DIR / "mock"

STORAGE_DIR = BACKEND_ROOT / "storage"
LOG_DIR = STORAGE_DIR / "logs"
SQLITE_PATH = STORAGE_DIR / "supportpilot.db"
TRACE_PATH = LOG_DIR / "traces.jsonl"
QUEUE_PATH = STORAGE_DIR / "queue.json"
TICKETS_PATH = STORAGE_DIR / "tickets.json"
