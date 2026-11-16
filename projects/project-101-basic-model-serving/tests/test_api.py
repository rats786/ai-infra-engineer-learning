"""Tests for the FastAPI application."""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from prometheus_client.parser import text_string_to_metric_families

from src.api import app


def metric_value(metrics_text, metric_name, labels):
    for family in text_string_to_metric_families(metrics_text):
        for sample in family.samples:
            if sample.name == metric_name and sample.labels == labels:
                return sample.value
    return 0


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_image():
    image = Image.new("RGB", (224, 224), color="blue")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def invalid_image():
    return b"not an image"


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "running"
    assert "message" in payload


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] in {"healthy", "unhealthy"}
    assert "model_loaded" in payload


def test_metrics_endpoint_returns_prometheus_exposition(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain; version=0.0.4")
    assert "python_gc_objects_collected_total" in response.text
    assert "app_uptime_seconds 1" not in response.text


def test_request_metrics_track_route_and_ignore_scrapes(client):
    labels = {"method": "GET", "route": "/", "status_code": "200"}
    before = client.get("/metrics").text
    before_count = metric_value(before, "http_requests_total", labels)
    before_duration_count = metric_value(
        before, "http_request_duration_seconds_count", {"method": "GET", "route": "/"}
    )

    response = client.get("/")
    after = client.get("/metrics").text

    assert response.status_code == 200
    assert metric_value(after, "http_requests_total", labels) == before_count + 1
    assert metric_value(
        after, "http_request_duration_seconds_count", {"method": "GET", "route": "/"}
    ) == before_duration_count + 1
    assert metric_value(
        after,
        "http_requests_total",
        {"method": "GET", "route": "/metrics", "status_code": "200"},
    ) == 0


def test_prediction_metrics_track_success_and_failure(client, sample_image, monkeypatch):
    class StubModel:
        def __init__(self, fail=False):
            self.fail = fail

        def predict(self, image_bytes, top_k):
            if self.fail:
                raise ValueError("Invalid image")
            return [{"class_id": 1, "class_name": "sample", "confidence": 0.9}]

    before = client.get("/metrics").text
    before_success = metric_value(before, "predictions_total", {"status": "success"})
    before_error = metric_value(before, "predictions_total", {"status": "error"})
    before_duration_count = metric_value(before, "prediction_duration_seconds_count", {})

    monkeypatch.setattr(app.state, "model", StubModel())
    success = client.post(
        "/predict",
        files={"file": ("sample.jpg", sample_image, "image/jpeg")},
    )
    monkeypatch.setattr(app.state, "model", StubModel(fail=True))
    failure = client.post(
        "/predict",
        files={"file": ("sample.jpg", sample_image, "image/jpeg")},
    )
    after = client.get("/metrics").text

    assert success.status_code == 200
    assert failure.status_code == 400
    assert metric_value(after, "predictions_total", {"status": "success"}) == before_success + 1
    assert metric_value(after, "predictions_total", {"status": "error"}) == before_error + 1
    assert metric_value(after, "prediction_duration_seconds_count", {}) == before_duration_count + 2


def test_predict_with_valid_image(client, sample_image):
    response = client.post(
        "/predict",
        files={"file": ("sample.jpg", sample_image, "image/jpeg")},
    )
    assert response.status_code == 200
    payload = response.json()
    assert "predictions" in payload
    assert len(payload["predictions"]) > 0
    for pred in payload["predictions"]:
        assert "class_name" in pred
        assert "confidence" in pred
        assert 0.0 <= pred["confidence"] <= 1.0


def test_predict_with_invalid_image(client, invalid_image):
    response = client.post(
        "/predict",
        files={"file": ("bad.txt", invalid_image, "text/plain")},
    )
    assert response.status_code in {400, 422}


def test_grafana_dashboard_is_provisioned_and_queries_metrics():
    dashboard_path = (
        Path(__file__).resolve().parents[1] / "monitoring" / "grafana" / "dashboards" / "ml-api-overview.json"
    )

    assert dashboard_path.exists()

    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    assert dashboard.get("uid") == "ml-api-overview"
    panel_expressions = {
        panel["title"]: target["expr"]
        for panel in dashboard.get("panels", [])
        for target in panel.get("targets", [])
    }

    assert "API availability" in panel_expressions
    assert panel_expressions["API availability"] == 'up{job="ml-api"}'
    assert panel_expressions["Request rate"] == "sum(rate(http_requests_total[5m]))"
    assert panel_expressions["5xx error rate"] == 'sum(rate(http_requests_total{status_code=~"5.."}[5m]))'
    assert panel_expressions["p95 request duration"] == (
        "histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))"
    )
    assert panel_expressions["p95 inference duration"] == (
        "histogram_quantile(0.95, sum by (le) (rate(prediction_duration_seconds_bucket[5m])))"
    )
