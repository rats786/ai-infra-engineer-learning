# K8S-6: Deploy Prometheus as a separate monitoring platform workload

**Status:** Open

## Current implementation

`monitoring/kubernetes/prometheus.yaml` deploys Prometheus as a separate
workload in the `monitoring` namespace. Its scrape configuration targets the
API Service at
`ml-model-serving-service.ml-serving.svc.cluster.local:80/metrics`, so API pod
rescheduling does not change the scrape target. Prometheus itself is exposed
only by an internal `ClusterIP` Service.

## Verification still required

Apply the manifest after the API Service exists. Confirm the `ml-api` target is
`UP` in Prometheus and remains `UP` after an API pod reschedule.

See the [tracker](tracker.md) for the K8S issue sequence and remaining deployment work.
