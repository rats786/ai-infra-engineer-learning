"""FastAPI application for serving a small image-classification model."""

import logging
import time
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import Response
from pydantic import BaseModel, Field
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from src.model import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Model Serving API",
    description="REST API for serving image classification models",
    version="1.0.0",
)

app.state.model = None
app.state.start_time = time.time()

HTTP_REQUESTS = Counter(
    "http_requests_total",
    "Total number of completed HTTP requests",
    ["method", "route", "status_code"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "Duration of completed HTTP requests in seconds",
    ["method", "route"],
)
PREDICTIONS = Counter(
    "predictions_total",
    "Total number of inference attempts by outcome",
    ["status"],
)
PREDICTION_DURATION = Histogram(
    "prediction_duration_seconds",
    "Duration of model inference in seconds",
)


class PredictionRequest(BaseModel):
    image_url: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=10)
    threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class Prediction(BaseModel):
    class_id: int
    class_name: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class PredictionResponse(BaseModel):
    predictions: List[Prediction]
    inference_time_ms: float
    model_version: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    version: str
    uptime_seconds: float


@app.on_event("startup")
async def startup_event():
    logger.info("Starting ML Model Serving API...")
    try:
        app.state.model = load_model("resnet18", "cpu")
        app.state.start_time = time.time()
        logger.info("Model loaded successfully")
    except Exception as exc:  # pragma: no cover - startup guard
        logger.warning("Model could not be loaded at startup: %s", exc)
        app.state.model = None


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down ML Model Serving API...")
    app.state.model = None


@app.middleware("http")
async def track_requests(request: Request, call_next):
    start_time = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - start_time
        if request.url.path != "/metrics":
            route = request.scope.get("route")
            route_path = getattr(route, "path", "unmatched")
            HTTP_REQUESTS.labels(request.method, route_path, str(status_code)).inc()
            HTTP_REQUEST_DURATION.labels(request.method, route_path).observe(duration)
        logger.info("%s %s - %s - %.3fs", request.method, request.url.path, status_code, duration)


@app.get("/")
async def root():
    return {"message": "ML Model Serving API", "status": "running", "docs": "/docs"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    if app.state.model is None:
        raise HTTPException(status_code=503, detail="Model is not loaded")

    return HealthResponse(
        status="healthy",
        model_loaded=True,
        version="1.0.0",
        uptime_seconds=time.time() - app.state.start_time,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict(file: UploadFile = File(...), top_k: int = 5):
    if app.state.model is None:
        try:
            app.state.model = load_model("resnet18", "cpu")
        except Exception as exc:  # pragma: no cover - startup fallback
            raise HTTPException(status_code=503, detail="Model is not loaded") from exc

    if top_k < 1 or top_k > 10:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 10")
    if file is None:
        raise HTTPException(status_code=422, detail="Image file is required")

    content_type = file.content_type or ""
    if "image" not in content_type:
        raise HTTPException(status_code=400, detail="Invalid image content type")

    try:
        image_bytes = await file.read()
        start_timer = time.perf_counter()
        try:
            predictions = app.state.model.predict(image_bytes, top_k=top_k)
        except ValueError:
            PREDICTIONS.labels(status="error").inc()
            raise
        except Exception:
            PREDICTIONS.labels(status="error").inc()
            raise
        else:
            PREDICTIONS.labels(status="success").inc()
        finally:
            inference_duration_seconds = time.perf_counter() - start_timer
            PREDICTION_DURATION.observe(inference_duration_seconds)
        inference_time_ms = inference_duration_seconds * 1000
        return PredictionResponse(
            predictions=predictions,
            inference_time_ms=float(inference_time_ms),
            model_version="1.0.0",
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(status_code=500, detail="Inference failed") from exc


@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


def preprocess_image(image_bytes: bytes):
    return load_model("resnet18", "cpu").preprocess_image(image_bytes)
