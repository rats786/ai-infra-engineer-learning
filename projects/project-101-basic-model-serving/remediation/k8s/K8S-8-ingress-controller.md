# K8S-8: Treat ingress as separate platform infrastructure

**Status:** Open

## Why this matters

The ingress controller is cluster infrastructure, not an application component of the API deployment. Access patterns, TLS, and authentication should be configured at the ingress layer rather than by exposing Services directly to the public internet.

## Root cause

The current Service is a `LoadBalancer` and there is no defined ingress or platform-control boundary. That makes routing, TLS, and access policy decisions implicit and hard to audit.

## Recommended fix

1. Install or manage the ingress controller as cluster/platform infrastructure.
2. Keep the API Service internal unless a public route is explicitly approved.
3. Define explicit Ingress resources for the routes that need external exposure.
4. Configure TLS and access controls for Grafana and any public API route.
5. Keep internal monitoring traffic off public ingress paths.

## Acceptance criteria

- Only approved hosts and routes are publicly reachable.
- TLS is configured correctly for any public endpoints.
- Public routes reject unauthenticated traffic when access control is required.
- Internal Prometheus or Grafana traffic does not depend on public ingress exposure.

See the [tracker](tracker.md) for the overall Kubernetes remediation order and verification steps.
