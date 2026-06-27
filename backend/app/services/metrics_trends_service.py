from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.models.schemas import MetricsTrendPoint, MetricsTrendResponse
from app.storage import repository


def get_metrics_trends(hours: int = 24) -> MetricsTrendResponse:
    window_hours = max(1, min(hours, 168))
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    bucket_keys = [
        (now - timedelta(hours=offset)).isoformat() for offset in range(window_hours - 1, -1, -1)
    ]
    stats = {key: {"total": 0, "auto_reply_count": 0} for key in bucket_keys}
    earliest = datetime.fromisoformat(bucket_keys[0].replace("Z", "+00:00"))

    for row in repository.read_trace_rows():
        created_at = row.get("created_at")
        if not created_at:
            continue

        dt = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(timezone.utc).replace(minute=0, second=0, microsecond=0)
        if dt < earliest:
            continue

        bucket = dt.isoformat()
        if bucket not in stats:
            continue

        stats[bucket]["total"] += 1
        if row.get("action") == "auto_reply":
            stats[bucket]["auto_reply_count"] += 1

    points = [
        MetricsTrendPoint(
            bucket=bucket,
            total=stats[bucket]["total"],
            auto_reply_count=stats[bucket]["auto_reply_count"],
            auto_resolution_rate=round(
                stats[bucket]["auto_reply_count"] / stats[bucket]["total"],
                3,
            )
            if stats[bucket]["total"]
            else 0,
        )
        for bucket in bucket_keys
    ]

    return MetricsTrendResponse(hours=window_hours, granularity="hour", points=points)
