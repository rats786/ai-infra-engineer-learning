# K8S-8: Treat ingress as separate platform infrastructure

**Status:** Open

## Current implementation

The API, Prometheus, and Grafana Services are `ClusterIP`. The repository does
not install an ingress controller or define public Ingress routes. This keeps
the unauthenticated API private by default; any controller remains a
cluster/platform responsibility.

## External route policy

No hostname, TLS certificate, or public API authentication policy is defined
for this project, so no public route is configured. If external access is
approved later, define an explicit Ingress using the platform-managed
controller, require TLS, and protect Grafana and any API route with the
appropriate authentication and access controls. Add API authentication before
creating a public inference route.

## Verification still required

Confirm the API, Prometheus, and Grafana Services are `ClusterIP` and that no
Ingress in the application namespaces routes to them. Validate any
platform-managed ingress separately.

See the [tracker](tracker.md) for the overall Kubernetes remediation order and verification steps.
