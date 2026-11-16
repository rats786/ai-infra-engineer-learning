# MON-2: Instrument API Requests and Predictions

**Status:** Implemented; pending user review.

## Implemented change

[`src/api.py`](../../src/api.py) now exports `http_requests_total` by method, route template, and status code; `http_request_duration_seconds` by method and route; `predictions_total` by fixed success/error status; and `prediction_duration_seconds` for model execution. The middleware excludes `/metrics` to avoid counting scrape traffic. Prediction duration uses a monotonic timer and is recorded for successful and failed model calls.

Focused tests compare registry samples before and after requests, including prediction success and failure, rather than assuming counters start at zero.

## What to measure

Add counters and histograms with the Prometheus client. Counters answer “how many?”; histograms record durations so Prometheus can calculate rates and latency percentiles.

| Metric | Type | Suggested labels | Meaning |
| --- | --- | --- | --- |
| `http_requests_total` | Counter | `method`, `route`, `status_code` | Completed API requests |
| `http_request_duration_seconds` | Histogram | `method`, `route` | End-to-end request duration |
| `predictions_total` | Counter | `status` (`success` or `error`) | Prediction attempts and outcomes |
| `prediction_duration_seconds` | Histogram | none, or a small fixed `model` label | Time spent running inference |

Use seconds for duration metrics. The Prometheus client’s Histogram has useful default buckets; tune them only if measurements show the defaults do not fit inference times.

## Implementation guidance

1. Define metrics once at module scope so all requests update the same collectors. Keep using the default registry with `generate_latest()` from MON-1, unless the application needs a separate registry for isolation.
2. In the existing HTTP middleware in [`src/api.py`](../../src/api.py), measure elapsed time with `time.perf_counter()` and record the request counter and duration after the response is available.
3. Use the matched FastAPI route template (for example `/predict`), not the raw URL path. For unmatched routes, use a fixed value such as `unmatched`. Exclude `/metrics` from request instrumentation so each scrape does not count itself or distort the request rate.
4. In `predict`, increment the success counter after inference succeeds, and increment the error counter in inference failure paths. Observe inference duration in a `finally` block so failed attempts are timed too.
5. Keep labels bounded. Never label metrics with image filename, image content, user ID, request ID, or arbitrary query-string values. High-cardinality labels can create a very large number of Prometheus time series.

## Tests

- Request a simple endpoint and compare metric values before and after; assert the matching method, route template, and status labels are present.
- Exercise a successful prediction and a failed prediction with a lightweight mocked model, then assert the appropriate prediction counters and duration sample change.
- Confirm requests to `/metrics` do not increase `http_requests_total`.
- Compare before/after values instead of assuming counters start at zero; the Python process and other tests may already have updated the shared registry.

## Example PromQL

Average request rate over five minutes:

```promql
sum by (route) (rate(http_requests_total[5m]))
```

p95 request duration, assuming the Histogram name above:

```promql
histogram_quantile(
  0.95,
  sum by (le) (rate(http_request_duration_seconds_bucket[5m]))
)
```

The queries return data only after the metric names and instrumentation are implemented and Prometheus has scraped samples.
