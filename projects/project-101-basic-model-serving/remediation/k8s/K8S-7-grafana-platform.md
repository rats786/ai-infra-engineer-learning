# K8S-7: Deploy Grafana as a separate platform service

**Status:** Open

## Current implementation

`kubectl apply -k monitoring` deploys Grafana independently in the `monitoring`
namespace. Kustomize provisions the Prometheus datasource using in-cluster DNS
and reuses the repository dashboard. A PersistentVolumeClaim stores Grafana
state, and the admin credentials are read from the `grafana-credentials`
Secret. The Grafana Service is internal-only.

## Verification still required

Create the Secret and apply the Kustomize configuration after deploying
Prometheus. Restart or reschedule Grafana, then confirm the Prometheus
datasource and ML API dashboard load and the PVC remains bound.

See the [tracker](tracker.md) for the full Kubernetes deployment roadmap.
