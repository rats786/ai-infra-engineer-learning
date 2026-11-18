# Kubernetes Remediation Tracker

This tracker records Kubernetes deployment risks and planned platform work. The model API is an application workload; Prometheus, Grafana, and the ingress controller are platform applications and should be deployed and operated separately from it. Items are open until the relevant manifest, chart configuration, or application change is implemented and its verification criteria pass.

## Current State

- The Deployment selector and pod labels match.
- The Service selector matches the pod labels and targets container port `8000`.
- `monitoring/prometheus.yml` and Grafana provisioning currently use Docker Compose service names (`api` and `prometheus`); they are not Kubernetes-ready configurations.
- Prometheus, Grafana, and an ingress controller do not yet have Kubernetes deployment definitions in this repository.
- No Kubernetes cluster validation has been run for these findings yet.

## Work Items

| ID | Priority | Status | Summary | Verification | Solution guide |
| --- | --- | --- | --- | --- | --- |
| K8S-1 | High | Open | Make readiness fail when the model is unavailable. `/health` currently responds with HTTP 200 even when its JSON status is `unhealthy`, so the HTTP readiness probe can route traffic to a pod that cannot infer. | Simulate model load failure; confirm the pod remains NotReady and receives no Service traffic. Confirm it becomes Ready after the model loads. | [K8S-1 readiness fail guide](K8S-1-readiness-model-failure.md) |
| K8S-2 | High | Open | Review external exposure. `service.yaml` uses `type: LoadBalancer`, while the API currently has no authentication. Restrict it to internal access or put an authenticated, access-controlled ingress in front if public access is required. | Inspect the provisioned endpoint and verify unauthenticated external clients cannot invoke the API unless public access is explicitly intended and protected. | [K8S-2 external exposure guide](K8S-2-external-exposure.md) |
| K8S-3 | Medium | Open | Connect Deployment environment variables to application configuration. The manifest sets `MODEL_NAME` and `DEVICE`, but API startup currently hardcodes `resnet18` and `cpu`. | Change the ConfigMap values and confirm the running application uses the configured model/device, or remove unsupported knobs and document fixed behavior. | [K8S-3 configmap guide](K8S-3-configmap-env-usage.md) |
| K8S-4 | Medium | Open | Publish and deploy the versioned GHCR image `ghcr.io/rats786/project-101-basic-model-serving:v1.0`; clean-node pull verification is pending. | Publish the image, make its GHCR package public, then deploy on a clean node and confirm all pods start without `ErrImagePull` or `ImagePullBackOff`. | [K8S-4 image reference guide](K8S-4-image-reference.md) |
| K8S-5 | Medium | Open | Allow up to five minutes for the application to start responding before liveness/readiness probes begin; clean-cluster validation is pending. | Test with startup taking longer than the liveness delay but less than five minutes; confirm no restart occurs and the pod becomes Ready after model initialization. | [K8S-5 startup probe guide](K8S-5-startup-probe.md) |
| K8S-6 | High | Open | Deploy Prometheus independently in the `monitoring` namespace and scrape the API through its stable in-cluster Service DNS; cluster verification is pending. | Confirm the `ml-api` target is `UP` after API pod rescheduling and request/inference metrics are queryable. | [K8S-6 Prometheus platform guide](K8S-6-prometheus-platform.md) |
| K8S-7 | High | Open | Deploy Grafana independently with Kustomize-provisioned datasource/dashboard, a credentials Secret, and persistent storage; cluster verification is pending. | Restart or reschedule Grafana and confirm its datasource, dashboard, PVC, and dashboard queries remain available. | [K8S-7 Grafana platform guide](K8S-7-grafana-platform.md) |
| K8S-8 | High | Open | Treat the ingress controller as cluster/platform infrastructure installed and managed separately. Expose the API and Grafana through explicit Ingress resources only where needed; keep their Services internal and configure TLS and access control for Grafana and any public API route. | Confirm only intended hostnames/routes are reachable, TLS is valid, protected routes reject unauthenticated access, and internal Prometheus access does not require public ingress. | [K8S-8 ingress guide](K8S-8-ingress-controller.md) |

## Suggested Verification Sequence

From the repository root, after implementing the items:

```powershell
kubectl apply -f kubernetes/configmap.yaml
kubectl apply -f kubernetes/deployment.yaml
kubectl apply -f kubernetes/service.yaml
kubectl apply -f kubernetes/hpa.yaml
kubectl rollout status deployment/ml-model-serving-deployment
kubectl get pods,svc,hpa
kubectl describe deployment ml-model-serving-deployment
```

Then check pod readiness, Service endpoints, external exposure policy, and API responses against the acceptance criteria above. Deploy and verify the monitoring platform and ingress controller through their own platform release/process rather than coupling them to the API rollout. HPA CPU and memory scaling also depends on the cluster's metrics API being available; inspect `kubectl describe hpa ml-model-serving-hpa` for missing-metrics conditions.
