"""Application configuration and validation helpers."""

import os
from pathlib import Path
from typing import List, Optional

from pydantic_settings import BaseSettings
import torch
from pydantic import Field, validator


class Settings(BaseSettings):
    app_name: str = Field(default="ML Model Serving API", description="Application name")
    app_version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment")

    host: str = Field(default="0.0.0.0", description="Server host address")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=1, description="Number of worker processes")
    reload: bool = Field(default=False, description="Auto-reload on code changes")

    model_name: str = Field(default="resnet18", description="Model name to load")
    model_path: Optional[str] = Field(default=None, description="Optional path to a local model")
    device: str = Field(default="cpu", description="Device to use")
    batch_size: int = Field(default=1, description="Batch size for inference")
    warmup_iterations: int = Field(default=10, description="Warmup iterations")

    max_image_size_mb: int = Field(default=10, description="Max image size in MB")
    allowed_image_types: List[str] = Field(default=["image/jpeg", "image/png", "image/jpg"])
    default_top_k: int = Field(default=5, description="Default top-k predictions")
    confidence_threshold: float = Field(default=0.0, ge=0.0, le=1.0)

    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format")

    enable_cache: bool = Field(default=False, description="Enable prediction caching")
    cache_size: int = Field(default=1000, description="Cache size")
    cache_ttl_seconds: int = Field(default=300, description="Cache TTL in seconds")

    enable_rate_limit: bool = Field(default=False, description="Enable rate limiting")
    rate_limit_requests: int = Field(default=100, description="Rate limit request cap")
    rate_limit_window_seconds: int = Field(default=60, description="Rate limit window")

    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: List[str] = Field(default=["*"], description="Allowed CORS origins")
    health_check_interval_seconds: int = Field(default=30, description="Health check interval")

    @validator("environment")
    def validate_environment(cls, value):
        allowed = ["development", "staging", "production"]
        normalized = str(value).lower()
        if normalized not in allowed:
            raise ValueError(f"Environment must be one of: {allowed}")
        return normalized

    @validator("port")
    def validate_port(cls, value):
        if not 1 <= int(value) <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        return int(value)

    @validator("model_name")
    def validate_model_name(cls, value):
        supported = ["resnet18", "resnet50"]
        normalized = str(value).lower()
        if normalized not in supported:
            raise ValueError(f"Model must be one of: {supported}")
        return normalized

    @validator("device")
    def validate_device(cls, value):
        device = str(value).lower()
        if device == "cpu":
            return device
        if device == "cuda":
            device_index = 0
        elif device.startswith("cuda:") and device[5:].isdigit():
            device_index = int(device[5:])
        else:
            raise ValueError(
                "Device must be 'cpu', 'cuda', or an available CUDA device "
                "(e.g. 'cuda:0')"
            )

        if not torch.cuda.is_available():
            raise ValueError("CUDA device specified but CUDA not available")
        if device_index >= torch.cuda.device_count():
            raise ValueError(f"CUDA device index {device_index} is not available")
        return device

    @validator("log_level")
    def validate_log_level(cls, value):
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        normalized = str(value).upper()
        if normalized not in allowed:
            raise ValueError(f"Log level must be one of: {allowed}")
        return normalized

    @validator("confidence_threshold")
    def validate_confidence_threshold(cls, value):
        value = float(value)
        if not 0.0 <= value <= 1.0:
            raise ValueError("Confidence threshold must be between 0.0 and 1.0")
        return value

    def is_production(self) -> bool:
        return self.environment == "production"

    def is_development(self) -> bool:
        return self.environment == "development"

    def get_device(self):
        import torch

        return torch.device(self.device)

    def get_model_path(self) -> Path:
        if self.model_path:
            return Path(self.model_path)
        return Path("models") / f"{self.model_name}.pth"

    def to_dict(self) -> dict:
        return self.dict()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def load_settings() -> Settings:
    return Settings()


_settings_cache: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings_cache
    if _settings_cache is None:
        _settings_cache = Settings()
    return _settings_cache


__all__ = ["Settings", "load_settings", "get_settings"]
