# Cloud GPU Rental & Testing Plan (Project 103)

## 1. Problem Statement & Motivation
Local hardware lacks an upgradeable NVIDIA GPU capable of running modern LLM serving infrastructure. Project 103 requires:
- **vLLM Inference Engine** running `Mistral-7B-Instruct-v0.2` (or LLaMA-3 8B) with PagedAttention and AWQ/FP16 precision.
- **RAG & Storage Stack**: Milvus (etcd + MinIO + Milvus-standalone), Redis, and PostgreSQL.
- **Observability Stack**: Prometheus, Grafana, and NVIDIA GPU exporter.

To achieve fast, cost-effective development without local hardware investments, this plan outlines renting on-demand cloud GPUs.

---

## 2. Hardware Sizing & Specifications

| Resource | Minimum Requirement | Recommended Specification | Rationale |
| :--- | :--- | :--- | :--- |
| **GPU** | 1x NVIDIA (Ampere/Ada) 16 GB VRAM | **1x NVIDIA A10G (24 GB) or RTX 4090 (24 GB) or L4 (24 GB)** | 7B model weights take 4.5 GB (AWQ) or ~14 GB (FP16). 24 GB VRAM guarantees comfortable headroom for vLLM KV cache and concurrent user requests. |
| **vCPU** | 4 cores | **8 cores** | Concurrent handling of Docker daemon, API routing, and document ingestion. |
| **System RAM** | 16 GB | **30 GB – 32 GB** | Running the full 7-container Docker Compose stack (Milvus, etcd, MinIO, Redis, Postgres, API, Prometheus) requires 12–16 GB RAM. |
| **Disk Storage**| 50 GB NVMe | **80 GB – 100 GB NVMe SSD** | Docker layers (~15 GB), HuggingFace cache (~15 GB), Milvus volumes, and OS. |

---

## 3. Cloud GPU Provider Comparison

| Provider | Recommended GPU Option | Hourly Rate (approx.) | Setup Time | Pros | Cons |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RunPod** *(Recommended)* | Secure Cloud: **NVIDIA A10G (24 GB)** or **L4 (24 GB)** | **$0.50 – $0.70 / hr** | < 2 minutes | Instant provisioning, no quota approval, persistent volume support, pre-built PyTorch/Docker templates. | Community cloud nodes can have variable bandwidth (stick to Secure Cloud). |
| **Lambda Labs** *(Strong Alternative)* | **1x NVIDIA A10 (24 GB)** | **$0.60 / hr** | < 5 minutes | Enterprise datacenters, official Ubuntu + CUDA + Docker environment, very clean SSH access. | GPUs frequently out of stock during peak hours. |
| **Vast.ai** | **1x RTX 4090 (24 GB)** | **$0.30 – $0.45 / hr** | < 5 minutes | Lowest pricing available. | Marketplace model with varied host reliability and connection speeds. |
| **AWS EC2** | `g5.2xlarge` (A10G 24GB, 8 vCPU, 32GB RAM) | **$1.21 / hr** (On-Demand) / **~$0.45 / hr** (Spot) | 24–48 hours (quota wait) | Enterprise security, direct integration with VPC, EKS, and IAM. | Requires submitting and waiting for GPU Service Quota approval; higher on-demand price. |

---

## 4. Cost Estimation & Budgeting

For a comprehensive learning and testing cycle of Project 103 (estimated **15 to 20 total active hours**):

- **Active Compute** (18 hours @ $0.60/hr): **$10.80**
- **Persistent Volume / Storage** (100 GB for 1 week): **$1.50**
- **Buffer / Test Runs**: **$2.70**
- **Total Estimated Project Cost**: **~$15.00 USD**

> [!TIP]
> **Pre-paid Deposit Strategy**: Fund the chosen platform (e.g., RunPod or Lambda) with a fixed $15–$20 balance to establish a hard cost ceiling.

---

## 5. Step-by-Step Execution Plan

### Step 1: Pre-Deployment Readiness (Local Machine)
Ensure all code and missing build files are prepared and committed to Git before spinning up paid GPU hours:
1. Create missing `requirements.txt`, `scripts/entrypoint.sh`, and `scripts/init-db.sql`.
2. Push all branches to the remote GitHub repository:
   ```bash
   git push origin <your-branch>
   ```

### Step 2: Provisioning the Cloud Instance
1. Create an account on **RunPod.io** (or **Lambda Labs**).
2. Deploy a Pod/VM with:
   - GPU: **1x NVIDIA A10G / RTX 4090 / L4 (24 GB VRAM)**.
   - Template: **RunPod PyTorch 2.2 / Ubuntu 22.04 with CUDA 12.1 and Docker**.
   - Storage: 80 GB container volume.
   - Attach your public SSH key (`~/.ssh/id_rsa.pub`).

### Step 3: Connect and Setup
1. Connect via SSH:
   ```bash
   ssh root@<INSTANCE_PUBLIC_IP> -p <PORT>
   ```
2. Verify GPU status and container toolkit:
   ```bash
   nvidia-smi
   docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi
   ```
3. Clone your repository:
   ```bash
   git clone <REPO_URL>
   cd ai-infra-engineer-learning/projects/project-103-llm-deployment
   cp .env.example .env
   ```

### Step 4: Docker Compose Deployment
1. Build and bring up auxiliary services first (Milvus, Redis, Postgres):
   ```bash
   docker compose up -d etcd minio milvus redis postgres
   docker compose ps
   ```
2. Build and launch `llm-server`:
   ```bash
   docker compose up -d --build llm-server
   docker compose logs -f llm-server
   ```
   *(vLLM will download model weights and allocate GPU memory).*

### Step 5: Local Access via SSH Port Forwarding
Run this SSH tunnel from your local machine to interact with remote services directly in your local browser:
```bash
ssh -N -L 8000:localhost:8000 \
       -L 3000:localhost:3000 \
       -L 9090:localhost:9090 \
       -L 9001:localhost:9001 \
       root@<INSTANCE_PUBLIC_IP> -p <PORT>
```
Endpoints now reachable locally:
- **FastAPI Docs**: `http://localhost:8000/docs`
- **FastAPI Health**: `http://localhost:8000/health`
- **Grafana Dashboard**: `http://localhost:3000`
- **Prometheus UI**: `http://localhost:9090`
- **MinIO Console**: `http://localhost:9001`

### Step 6: Testing & Benchmarking
Run the test suite and benchmark scripts on the remote host:
```bash
pytest tests/ -v
chmod +x scripts/benchmark.sh
./scripts/benchmark.sh
```

### Step 7: Teardown & Cost Guardrails
- When taking breaks: **Stop** the instance (compute billing pauses; only volume storage charges ~$0.0001/hr continue).
- When testing is complete: **Terminate** the instance and delete associated network volumes to ensure no recurring charges.
