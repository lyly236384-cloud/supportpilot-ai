from __future__ import annotations

import csv
import io

from app.storage import repository

_EXPORT_PAGE_SIZE = 500


def build_traces_csv(*, limit: int | None = None, export_all: bool = False) -> str:
    rows = _collect_trace_rows(limit=limit, export_all=export_all)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        [
            "trace_id",
            "customer_id",
            "message",
            "intent",
            "risk_level",
            "action",
            "elapsed_ms",
            "estimated_tokens",
            "answer",
            "created_at",
        ]
    )

    for row in rows:
        writer.writerow(
            [
                row.get("trace_id", ""),
                row.get("customer_id", ""),
                _csv_cell(row.get("message", "")),
                (row.get("intent") or {}).get("intent", ""),
                (row.get("risk") or {}).get("risk_level", ""),
                row.get("action", ""),
                row.get("elapsed_ms", ""),
                row.get("estimated_tokens", ""),
                _csv_cell(row.get("answer", "")),
                row.get("created_at", ""),
            ]
        )

    return buffer.getvalue()


def _collect_trace_rows(*, limit: int | None, export_all: bool) -> list[dict]:
    if export_all:
        return _paginate_all_trace_rows()

    effective_limit = limit if limit is not None else 2000
    rows, _ = repository.list_trace_rows(limit=effective_limit, offset=0)
    return rows


def _paginate_all_trace_rows() -> list[dict]:
    rows: list[dict] = []
    offset = 0

    while True:
        page, total = repository.list_trace_rows(limit=_EXPORT_PAGE_SIZE, offset=offset)
        if not page:
            break
        rows.extend(page)
        offset += len(page)
        if offset >= total:
            break

    return rows


def _csv_cell(value: str) -> str:
    return str(value).replace("\r\n", " ").replace("\n", " ").strip()
