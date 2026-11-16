# K8S-5: Add a startup probe for slow model initialization

**Status:** Open

## Why this matters

Model loading can take longer than the default liveness timing. Without a startup probe, Kubernetes may kill the container before initialization completes, which creates a flapping or crashing deployment.

## Root cause

The deployment does not include a startup probe, and the app is likely slower than the liveness threshold during model initialization. This is especially relevant for a model-serving container that downloads or loads a large model artifact.

## Recommended fix

1. Add a startup probe that checks a lightweight endpoint or process state before the container is considered started.
2. Give the app enough time to finish model load and warm-up.
3. Keep liveness focused on runtime health rather than startup timing.
4. Use a longer `failureThreshold` or `periodSeconds` if the model is large or slow.

## Acceptance criteria

- The container is not restarted while model initialization is still running.
- Once the model is ready, the pod becomes `Ready` and begins receiving traffic.
- Liveness checks do not mask startup delays.

See the [tracker](tracker.md) for the remaining K8S items and the verification sequence.
