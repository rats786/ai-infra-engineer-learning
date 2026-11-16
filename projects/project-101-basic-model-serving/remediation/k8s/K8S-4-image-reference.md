# K8S-4: Use a deployable image reference for the cluster

**Status:** Open

## Why this matters

The manifest references `ml-model-serving:v1.0` with `imagePullPolicy: IfNotPresent`. This only works when the image is already available on each node or is resolvable from a configured registry. A clean cluster or a different node pool may fail to pull the image.

## Root cause

The repository does not yet define a production-grade image build/publish workflow or a registry target that every cluster node can resolve. The manifest therefore depends on local assumptions that do not hold in a real Kubernetes environment.

## Recommended fix

1. Publish the image to an accessible registry (for example, registry or a cluster-managed registry).
2. Use a full image name and tag that the cluster can resolve.
3. Configure the image pull policy to match the deployment pattern.
4. Validate the image on a fresh node or clean cluster before moving to production.

## Acceptance criteria

- The pod starts without `ErrImagePull` or `ImagePullBackOff`.
- The image is resolvable from all nodes that run the workload.
- The deployment is reproducible across a clean environment.

See the [tracker](tracker.md) for the full Kubernetes remediation checklist.
