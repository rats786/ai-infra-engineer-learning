"""Model loading and inference for a simple image classifier."""

import io
import logging
import os
from typing import Any, Dict, List

import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

logger = logging.getLogger(__name__)


class ModelInference:
    """Wrapper for a small PyTorch image-classification model."""

    def __init__(self, model_name: str = "resnet18", device: str = "cpu"):
        normalized_name = (model_name or "").lower()
        supported = get_supported_models()
        if normalized_name not in supported:
            raise ValueError(f"Unsupported model: {model_name}. Supported: {supported}")

        self.model_name = normalized_name
        self.device = torch.device(device)
        self.model = None
        self.preprocess = self._create_transforms()
        self.classes = self._load_class_labels()

    def load_model(self) -> None:
        """Load the selected model and warm it up."""
        logger.info("Loading model %s on %s", self.model_name, self.device)

        if self.device.type == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but unavailable; falling back to CPU")
            self.device = torch.device("cpu")

        if self.model_name == "resnet18":
            self.model = models.resnet18(weights=None)
        elif self.model_name == "resnet50":
            self.model = models.resnet50(weights=None)
        else:
            raise ValueError(f"Unsupported model: {self.model_name}")

        self.model.to(self.device)
        self.model.eval()

        dummy_input = torch.randn(1, 3, 224, 224, device=self.device)
        with torch.no_grad():
            self.model(dummy_input)

        logger.info("Model %s loaded successfully", self.model_name)

    def _create_transforms(self) -> transforms.Compose:
        return transforms.Compose(
            [
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def _load_class_labels(self) -> List[str]:
        logger.info("Loading class labels")
        candidate_paths = [
            os.path.join(os.getcwd(), "imagenet_classes.txt"),
            os.path.join(os.path.dirname(__file__), "..", "imagenet_classes.txt"),
        ]
        for path in candidate_paths:
            try:
                normalized = os.path.abspath(path)
                if os.path.exists(normalized):
                    with open(normalized, "r", encoding="utf-8") as handle:
                        labels = [line.strip() for line in handle if line.strip()]
                    if labels:
                        return labels
            except OSError:
                pass

        return [f"class_{idx}" for idx in range(1000)]

    def preprocess_image(self, image_bytes: bytes) -> torch.Tensor:
        if not isinstance(image_bytes, (bytes, bytearray)):
            raise TypeError("image_bytes must be bytes-like")

        try:
            image = Image.open(io.BytesIO(image_bytes))
            image = image.convert("RGB")
        except Exception as exc:  # pragma: no cover - defensive code path
            raise ValueError(f"Invalid image data: {exc}") from exc

        tensor = self.preprocess(image)
        batch = tensor.unsqueeze(0).to(self.device)
        return batch

    def predict(self, image_bytes: bytes, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.model is None:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        if not 1 <= top_k <= 10:
            raise ValueError("top_k must be between 1 and 10")

        input_batch = self.preprocess_image(image_bytes)
        with torch.no_grad():
            logits = self.model(input_batch)

        probabilities = torch.nn.functional.softmax(logits[0], dim=0)
        top_k_actual = min(top_k, probabilities.numel())
        top_probs, top_indices = torch.topk(probabilities, k=top_k_actual)

        predictions: List[Dict[str, Any]] = []
        for probability, index in zip(top_probs, top_indices):
            class_id = int(index.item())
            class_name = self.classes[class_id] if class_id < len(self.classes) else f"class_{class_id}"
            predictions.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "confidence": float(probability.item()),
                }
            )
        return predictions

    def predict_from_url(self, image_url: str, top_k: int = 5) -> List[Dict[str, Any]]:
        import requests

        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return self.predict(response.content, top_k=top_k)

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "device": str(self.device),
            "loaded": self.model is not None,
            "input_size": (224, 224),
            "framework": "PyTorch",
            "version": torch.__version__,
            "num_classes": len(self.classes),
        }


def load_model(model_name: str = "resnet18", device: str = "cpu") -> ModelInference:
    inference = ModelInference(model_name=model_name, device=device)
    inference.load_model()
    return inference


def validate_image(image_bytes: bytes) -> bool:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()
        return True
    except Exception:
        return False


def get_supported_models() -> List[str]:
    return ["resnet18", "resnet50"]


def test_model_loading():
    model = ModelInference("resnet18", "cpu")
    model.load_model()
    assert model.model is not None
    assert not model.model.training
    assert len(model.classes) > 0


if __name__ == "__main__":
    test_model_loading()
    print("Model loading test passed")
