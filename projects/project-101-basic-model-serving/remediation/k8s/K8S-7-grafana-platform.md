# K8S-7: Deploy Grafana as a separate platform service

**Status:** Open

## Current implementation

`kubectl apply -k monitoring` deploys Grafana independently in the `monitoring`
namespace. Kustomize provisions the Prometheus datasource using in-cluster DNS
and reuses the repository dashboard. A PersistentVolumeClaim stores Grafana
state. The admin credentials are read from the `grafana-credentials`
Kubernetes Secret, which an operator creates directly and interactively
(password-based authentication); this project does not use Vault or the
External Secrets Operator. The Grafana Service is internal-only.

## Verification still required

Create the `grafana-credentials` Secret, then apply the monitoring Kustomize
configuration. Confirm Grafana becomes Ready and the Prometheus datasource and
ML API dashboard load, and that the PVC remains bound.

See the [tracker](tracker.md) for the full Kubernetes deployment roadmap.
