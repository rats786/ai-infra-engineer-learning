# MON-5: Verify Monitoring End to End

**Status:** Verified against the local Compose stack.

## Goal

Confirm the complete path works: the API emits metrics, Prometheus scrapes and stores them, and Grafana can query and display them.

## Local verification

Run from the repository root:

```powershell
docker compose up -d
docker compose ps
curl.exe http://localhost:8000/metrics
```

Then check:

1. Open `http://localhost:9090/targets` and confirm the `ml-api` target is **UP**. If it is down, open the target details and read the scrape error.
2. Open `http://localhost:9090/graph`, query `up{job="ml-api"}`, and confirm the result is `1`.
3. Generate ordinary API traffic, for example `curl.exe http://localhost:8000/` and `curl.exe http://localhost:8000/health`.
4. If testing prediction metrics, send a valid image with `curl.exe -F "file=@PATH_TO_IMAGE.jpg" http://localhost:8000/predict`. Use an image that exists locally; the repository may not include a sample image or model weights.
5. In Prometheus, query `http_requests_total` or `rate(http_requests_total[5m])` after MON-2 is implemented and at least one scrape has collected the updated metrics.
6. Open Grafana at `http://localhost:3000`, select the provisioned dashboard, and confirm the panels show the same metrics. The default local credentials are `admin` / `admin` unless overridden; do not keep those defaults for a non-local deployment.

Prometheus scrapes every 15 seconds in this project, so allow at least one interval after generating traffic. A range query such as `rate(...[5m])` also needs enough samples in its time window.

## Troubleshooting

- **Target down:** `docker compose logs api prometheus`; verify Prometheus uses `api:8000` inside the Compose network.
- **Target up, app metric absent:** inspect `/metrics`; confirm MON-1 and MON-2 have been implemented and the query uses the exact metric name.
- **Grafana cannot query `up`:** verify its provisioned datasource URL is `http://prometheus:9090` and check `docker compose logs grafana`.
- **Dashboard missing:** check the provider directory, mounted dashboard JSON, and Grafana provisioning logs.

Stop the services with `docker compose down`. This preserves named data volumes. `docker compose down --volumes` also removes Prometheus history and Grafana state.
