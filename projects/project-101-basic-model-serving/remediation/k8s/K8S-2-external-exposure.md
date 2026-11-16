# K8S-2: Review external exposure and restrict the API surface

**Status:** Open

## Why this matters

The API Service is configured as a `LoadBalancer` and does not appear to enforce authentication. That exposes the inference endpoint directly, which is risky unless the service is explicitly intended to be public and properly protected.

## Root cause

The Kubernetes manifest makes the API reachable outside the cluster without any documented access-control boundary. In cluster environments, direct `LoadBalancer` exposure is often too broad for an internal model-serving workload.

## Recommended fix

1. Decide whether the API is private or public.
2. If private, keep the Service internal or use an internal load balancer / cluster network policy.
3. If public, front it with an authenticated Ingress or API gateway with TLS and access controls.
4. Do not expose the raw Service publicly unless that is an explicit security decision.

## Suggested implementation pattern

- Keep the API Service cluster-internal by default.
- Expose a vetted route through an ingress controller with TLS.
- Add authentication or a network boundary for Grafana and any public inference route.

## Acceptance criteria

- Unauthenticated external clients are blocked unless the public deployment is intentionally approved.
- The API is only reachable from expected networks or via an authenticated ingress.
- The team can explain and document the intended exposure model.

See the [tracker](tracker.md) for the full remediation sequence and verification context.
