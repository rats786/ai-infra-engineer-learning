# MON-4: Provision a Grafana Dashboard

**Status:** Guide written; implementation not started.

## How provisioning works here

Grafana's data source is provisioned from [`monitoring/grafana/datasources/prometheus.yml`](../../monitoring/grafana/datasources/prometheus.yml). The dashboard provider in [`monitoring/grafana/dashboards/dashboard.yml`](../../monitoring/grafana/dashboards/dashboard.yml) tells Grafana where to find dashboard JSON files. Compose mounts that directory into Grafana read-only. A provider configuration does not itself create a dashboard; a dashboard JSON file is also needed.

## Suggested implementation

1. Give the Prometheus data source a stable UID such as `prometheus` in the datasource provisioning YAML.
2. Add a Grafana dashboard JSON file in `monitoring/grafana/dashboards/`, and set its panels to use the Prometheus data source UID.
3. Start with five panels:
   - **API availability:** `up{job="ml-api"}`
   - **Request rate:** `sum(rate(http_requests_total[5m]))`
   - **5xx error rate:** `sum(rate(http_requests_total{status_code=~"5.."}[5m]))`
   - **p95 request duration:** `histogram_quantile(0.95, sum by (le) (rate(http_request_duration_seconds_bucket[5m])))`
   - **p95 inference duration:** `histogram_quantile(0.95, sum by (le) (rate(prediction_duration_seconds_bucket[5m])))`
4. Use readable panel titles and units (`req/s`, `s`, or percent as appropriate), and choose a dashboard time range such as the last 15 minutes.
5. Ensure query names and labels exactly match the metrics implemented in MON-2. The examples above assume the suggested names from that guide.

## Verify

Restart Grafana or wait for its provider refresh, then confirm the dashboard appears without manual import. Send API traffic and check that availability and rate panels show values. Latency panels need enough observations and a non-empty time range; immediately after startup, they may have no percentile to display.

For Prometheus histograms, the `_bucket` series (including the `le` bucket label) is what the percentile expression uses.
