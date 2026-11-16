# MON-1: Return Valid Prometheus Metrics

**Status:** Guide written; implementation not started.

## Why this matters

Prometheus expects `/metrics` to use a recognized text exposition format. The current endpoint in [`src/api.py`](../../src/api.py) hand-writes one sample and labels the response `version=0.7.0`. Prometheus' classic text format is version `0.0.4`; the `prometheus-client` package already listed in `requirements.txt` generates the correct body and content type.

A successful HTTP response alone is not enough: Prometheus must also parse the response. A format problem typically appears as a scrape error and makes the target **DOWN**.

## Suggested implementation

1. Import `CONTENT_TYPE_LATEST` and `generate_latest` from `prometheus_client`.
2. Replace the hard-coded string in `/metrics` with a `Response` whose content is `generate_latest()` and whose media type is `CONTENT_TYPE_LATEST`.
3. Remove the fake `app_uptime_seconds 1` sample. Live application metrics will be added in MON-2.
4. Add an API test that checks status `200`, the content type starts with `text/plain; version=0.0.4`, and the body contains a known metric emitted by the Prometheus client registry. Do not assert an exact full body because runtime/client metrics can vary by Python version.

Example endpoint shape:

```python
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## Verify

Run the focused endpoint test, then start the stack and inspect `http://localhost:9090/targets`. The `ml-api` target should become **UP** after Prometheus scrapes it. Also inspect `http://localhost:8000/metrics` and confirm it is no longer the constant placeholder.

See the [tracker](tracker.md) for the full sequence and local workflow.
