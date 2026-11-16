"""Utility functions for ML model serving."""

import io
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import torch
from PIL import Image


def setup_logging(log_level: str = "INFO", json_format: bool = True) -> logging.Logger:
    logger = logging.getLogger("ml-serving")
    logger.setLevel(getattr(logging, str(log_level).upper(), logging.INFO))
    logger.handlers.clear()

    handler = logging.StreamHandler()
    if json_format:
        class JSONFormatter(logging.Formatter):
            def format(self, record):
                payload = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "level": record.levelname,
                    "message": record.getMessage(),
                    "module": record.module,
                }
                return json.dumps(payload)

        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

    logger.addHandler(handler)
    logger.propagate = False
    return logger


def validate_image_file(file_content: bytes, max_size_mb: int = 10) -> Tuple[bool, str]:
    if len(file_content) == 0:
        return False, "Image file is empty"
    max_bytes = max_size_mb * 1024 * 1024
    if len(file_content) > max_bytes:
        return False, "Image file exceeds maximum allowed size"

    try:
        image = Image.open(io.BytesIO(file_content))
        image.verify()
        if image.format not in {"JPEG", "PNG", "JPG"}:
            return False, "Unsupported image format"
        image = Image.open(io.BytesIO(file_content))
        width, height = image.size
        if width > 4096 or height > 4096:
            return False, "Image dimensions are too large"
    except Exception:
        return False, "Invalid or corrupted image file"

    return True, ""


def load_image_from_bytes(image_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        return image.convert("RGB")
    except Exception as exc:  # pragma: no cover - defensive path
        raise ValueError(f"Invalid image data: {exc}") from exc


def resize_image(image: Image.Image, size: Tuple[int, int] = (224, 224)) -> Image.Image:
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image.resize(size)


def preprocess_image(
    image: Image.Image,
    mean: List[float] = [0.485, 0.456, 0.406],
    std: List[float] = [0.229, 0.224, 0.225],
) -> torch.Tensor:
    rgb = image.convert("RGB")
    array = np.asarray(rgb, dtype=np.float32) / 255.0
    tensor = torch.tensor(array, dtype=torch.float32).permute(2, 0, 1)
    mean_t = torch.tensor(mean, dtype=torch.float32).view(3, 1, 1)
    std_t = torch.tensor(std, dtype=torch.float32).view(3, 1, 1)
    tensor = (tensor - mean_t) / std_t
    return tensor.unsqueeze(0)


def get_model_path(model_name: str, models_dir: str = "models") -> Path:
    return Path(models_dir) / f"{model_name}.pth"


def load_class_labels(labels_file: str = "imagenet_classes.txt") -> List[str]:
    path = Path(labels_file)
    if path.exists():
        with path.open("r", encoding="utf-8") as handle:
            return [line.strip() for line in handle if line.strip()]
    return [f"class_{idx}" for idx in range(1000)]


def warm_up_model(model: torch.nn.Module, device: torch.device, num_iterations: int = 10):
    dummy_input = torch.randn(1, 3, 224, 224, device=device)
    with torch.no_grad():
        for _ in range(num_iterations):
            model(dummy_input)


def get_top_predictions(
    probabilities: torch.Tensor,
    class_labels: List[str],
    top_k: int = 5,
    threshold: float = 0.0,
) -> List[dict]:
    if probabilities.ndim > 1:
        probabilities = probabilities.flatten()
    probs = torch.nn.functional.softmax(probabilities, dim=0)
    top_probs, top_indices = torch.topk(probs, k=min(top_k, probs.numel()))

    results: List[dict] = []
    for prob, index in zip(top_probs, top_indices):
        confidence = float(prob.item())
        if confidence >= threshold:
            class_id = int(index.item())
            results.append({
                "class_id": class_id,
                "class_name": class_labels[class_id] if class_id < len(class_labels) else f"class_{class_id}",
                "confidence": confidence,
            })
    return results


def calculate_latency_percentiles(latencies: List[float]) -> Dict[str, float]:
    values = np.array(latencies, dtype=float)
    if values.size == 0:
        return {"min": 0.0, "max": 0.0, "mean": 0.0, "p50": 0.0, "p95": 0.0, "p99": 0.0}
    return {
        "min": float(np.min(values)),
        "max": float(np.max(values)),
        "mean": float(np.mean(values)),
        "p50": float(np.percentile(values, 50)),
        "p95": float(np.percentile(values, 95)),
        "p99": float(np.percentile(values, 99)),
    }


def log_prediction(logger: logging.Logger, image_name: str, prediction: Dict, latency_ms: float, status: str = "success"):
    logger.info(
        "Prediction completed",
        extra={
            "image": image_name,
            "prediction": prediction,
            "latency_ms": latency_ms,
            "status": status,
        },
    )


def handle_inference_error(error: Exception, logger: logging.Logger) -> Dict[str, str]:
    logger.exception("Inference error: %s", error)
    if isinstance(error, ValueError):
        error_name = "validation_error"
        message = str(error)
    elif isinstance(error, RuntimeError):
        error_name = "runtime_error"
        message = "Model execution failed"
    elif isinstance(error, MemoryError):
        error_name = "memory_error"
        message = "Model inference ran out of memory"
    else:
        error_name = "internal_error"
        message = "Unexpected inference failure"
    return {"error": error_name, "message": message, "details": str(error)}


class PredictionCache:
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._data = {}

    def get(self, key):
        if key not in self._data:
            return None
        value, timestamp = self._data[key]
        if (datetime.utcnow() - timestamp).total_seconds() > self.ttl_seconds:
            del self._data[key]
            return None
        return value

    def set(self, key, value):
        self._data[key] = (value, datetime.utcnow())
        if len(self._data) > self.max_size:
            oldest_key = next(iter(self._data))
            del self._data[oldest_key]

    def clear(self):
        self._data.clear()
