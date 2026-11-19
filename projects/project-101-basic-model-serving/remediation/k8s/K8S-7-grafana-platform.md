# K8S-7: Deploy Grafana as a separate platform service

**Status:** Open

## Current implementation

`kubectl apply -k monitoring` deploys Grafana independently in the `monitoring`
namespace. Kustomize provisions the Prometheus datasource using in-cluster DNS
and reuses the repository dashboard. A PersistentVolumeClaim stores Grafana
state, and the admin credentials are read from the `grafana-credentials`
Secret. ESO creates that Secret from the namespace-scoped Vault `SecretStore`
and `ExternalSecret`; the Vault KV v2 entry and Kubernetes auth role require
the documented post-initialization bootstrap. The Grafana Service is
internal-only.

## Verification still required

Deploy and bootstrap the Vault/ESO platform before applying the monitoring
Kustomize configuration. Confirm the SecretStore and ExternalSecret become
Ready, then restart or reschedule Grafana and confirm the Prometheus datasource
and ML API dashboard load and the PVC remains bound.

See the [tracker](tracker.md) for the full Kubernetes deployment roadmap.
