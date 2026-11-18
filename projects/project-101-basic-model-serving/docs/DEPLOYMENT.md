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
kubectl apply -f monitoring/kubernetes/prometheus.yaml
kubectl get pods,svc -n monitoring

# Inspect the API target
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets and confirm the ml-api target is UP.
```

### Step 7: Cleanup

```bash
kubectl delete namespace ml-serving
kubectl delete namespace monitoring
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
