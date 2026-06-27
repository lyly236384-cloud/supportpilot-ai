import shutil
from pathlib import Path

import pytest

_PROJECT_TMP = Path(__file__).resolve().parent.parent / ".pytest_tmp"

_PATH_TARGETS = (
    "app.config.paths",
    "app.config",
    "app.storage.json_store",
    "app.storage.sqlite_store",
    "app.services.ticket_service",
    "app.services.queue_service",
)


@pytest.fixture
def tmp_path(request) -> Path:
    """Project-local temp directory (avoids Windows system temp permission errors)."""
    _PROJECT_TMP.mkdir(exist_ok=True)
    path = _PROJECT_TMP / request.node.name
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    path.mkdir(parents=True)
    return path


@pytest.fixture(autouse=True)
def isolated_runtime_storage(monkeypatch, tmp_path):
    monkeypatch.setenv("STORAGE_BACKEND", "json")

    log_dir = tmp_path / "logs"
    storage_paths = {
        "TRACE_PATH": tmp_path / "traces.jsonl",
        "QUEUE_PATH": tmp_path / "queue.json",
        "TICKETS_PATH": tmp_path / "tickets.json",
        "LOG_DIR": log_dir,
        "STORAGE_DIR": tmp_path,
        "SQLITE_PATH": tmp_path / "supportpilot.db",
    }

    for module in _PATH_TARGETS:
        for name, value in storage_paths.items():
            monkeypatch.setattr(f"{module}.{name}", value, raising=False)

    metrics_snapshot = log_dir / "metrics_snapshot.json"
    monkeypatch.setattr("app.services.metrics_service.LOG_DIR", log_dir, raising=False)
    monkeypatch.setattr(
        "app.services.metrics_service.METRICS_SNAPSHOT_PATH",
        metrics_snapshot,
        raising=False,
    )

    log_dir.mkdir(parents=True, exist_ok=True)
    yield
