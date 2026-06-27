from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import contextmanager

from app.config import SQLITE_PATH, STORAGE_DIR
from app.models.schemas import QueueRecord, TicketRecord
from app.storage import json_store

_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id TEXT NOT NULL UNIQUE,
    payload_json TEXT NOT NULL,
    created_at TEXT
);
CREATE TABLE IF NOT EXISTS queue_records (
    trace_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS ticket_records (
    ticket_id TEXT PRIMARY KEY,
    payload_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""


def init_db() -> None:
    with _lock:
        STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        with _connect() as conn:
            conn.executescript(_SCHEMA)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_traces_created_at ON traces(created_at)"
            )
            conn.commit()


def migrate_from_legacy_files() -> None:
    with _lock:
        with _connect() as conn:
            if _meta_value(conn, "legacy_migrated") == "true":
                return

            if not json_store.legacy_files_exist() and conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0] == 0:
                conn.execute(
                    "INSERT OR REPLACE INTO meta(key, value) VALUES ('legacy_migrated', 'true')"
                )
                conn.commit()
                return

            for row in json_store.read_trace_rows():
                _upsert_trace(conn, row)

            for record in json_store.read_queue_store().values():
                _upsert_queue(conn, record)

            for record in json_store.read_ticket_store().values():
                _upsert_ticket(conn, record)

            conn.execute(
                "INSERT OR REPLACE INTO meta(key, value) VALUES ('legacy_migrated', 'true')"
            )
            conn.commit()


def append_trace_row(row: dict) -> None:
    with _lock:
        with _connect() as conn:
            _upsert_trace(conn, row)
            conn.commit()


def read_trace_rows() -> list[dict]:
    with _lock:
        with _connect() as conn:
            cursor = conn.execute("SELECT payload_json FROM traces ORDER BY id ASC")
            return [json.loads(row[0]) for row in cursor.fetchall()]


def list_trace_rows(limit: int, offset: int) -> tuple[list[dict], int]:
    with _lock:
        with _connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM traces").fetchone()[0]
            cursor = conn.execute(
                """
                SELECT payload_json
                FROM traces
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            )
            rows = [json.loads(item[0]) for item in cursor.fetchall()]
            rows.reverse()
            return rows, total


def get_trace_row(trace_id: str) -> dict | None:
    with _lock:
        with _connect() as conn:
            row = conn.execute(
                "SELECT payload_json FROM traces WHERE trace_id = ?",
                (trace_id,),
            ).fetchone()
            if row is None:
                return None
            return json.loads(row[0])


def read_queue_store() -> dict[str, QueueRecord]:
    with _lock:
        with _connect() as conn:
            cursor = conn.execute("SELECT payload_json FROM queue_records")
            return {
                QueueRecord(**json.loads(row[0])).trace_id: QueueRecord(**json.loads(row[0]))
                for row in cursor.fetchall()
            }


def write_queue_store(records: dict[str, QueueRecord]) -> None:
    with _lock:
        with _connect() as conn:
            conn.execute("DELETE FROM queue_records")
            for record in records.values():
                _upsert_queue(conn, record)
            conn.commit()


def read_ticket_store() -> dict[str, TicketRecord]:
    with _lock:
        with _connect() as conn:
            cursor = conn.execute("SELECT payload_json FROM ticket_records")
            return {
                TicketRecord(**json.loads(row[0])).ticket_id: TicketRecord(**json.loads(row[0]))
                for row in cursor.fetchall()
            }


def write_ticket_store(records: dict[str, TicketRecord]) -> None:
    with _lock:
        with _connect() as conn:
            conn.execute("DELETE FROM ticket_records")
            for record in records.values():
                _upsert_ticket(conn, record)
            conn.commit()


def aggregate_trace_metrics() -> dict[str, int]:
    with _lock:
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(*) AS total_conversations,
                    SUM(CASE WHEN json_extract(payload_json, '$.action') = 'auto_reply' THEN 1 ELSE 0 END)
                        AS auto_reply_count,
                    SUM(CASE WHEN json_extract(payload_json, '$.action') = 'handoff' THEN 1 ELSE 0 END)
                        AS handoff_count,
                    SUM(CASE WHEN json_extract(payload_json, '$.action') = 'create_ticket' THEN 1 ELSE 0 END)
                        AS ticket_count,
                    COALESCE(SUM(CAST(json_extract(payload_json, '$.elapsed_ms') AS INTEGER)), 0)
                        AS total_elapsed_ms,
                    COALESCE(SUM(CAST(json_extract(payload_json, '$.estimated_tokens') AS INTEGER)), 0)
                        AS total_estimated_tokens,
                    SUM(
                        CASE
                            WHEN json_extract(payload_json, '$.risk.risk_level') = 'high' THEN 1
                            ELSE 0
                        END
                    ) AS high_risk_count
                FROM traces
                """
            ).fetchone()

    return {
        "total_conversations": int(row[0] or 0),
        "auto_reply_count": int(row[1] or 0),
        "handoff_count": int(row[2] or 0),
        "ticket_count": int(row[3] or 0),
        "total_elapsed_ms": int(row[4] or 0),
        "total_estimated_tokens": int(row[5] or 0),
        "high_risk_count": int(row[6] or 0),
    }


def count_high_risk_traces() -> int:
    with _lock:
        with _connect() as conn:
            row = conn.execute(
                """
                SELECT COUNT(*)
                FROM traces
                WHERE json_extract(payload_json, '$.risk.risk_level') = 'high'
                """
            ).fetchone()
    return int(row[0] or 0)


@contextmanager
def _connect():
    conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
    try:
        yield conn
    finally:
        conn.close()


def _meta_value(conn: sqlite3.Connection, key: str) -> str | None:
    row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def _upsert_trace(conn: sqlite3.Connection, row: dict) -> None:
    trace_id = row["trace_id"]
    created_at = row.get("created_at")
    conn.execute(
        """
        INSERT INTO traces(trace_id, payload_json, created_at)
        VALUES (?, ?, ?)
        ON CONFLICT(trace_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            created_at = excluded.created_at
        """,
        (trace_id, json.dumps(row, ensure_ascii=False), created_at),
    )


def _upsert_queue(conn: sqlite3.Connection, record: QueueRecord) -> None:
    payload = record.model_dump(mode="json")
    conn.execute(
        """
        INSERT INTO queue_records(trace_id, payload_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(trace_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            updated_at = excluded.updated_at
        """,
        (record.trace_id, json.dumps(payload, ensure_ascii=False), record.updated_at),
    )


def _upsert_ticket(conn: sqlite3.Connection, record: TicketRecord) -> None:
    payload = record.model_dump(mode="json")
    conn.execute(
        """
        INSERT INTO ticket_records(ticket_id, payload_json, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(ticket_id) DO UPDATE SET
            payload_json = excluded.payload_json,
            updated_at = excluded.updated_at
        """,
        (record.ticket_id, json.dumps(payload, ensure_ascii=False), record.updated_at),
    )
