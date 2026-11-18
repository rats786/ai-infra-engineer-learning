# K8S-4: Use a deployable image reference for the cluster

**Status:** Open

## Current implementation

The Deployment references the versioned GHCR image
`ghcr.io/rats786/project-101-basic-model-serving:v1.0` with
`imagePullPolicy: IfNotPresent`. A tag-triggered GitHub Actions workflow builds
and publishes the image. After its first publish, the GHCR package must be made
public for unauthenticated cluster pulls.

## Verification still required

The repository does not have a Kubernetes cluster validation recorded yet.
Deploy on a clean node and confirm all pods start without `ErrImagePull` or
`ImagePullBackOff` before closing this item.

## Release process

Push a tag named `project-101-basic-model-serving-v<version>` to build and
publish the matching `v<version>` image tag. Update the Deployment image when
releasing a new version.

See the [tracker](tracker.md) for the full Kubernetes remediation checklist.
