"""Tests for the model inference module."""

import io

import pytest
import torch
from PIL import Image

from src.model import ModelInference, get_supported_models


@pytest.fixture
def model_instance():
    return ModelInference(model_name="resnet18", device="cpu")


@pytest.fixture
def sample_image_bytes():
    image = Image.new("RGB", (224, 224), color="red")
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def test_model_init():
    model = ModelInference(model_name="resnet18", device="cpu")
    assert model.model is None
    assert model.model_name == "resnet18"
    assert model.weights is not None
    assert len(model.classes) == 1000
    assert str(model.device) == "cpu"


def test_model_init_invalid_name():
    with pytest.raises(ValueError):
        ModelInference(model_name="not_a_real_model", device="cpu")


def test_load_model(model_instance):
    model_instance.load_model()
    assert model_instance.model is not None
    assert model_instance.model.training is False
    assert next(model_instance.model.parameters()).device.type == "cpu"


def test_load_model_twice(model_instance):
    model_instance.load_model()
    model_instance.load_model()
    assert model_instance.model is not None
    assert not model_instance.model.training


def test_preprocess_image(model_instance, sample_image_bytes):
    tensor = model_instance.preprocess_image(sample_image_bytes)
    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape == (1, 3, 224, 224)
    assert torch.isfinite(tensor).all()


def test_predict_returns_top_k(model_instance, sample_image_bytes):
    model_instance.load_model()
    predictions = model_instance.predict(sample_image_bytes, top_k=3)
    assert len(predictions) == 3
    for pred in predictions:
        assert set(pred.keys()) == {"class_id", "class_name", "confidence"}
        assert 0 <= pred["confidence"] <= 1.0
        assert isinstance(pred["class_name"], str)


def test_supported_models():
    supported = get_supported_models()
    assert "resnet18" in supported
    assert "resnet50" in supported
