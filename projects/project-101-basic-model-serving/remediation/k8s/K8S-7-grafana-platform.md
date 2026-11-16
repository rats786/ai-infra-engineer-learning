# K8S-7: Deploy Grafana as a separate platform service

**Status:** Open

## Why this matters

Grafana is a platform application, not part of the API workload. It needs a provisioned Prometheus datasource, dashboard configuration, and storage that survive pod restarts and rescheduling. This is not a Compose-only concern.

## Root cause

The repository currently contains Compose-specific datasource configuration using `http://prometheus:9090`, which is not a Kubernetes service address. Grafana is also not defined as a separate workload in the repository, so the platform dependencies are missing.

## Recommended fix

1. Deploy Grafana independently from the API and Prometheus.
2. Provision the Prometheus datasource using the in-cluster service DNS name.
3. Add dashboard provisioning and persistent storage as needed.
4. Store credentials in a Kubernetes Secret rather than in static config files.

## Acceptance criteria

- Grafana can reconnect to Prometheus after restart or reschedule.
- Dashboards remain available from the configured storage or provisioning path.
- Secrets hold credentials and no sensitive values are checked into source control.
- Grafana is managed as a platform component, not bundled with the API deployment.

See the [tracker](tracker.md) for the full Kubernetes deployment roadmap.
