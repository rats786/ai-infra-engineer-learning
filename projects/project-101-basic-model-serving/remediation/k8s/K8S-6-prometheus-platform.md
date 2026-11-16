# K8S-6: Deploy Prometheus as a separate monitoring platform workload

**Status:** Open

## Why this matters

The repository currently uses Docker Compose service names such as `api:8000` and `prometheus:9090`. Those names are meaningful only inside a single Compose network and are not valid Kubernetes service discovery assumptions. In Kubernetes, monitoring must be designed as a separate platform capability.

## Root cause

The monitoring configuration is coupled to the API workload and to Docker networking assumptions rather than Kubernetes-native service discovery. This makes Prometheus configuration brittle after pod rescheduling and prevents clean separation between the API application and platform infrastructure.

## Recommended fix

1. Deploy Prometheus as its own workload and service.
2. Configure Prometheus to scrape the API Service using a Kubernetes DNS name or a Prometheus Operator `ServiceMonitor`.
3. Keep the API metrics endpoint on the application port, but do not treat the Compose DNS topology as a cluster equivalent.
4. Maintain a clear separation between the API workload and the monitoring platform.

## Acceptance criteria

- Prometheus can scrape the API Service after pod restart or reschedule.
- The target is `UP` and fetches `/metrics` successfully.
- The monitoring platform remains independent from the API rollout and can be managed separately.

See the [tracker](tracker.md) for the K8S issue sequence and remaining deployment work.
