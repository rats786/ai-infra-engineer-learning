# K8S-5: Add a startup probe for slow model initialization

**Status:** Open

## Current implementation

The Deployment has a startup probe on `/` with a 10-second period and a
failure threshold of 30, allowing up to 5 minutes for the application to start
responding before liveness and readiness probes begin.

The startup probe checks process responsiveness rather than model readiness.
The existing `/health` readiness probe continues to keep a pod out of Service
endpoints when model loading fails.

## Verification still required

Test a startup longer than the liveness delay but shorter than the five-minute
window. Confirm Kubernetes does not restart the container during startup and
the pod becomes Ready after model initialization.

See the [tracker](tracker.md) for the remaining K8S items and the verification sequence.
