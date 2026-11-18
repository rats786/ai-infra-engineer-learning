"""Tests for configuration helpers."""

from pathlib import Path

import pytest

from src.config import Settings


def test_settings_defaults():
    settings = Settings()

    assert settings.app_name == "ML Model Serving API"
    assert settings.model_name == "resnet18"
    assert settings.environment == "development"
    assert settings.port == 8000
    assert settings.get_model_path() == Path("models") / "resnet18.pth"
    assert settings.get_device().type == "cpu"
    assert settings.is_development() is True
    assert settings.is_production() is False


def test_settings_validation_errors():
    with pytest.raises(ValueError):
        Settings(environment="invalid")

    with pytest.raises(ValueError):
        Settings(port=70000)

    with pytest.raises(ValueError):
        Settings(model_name="not-real")

    with pytest.raises(ValueError):
        Settings(model_name="mobilenet_v2")

    with pytest.raises(ValueError):
        Settings(device="cuda")

    with pytest.raises(ValueError):
        Settings(log_level="invalid")

    with pytest.raises(ValueError):
        Settings(confidence_threshold=1.5)


def test_settings_read_model_and_device_from_environment(monkeypatch):
    monkeypatch.setenv("MODEL_NAME", "resnet50")
    monkeypatch.setenv("DEVICE", "cpu")

    settings = Settings()

    assert settings.model_name == "resnet50"
    assert settings.device == "cpu"
