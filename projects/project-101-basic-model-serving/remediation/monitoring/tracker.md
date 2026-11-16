# Monitoring Remediation Tracker

This folder is a learning guide and work tracker for improving monitoring in this model-serving project. The solution notes describe changes for you to implement; no application or infrastructure code is changed by these guides.

## The Basics

Monitoring here has three parts:

1. **The API exposes metrics.** The API makes measurements available over HTTP at `/metrics`, for example, the number of successful predictions.
2. **Prometheus collects and stores metrics.** It periodically requests `/metrics`; each collection is a scrape. This project is configured to scrape every 15 seconds.
3. **Grafana queries and displays metrics.** Grafana uses Prometheus as its data source to query and visualize the stored measurements. Grafana does not collect API metrics itself.

```text
FastAPI at api:8000/metrics
          -> Prometheus at prometheus:9090
          -> Grafana at grafana:3000
```

`api`, `prometheus`, and `grafana` are Compose service names, used between containers. On your computer, use the published `localhost` ports instead.

### Terms you will see

- **Metric:** A named measurement, optionally split by labels such as route or status.
- **Counter:** A value that only increases, such as completed requests. `rate(counter[5m])` estimates its average per-second increase over five minutes.
- **Gauge:** A value that can go up or down, such as current in-flight requests.
- **Histogram:** A set of duration observations grouped into buckets, useful for latency percentiles such as p95.
- **Target:** An endpoint Prometheus is configured to scrape. **UP** means it could scrape and parse the endpoint, not that the API exports all the metrics you want.
- **PromQL:** Prometheus' query language, used in Prometheus and Grafana.

Avoid metric labels that can take a huge number of values, such as image filenames, user IDs, or request IDs. Every unique label combination creates another time series.

## Current State

- `monitoring/prometheus.yml` scrapes `api:8000/metrics` every 15 seconds.
- `monitoring/grafana/datasources/prometheus.yml` points Grafana to `http://prometheus:9090`.
- `src/api.py` serves Prometheus-formatted runtime metrics; request and inference metrics are still to be added.
- The Grafana dashboard provider is configured, but no dashboard JSON is present yet.
- Compose and application settings advertise metrics enable/port options that the API does not use; Prometheus scrapes `/metrics` unconditionally.

## Work Items

Work top to bottom. MON-1 is implemented and pending review; MON-2 and MON-3 are not started.

| ID | Priority | Status | Summary | Solution guide |
| --- | --- | --- | --- | --- |
| MON-1 | High | Pending review | Serve valid Prometheus exposition instead of a hard-coded sample. | [MON-1: Prometheus format](MON-1-prometheus-format.md) |
| MON-2 | High | Not started | Add bounded-cardinality request, prediction, and duration metrics. | [MON-2: API instrumentation](MON-2-api-instrumentation.md) |
| MON-3 | Medium | Not started | Make metrics configuration agree with API behavior and the scrape configuration. | [MON-3: Metrics setting](MON-3-metrics-setting.md) |
| MON-4 | Medium | Not started | Provision a Grafana dashboard for availability, traffic, errors, and latency. | [MON-4: Grafana dashboard](MON-4-grafana-dashboard.md) |
| MON-5 | Medium | Not started | Validate the complete Compose monitoring workflow. | [MON-5: End-to-end check](MON-5-end-to-end-check.md) |

## Try the Current Stack

From the repository root:

```powershell
docker compose up -d
docker compose ps
curl.exe http://localhost:8000/metrics
```

- Prometheus targets: `http://localhost:9090/targets`
- Prometheus query page: `http://localhost:9090/graph` (try `up`)
- Grafana: `http://localhost:3000`

The Prometheus data source is provisioned automatically. Until MON-4 is implemented, use Grafana's **Explore** view and query `up`. The application metric examples in MON-2 and MON-4 return data only after the corresponding code changes are implemented and scraped.

The local Compose credentials default to `admin` / `admin` unless overridden. Change them before exposing the services beyond a trusted local machine.

## Stop the Stack

```powershell
docker compose down
```

This preserves named data volumes. `docker compose down --volumes` also deletes Prometheus history and Grafana state.
