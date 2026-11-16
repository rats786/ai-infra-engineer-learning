"""Tests for the FastAPI application."""

import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from src.api import app


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
