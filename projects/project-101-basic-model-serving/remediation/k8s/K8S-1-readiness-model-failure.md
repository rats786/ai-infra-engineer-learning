# K8S-1: Make readiness fail when the model is unavailable

**Status:** Open

## Why this matters

The API `/health` endpoint currently returns HTTP 200 even when the JSON payload reports `"unhealthy"`. In Kubernetes, a container can be marked Ready when a probe succeeds, even if the model is not actually usable. That means traffic can be routed to a pod that cannot perform inference.

## Root cause

The application is reporting a health status in the payload, but the HTTP response code is not aligned with that state. A readiness probe that checks only `200 OK` cannot distinguish a usable model from a broken one.

## Recommended fix

1. Keep the model initialization logic separate from the request path.
2. Report a real failure state from `/health` when the model is not loaded or has failed to initialize.
3. Return a non-2xx status code for readiness when the app is not ready to serve traffic.
4. Use the readiness probe to gate Service traffic while keeping liveness focused on process health.

Example approach:

```python
@app.get("/health")
def health():
    if not model_is_ready:
        return JSONResponse(status_code=503, content={"status": "unhealthy"})
    return {"status": "healthy", "model_loaded": True}
```

## Acceptance criteria

- A model startup failure leaves the pod in `NotReady`.
- The Service does not send traffic to the failing pod.
- Once the model loads successfully, the pod transitions to `Ready`.
- A probe check is observable from `kubectl describe pod` and `kubectl get endpoints`.

See the [tracker](tracker.md) for the full deployment sequence and remaining Kubernetes issues.
