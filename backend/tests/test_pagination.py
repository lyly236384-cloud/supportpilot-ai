from fastapi.testclient import TestClient

from app.main import app


def test_traces_support_paginated_envelope():
    client = TestClient(app)
    response = client.get("/api/traces", params={"limit": 10, "offset": 0, "envelope": True})

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "total" in payload
    assert payload["limit"] == 10
    assert payload["offset"] == 0


def test_not_found_returns_error_envelope():
    client = TestClient(app)
    response = client.get("/api/traces/trace_does_not_exist_123")

    assert response.status_code == 404
    payload = response.json()
    assert payload["error"]["code"] == "http_404"
    assert "Trace not found" in payload["error"]["message"]


def test_metrics_rebuild_endpoint():
    client = TestClient(app)
    response = client.post("/api/metrics/rebuild")

    assert response.status_code == 200
    payload = response.json()
    assert "total_conversations" in payload
    assert "auto_reply_count" in payload
    assert "high_risk_count" in payload


def test_metrics_trends_endpoint():
    client = TestClient(app)
    response = client.get("/api/metrics/trends", params={"hours": 12})

    assert response.status_code == 200
    payload = response.json()
    assert payload["hours"] == 12
    assert payload["granularity"] == "hour"
    assert len(payload["points"]) == 12
    assert "bucket" in payload["points"][0]
    assert "auto_resolution_rate" in payload["points"][0]


def test_traces_export_returns_csv():
    client = TestClient(app)
    response = client.get("/api/traces/export", params={"limit": 10})

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "trace_id" in response.text
    assert "Content-Disposition" in response.headers


def test_traces_export_all_returns_csv():
    client = TestClient(app)
    response = client.get("/api/traces/export", params={"all": True})

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "trace_id" in response.text


def test_queue_supports_paginated_envelope():
    client = TestClient(app)
    response = client.get("/api/queue", params={"limit": 10, "offset": 0, "envelope": True})

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "total" in payload
    assert payload["limit"] == 10
    assert payload["offset"] == 0


def test_tickets_support_paginated_envelope():
    client = TestClient(app)
    response = client.get("/api/tickets", params={"limit": 10, "offset": 0, "envelope": True})

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload
    assert "total" in payload
    assert payload["limit"] == 10
    assert payload["offset"] == 0
