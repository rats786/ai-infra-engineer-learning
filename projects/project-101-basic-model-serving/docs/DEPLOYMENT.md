# Deployment Guide - Project 01: Basic Model Serving

## Prerequisites

- Docker installed
- Kubernetes cluster (minikube, kind, or cloud cluster)
- kubectl configured
- Python 3.11+

## Deployment Options

1. [Local Development (Docker Compose)](#option-1-local-development)
2. [Kubernetes (Minikube)](#option-2-kubernetes-local)
3. [Cloud Kubernetes (GKE/EKS/AKS)](#option-3-cloud-kubernetes)

---

## Option 1: Local Development (Docker Compose)

### Step 1: Clone and Setup

```bash
cd projects/project-101-basic-model-serving

# Create .env file
cp .env.example .env
# Edit .env as needed

# Download pre-trained model (or use model download script)
mkdir -p models
# TODO: Add model download script
```

### Step 2: Build and Run

```bash
# Build and start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Verify services
curl http://localhost:8000/health
curl http://localhost:9090  # Prometheus
open http://localhost:3000  # Grafana (admin/admin)
```

### Step 3: Test API

```bash
# Test prediction
curl -X POST "http://localhost:8000/v1/predict" \
  -F "file=@test_image.jpg"

# Check metrics
curl http://localhost:8000/metrics
```

### Step 4: Stop Services

```bash
docker-compose down
# Or keep data: docker-compose down --volumes
```

---

## Option 2: Kubernetes (Local - Minikube)

### Step 1: Start Minikube

```bash
# Start minikube with enough resources
minikube start --cpus=4 --memory=8192

# Enable addons
minikube addons enable metrics-server
minikube addons enable ingress

# Verify cluster
kubectl cluster-info
kubectl get nodes
```

### Step 2: Build Docker Image

```bash
# Build the image using the same reference as the Kubernetes Deployment
docker build -t ghcr.io/rats786/project-101-basic-model-serving:v1.0 .

# Load image into minikube
minikube image load ghcr.io/rats786/project-101-basic-model-serving:v1.0

# Verify
minikube image ls | grep project-101-basic-model-serving
```

### Step 3: Deploy to Kubernetes

```bash
# Create namespace
kubectl create namespace ml-serving

# Apply ConfigMap
kubectl apply -f kubernetes/configmap.yaml -n ml-serving

# Deploy application
kubectl apply -f kubernetes/deployment.yaml -n ml-serving

# Expose service
kubectl apply -f kubernetes/service.yaml -n ml-serving

# Setup autoscaling
kubectl apply -f kubernetes/hpa.yaml -n ml-serving
```

### Step 4: Verify Deployment

```bash
# Check pods
kubectl get pods -n ml-serving
kubectl describe pod <pod-name> -n ml-serving

# Check service
kubectl get svc -n ml-serving

# Check HPA
kubectl get hpa -n ml-serving

# View logs
kubectl logs -f deployment/ml-api -n ml-serving
```

### Step 5: Access the API

The Service is `ClusterIP` and is reachable only from within the cluster. For
local testing, forward a local port:

```bash
kubectl port-forward -n ml-serving svc/ml-model-serving-service 8000:80

# Test
curl http://localhost:8000/health
```

### Step 6: Deploy Prometheus

```bash
# Prometheus is a separate platform workload with an internal ClusterIP.
kubectl --context docker-desktop apply -f monitoring/kubernetes/prometheus.yaml
kubectl --context docker-desktop get pods,svc -n monitoring

# Inspect the API target
kubectl --context docker-desktop port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets and confirm the ml-api target is UP.
```

### Step 7: Deploy the Vault and ESO platform services

This local learning deployment uses a single Vault server with persistent
integrated Raft storage and a namespace-scoped External Secrets Operator (ESO).
The Vault and ESO Helm charts and image tags are pinned in
`platform/secret-management/`. Kustomize's Helm integration and Helm 3.6+ are
required to render the chart releases. Run these commands from
`projects/project-101-basic-model-serving`:

```bash
kubectl kustomize --enable-helm platform/secret-management | kubectl --context docker-desktop apply -f -
kubectl --context docker-desktop get pods,pvc -n vault
kubectl --context docker-desktop get pods -n external-secrets
```

Vault uses the cluster's default StorageClass (Docker Desktop currently uses
`hostpath`) for a 5Gi persistent volume. The service is `ClusterIP` only; no
Ingress, NodePort, or LoadBalancer is created. The listener uses plaintext
HTTP inside the cluster, so this configuration is for a trusted local learning
cluster, not production or an untrusted multi-tenant cluster.

The Vault chart declares Kubernetes `>=1.20`, but HashiCorp's current chart
documentation lists tested/supported Kubernetes releases as 1.32–1.36.
Docker Desktop's Kubernetes 1.30.5 is outside that documented test range; it
may render but is not an officially covered version. Confirm compatibility or
upgrade Kubernetes before relying on this setup.

### Step 8: Initialize and configure Vault

Vault does not run in dev mode and does not auto-initialize or auto-unseal.
Wait until the Vault pod is running, then initialize the Raft node once:

```bash
kubectl --context docker-desktop exec -it -n vault vault-0 -- vault operator init
```

Store the displayed recovery shares and initial root token in a secure
password manager or other approved offline location. Do not put them in Git,
a Kubernetes Secret, terminal transcript, or ticket. Unseal the node using
three distinct shares (the default initialization threshold is 3 of 5):

```bash
kubectl --context docker-desktop exec -it -n vault vault-0 -- vault operator unseal
```

Repeat the unseal command twice more, entering a different recovery share each
time. A restarted pod will need to be unsealed again. The PVC preserves the
Raft data across pod restarts, but this one-replica deployment is not highly
available and cannot tolerate loss of its node or volume.

After unsealing, use Terraform to declaratively configure the Kubernetes auth
method, least-privilege Grafana policy/role, and KV v2 engine. Terraform reads
the initial root token from `VAULT_TOKEN`; it is not stored in the repository
or Terraform configuration. The Terraform state contains Vault configuration
metadata, not the Grafana password, and is Git-ignored.
Install Terraform CLI and the Vault CLI before continuing; use a Vault CLI
compatible with the server version shown by the pinned Helm chart.

```bash
# Terminal 1
kubectl --context docker-desktop port-forward -n vault svc/vault 8200:8200

# Terminal 2
export VAULT_ADDR=http://127.0.0.1:8200
read -rsp "Vault initial root token: " VAULT_TOKEN
echo
export VAULT_TOKEN
terraform -chdir=platform/secret-management/vault-bootstrap init
terraform -chdir=platform/secret-management/vault-bootstrap apply
```

Entering the Grafana credential is a separate one-time secret-data operation,
not part of Terraform state. Do not run it until the secure credential-entry
step is approved. Enter a strong password without echoing or saving it:

```bash
read -rsp "Set Grafana admin password: " GRAFANA_ADMIN_PASSWORD
echo
printf '%s' "$GRAFANA_ADMIN_PASSWORD" | vault kv put secret/project-101/grafana admin-user=admin admin-password=-
unset GRAFANA_ADMIN_PASSWORD
vault token revoke -self
unset VAULT_TOKEN
```

The checked-in Terraform policy grants read access only to the Grafana KV v2
path. The Vault Kubernetes auth role accepts only the `vault-auth`
ServiceAccount in `monitoring`, requires the `vault` JWT audience, and issues
a short-lived token. The chart grants Vault's own ServiceAccount the
token-review permissions required by Kubernetes auth. The Terraform apply
and credential entry are separate operator actions; obtain approval before
running either against a cluster. Vault initialization/unseal approval alone
does not authorize post-init configuration or secret entry.

### Step 9: Deploy Grafana

After Vault is initialized, unsealed, and configured as above, apply the
monitoring Kustomize configuration. ESO reads the Vault KV v2 entry
`secret/project-101/grafana` and creates the `grafana-credentials` Secret
with `admin-user` and `admin-password`; Grafana's existing Secret references
remain unchanged.

```bash
kubectl --context docker-desktop apply -k monitoring
kubectl --context docker-desktop get pods,svc,pvc -n monitoring
kubectl --context docker-desktop get secretstores,externalsecrets -n monitoring
```

Wait for the `vault-grafana` SecretStore and `grafana-credentials`
ExternalSecret to report Ready before expecting Grafana to start. The
Grafana Service is internal. For local access, run:

```bash
kubectl --context docker-desktop port-forward -n monitoring svc/grafana 3000:3000
```

Then open `http://localhost:3000` and sign in with the username and password
stored in the Secret. Grafana data uses a 1Gi PersistentVolumeClaim, which
requires a default StorageClass in the cluster.

### External access policy

The manifests do not install an ingress controller or create public Ingress
routes. The API, Prometheus, and Grafana Services remain internal. Manage any
ingress controller as cluster infrastructure; only add a route after its
hostname, TLS certificate, and access-control policy are approved. Do not
expose the unauthenticated API publicly.

### Step 10: Cleanup

```bash
kubectl --context docker-desktop delete namespace ml-serving
kubectl --context docker-desktop delete namespace monitoring
kubectl --context docker-desktop delete namespace external-secrets
kubectl --context docker-desktop delete namespace vault
minikube stop
# Or: minikube delete
```

---

## Option 3: Cloud Kubernetes (Production)

The Kubernetes Deployment uses the public GHCR image
`ghcr.io/rats786/project-101-basic-model-serving:v1.0`. Publish it with:

```bash
git tag project-101-basic-model-serving-v1.0
git push origin project-101-basic-model-serving-v1.0
```

The repository workflow builds and publishes the image. After its first
publish, change the GHCR package visibility to **Public** so cluster nodes can
pull it without credentials.
Provider-specific registry examples below are alternatives; update the
Deployment image to match the image you publish.

### Step 3a: Google Kubernetes Engine (GKE)

```bash
# Set project
export PROJECT_ID=your-project-id
export CLUSTER_NAME=ml-cluster
export REGION=us-central1

gcloud config set project $PROJECT_ID

# Create GKE cluster
gcloud container clusters create $CLUSTER_NAME \
  --region=$REGION \
  --machine-type=n1-standard-2 \
  --num-nodes=2 \
  --enable-autoscaling --min-nodes=1 --max-nodes=5 \
  --enable-stackdriver-kubernetes

# Get credentials
gcloud container clusters get-credentials $CLUSTER_NAME --region=$REGION

# Verify
kubectl get nodes
```

**Build and Push Image:**
```bash
# Build for GCP
docker build -t gcr.io/$PROJECT_ID/ml-api:v1 .

# Push to Container Registry
docker push gcr.io/$PROJECT_ID/ml-api:v1

# Update deployment.yaml to use gcr.io image
```

**Deploy:**
```bash
kubectl apply -f kubernetes/ -n ml-serving
kubectl get svc -n ml-serving  # The API Service is internal (ClusterIP)
```

The API is not publicly exposed by default. If external access is required,
configure an authenticated, access-controlled ingress or API gateway before
exposing it.

**Cleanup:**
```bash
gcloud container clusters delete $CLUSTER_NAME --region=$REGION
```

### Step 3b: Amazon EKS (AWS)

```bash
# Install eksctl
# See: https://eksctl.io/installation/

# Create cluster
eksctl create cluster \
  --name ml-cluster \
  --region us-east-1 \
  --nodegroup-name standard-workers \
  --node-type t3.medium \
  --nodes 2 \
  --nodes-min 1 \
  --nodes-max 5 \
  --managed

# Get credentials (automatic with eksctl)
kubectl get nodes
```

**Build and Push Image:**
```bash
# Create ECR repository
aws ecr create-repository --repository-name ml-api --region us-east-1

# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/ml-api:v1 .
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ml-api:v1
```

**Deploy:**
```bash
# If using ECR instead of the default GHCR image, update the Deployment image first.
kubectl apply -f kubernetes/ -n ml-serving
kubectl get svc -n ml-serving  # The API Service is internal (ClusterIP)
```

**Cleanup:**
```bash
eksctl delete cluster --name ml-cluster --region us-east-1
```

### Step 3c: Azure Kubernetes Service (AKS)

```bash
# Create resource group
az group create --name ml-rg --location eastus

# Create AKS cluster
az aks create \
  --resource-group ml-rg \
  --name ml-cluster \
  --node-count 2 \
  --enable-addons monitoring \
  --generate-ssh-keys

# Get credentials
az aks get-credentials --resource-group ml-rg --name ml-cluster
kubectl get nodes
```

**Build and Push Image:**
```bash
# Create ACR
az acr create --resource-group ml-rg --name mlacr --sku Basic

# Build and push
az acr build --registry mlacr --image ml-api:v1 .
```

**Deploy:**
```bash
# If using ACR instead of the default GHCR image, update the Deployment image first.
kubectl apply -f kubernetes/ -n ml-serving
kubectl get svc -n ml-serving
```

**Cleanup:**
```bash
az group delete --name ml-rg --yes --no-wait
```

---

## Troubleshooting

### Pod Not Starting

```bash
# Check pod status
kubectl get pods -n ml-serving
kubectl describe pod <pod-name> -n ml-serving

# Common issues:
# 1. Image pull error: Check image name and registry access
# 2. CrashLoopBackOff: Check logs for errors
# 3. Insufficient resources: Check node resources
```

### Cannot Access Service

```bash
# Check service
kubectl get svc -n ml-serving
kubectl describe svc ml-model-serving-service -n ml-serving

# Check endpoints
kubectl get endpoints -n ml-serving

# The API Service is internal (ClusterIP); use port-forward for local testing.
# External access requires a separately configured, access-controlled ingress
# or API gateway.
```

### High Memory Usage

```bash
# Check resource usage
kubectl top pods -n ml-serving

# Adjust resource limits in deployment.yaml
# Optimize model loading (lazy loading, model quantization)
```

### Slow Inference

```bash
# Check logs for inference time
kubectl logs -n ml-serving deployment/ml-api | grep inference_time

# Optimize:
# 1. Use GPU instances
# 2. Enable model caching
# 3. Implement request batching
# 4. Use model optimization (ONNX, TensorRT)
```

---

## Monitoring and Logging

### View Logs

```bash
# Real-time logs
kubectl logs -f deployment/ml-api -n ml-serving

# Logs from specific pod
kubectl logs <pod-name> -n ml-serving

# Logs from previous crashed container
kubectl logs <pod-name> -n ml-serving --previous
```

### Check Metrics

```bash
# Prometheus targets
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
# Visit: http://localhost:9090/targets

# Query metrics
# predictions_total
# prediction_duration_seconds
```

### Access Grafana

```bash
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
# Visit: http://localhost:3000
# Import dashboard from monitoring/grafana/dashboards/
```

---

## CI/CD Integration

### GitHub Actions (See .github/workflows/ci-cd.yaml)

Automatically:
1. Run tests on PR
2. Build Docker image on merge to main
3. Push to container registry
4. Deploy to staging/production

**Setup:**
```bash
# Add secrets to GitHub repo
# - DOCKER_USERNAME
# - DOCKER_PASSWORD
# - KUBE_CONFIG (base64 encoded)
```

---

## Production Checklist

Before deploying to production:

- [ ] Resource limits configured (CPU, memory)
- [ ] Health checks configured (liveness, readiness)
- [ ] Monitoring and alerting setup
- [ ] Logging aggregation configured
- [ ] Auto-scaling rules tested
- [ ] Disaster recovery plan documented
- [ ] Security hardening (non-root user, network policies)
- [ ] Cost monitoring enabled
- [ ] Documentation updated
- [ ] Load testing completed
- [ ] Rollback procedure tested

---

## Next Steps

1. ✅ Deploy locally and test
2. ✅ Deploy to Kubernetes and verify
3. ✅ Setup monitoring and alerts
4. ✅ Run load tests
5. ✅ Document any issues and optimizations

For questions, see [TROUBLESHOOTING.md](./TROUBLESHOOTING.md)
