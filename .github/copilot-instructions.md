# Repository instructions

## Kubernetes deployments and configuration

- Treat checked-in Kubernetes manifests and Kustomize configurations as the source of truth. Deploy or update resources declaratively with `kubectl apply -f`, `kubectl apply -k`, or an approved GitOps workflow.
- Do not use imperative commands or cluster/UI edits to create, modify, scale, or delete deployed resources or configuration (including Secrets). If a change is needed, update the declarative configuration first.
- Do not make manual changes to a cluster or its configuration unless the user explicitly approves them beforehand.
- Keep secret values out of source control. Manage Secrets only through an explicitly approved, secure declarative workflow; do not create ad hoc cluster-only credentials.
