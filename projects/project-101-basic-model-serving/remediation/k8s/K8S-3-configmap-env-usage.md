# K8S-3: Connect deployment environment variables to application configuration

**Status:** Open

## Why this matters

The Deployment manifest defines `MODEL_NAME` and `DEVICE`, but the API starter code currently hardcodes `resnet18` and `cpu` during model loading. That means environment values are ignored, and Kubernetes config changes do not affect runtime behavior.

## Root cause

The manifest advertises runtime knobs, but the application startup path does not read those settings. The result is a mismatch between desired configuration and actual runtime behavior.

## Recommended fix

1. Read `MODEL_NAME` and `DEVICE` from environment variables or a config object.
2. Validate that values are supported before loading the model.
3. Ensure the ConfigMap or Secrets values are reflected in the running process.
4. If the app intentionally has fixed behavior, remove unused knobs and document the fixed setup.

## Acceptance criteria

- Changing `MODEL_NAME` or `DEVICE` in the ConfigMap changes the actual runtime app configuration.
- Logs and health output reflect the configured values.
- Unsupported settings fail early with a clear error rather than silently ignoring the value.

See the [tracker](tracker.md) for the rest of the Kubernetes issue set and the validation order.
