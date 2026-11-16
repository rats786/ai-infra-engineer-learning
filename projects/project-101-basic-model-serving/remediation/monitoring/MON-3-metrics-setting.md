# MON-3: Make Metrics Configuration Consistent

**Status:** Guide written; implementation not started.

## Current mismatch

[`docker-compose.yml`](../../docker-compose.yml) sets `PROMETHEUS_ENABLED=true`, while [`src/config.py`](../../src/config.py) defines `enable_metrics`. The API does not currently use either setting, and Prometheus is configured to scrape `/metrics` unconditionally in [`monitoring/prometheus.yml`](../../monitoring/prometheus.yml). This makes the apparent switch misleading.

## Recommended choice for this project

For the local learning stack, keep the scrape endpoint always available because Prometheus is always configured to scrape it. Remove the unused `PROMETHEUS_ENABLED` environment entry from Compose and remove or clearly deprecate the unused `enable_metrics` setting (and `metrics_port` if it is not used elsewhere). Then document that the API exposes metrics whenever it is running.

This is the smallest coherent setup: there is no “disabled” state that unexpectedly makes a configured Prometheus target fail.

## If a real on/off switch is required

Choose one canonical name, preferably `PROMETHEUS_ENABLED`, parse it as a boolean in application settings, and test both values. Decide what `/metrics` returns when disabled. If it returns `404`, also disable the corresponding Prometheus scrape job; otherwise Prometheus will correctly report the target as failing. Do not treat a scrape failure as a healthy disabled state.

Be aware that the compatibility fallback in `src/config.py` uses Pydantic `BaseModel` when `pydantic-settings` is unavailable. Verify environment-variable loading in the selected runtime before relying on `Settings` to read Compose variables; plain `BaseModel` does not provide `BaseSettings` environment behavior.

## Verify

- Confirm `PROMETHEUS_ENABLED`, `enable_metrics`, and `metrics_port` are no longer defined as inactive configuration; the documented behavior is always-on metrics on the API port.
- If choosing always-on, run Compose and confirm `/metrics` is still scrapeable.
- If choosing a switch, test enabled and disabled behavior, then confirm Prometheus configuration matches each mode.
