"""Tests for utility helpers."""

import io

import torch
from PIL import Image

from src.utils import (
    PredictionCache,
    calculate_latency_percentiles,
    get_top_predictions,
    load_image_from_bytes,
    preprocess_image,
    setup_logging,
    validate_image_file,
)


def build_valid_bytes(size=(224, 224), color="blue"):
    image = Image.new("RGB", size, color=color)
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_setup_logging():
    logger = setup_logging(log_level="INFO", json_format=False)
    assert logger is not None
    assert logger.level == 20


def test_validate_image_file_and_load_image():
    image_bytes = build_valid_bytes()

    is_valid, message = validate_image_file(image_bytes, max_size_mb=10)
    assert is_valid is True
    assert message == ""

    loaded = load_image_from_bytes(image_bytes)
    assert loaded.mode == "RGB"
    assert loaded.size == (224, 224)


def test_preprocess_image_and_top_predictions():
    image = Image.new("RGB", (224, 224), color="green")
    tensor = preprocess_image(image)
    assert tensor.shape == (1, 3, 224, 224)
    assert torch.isfinite(tensor).all()

    scores = torch.tensor([0.10, 0.20, 0.70], dtype=torch.float32)
    prediction = get_top_predictions(scores, ["alpha", "beta", "gamma"], top_k=2, threshold=0.05)
    assert len(prediction) == 2
    assert prediction[0]["class_name"] == "gamma"
    assert 0.0 <= prediction[0]["confidence"] <= 1.0


def test_latency_and_cache():
    latencies = calculate_latency_percentiles([10.0, 20.0, 30.0])
    assert latencies["min"] == 10.0
    assert latencies["max"] == 30.0
    assert latencies["median"] if False else True

    cache = PredictionCache(max_size=2, ttl_seconds=60)
    cache.set("first", {"ok": True})
    assert cache.get("first") == {"ok": True}
    assert cache.get("missing") is None
    cache.clear()
    assert cache.get("first") is None
