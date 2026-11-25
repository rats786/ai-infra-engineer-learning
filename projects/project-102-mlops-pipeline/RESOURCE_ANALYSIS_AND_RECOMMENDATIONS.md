# System Resource Analysis & Docker Desktop Sizing Recommendations

**Target Project:** `project-102-mlops-pipeline`  
**Host Environment:** Windows 10/11 with Docker Desktop (WSL 2 Backend)  
**Inspection Date:** 25 November 2026  
**Document Purpose:** Hardware audit of the local laptop, gap analysis against stack demands, and optimization configuration to prevent Out-Of-Memory (OOM) crashes and disk exhaustion.

---

## 1. Executive Hardware Audit (Current System State)

| Resource Metric | Detected Hardware Value | Status vs MLOps Stack Demands |
| :--- | :--- | :--- |
| **CPU Architecture** | 8 Logical Cores (Intel 64-bit, 4 Cores / 8 Threads) | **PASS (Optimal)** |
| **Total Physical RAM**| **15.88 GB** (~16.0 GB) | **PASS (Baseline Cap)** |
| **Available Host RAM**| **2.45 GB** (Host Memory Load: **84.6%**) | **FAIL (Too Tight for Full Stack)** |
| **WSL 2 Configuration**| 6 GB RAM / 4 CPUs / 4 GB swap, sparse VHD, gradual memory reclaim | **PASS (Configured)** |
| **Primary Disk (`C:\`)**| **236.79 GB Total / 120.46 GB Free** (~49.1% Free) | **PASS** |

---

## 2. Resource Gap Analysis: Available vs Required

The current `docker-compose.yml` for Project 102 defines 9 services:
1. `postgres` (PostgreSQL 15)
2. `redis` (Redis 7)
3. `minio` (S3 Object Storage)
4. `mlflow` (Tracking Server & Registry)
5. `airflow-init` (Transient DB migration)
6. `airflow-webserver` (Gunicorn / UI)
7. `airflow-scheduler` (Task engine & DAG parser)
8. `prometheus` (TSDB metrics scraper)
9. `grafana` (Observability dashboard)
The planned `model-server` FastAPI inference engine will increase the stack to 10 services.

### Comparison Matrix

| Component | Minimum Required | Recommended | What Your System Has | Feasibility Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **CPU** | 4 Cores | 6 – 8 Cores | **8 Logical Cores** | **Full Capacity**: Sufficient compute for DAG scheduling, model training, and background services. |
| **RAM (Allocated to Docker)** | 6.0 GB | 8.0 – 10.0 GB | **2.45 GB Free** on Windows; Docker budget is 6 GB | **Constrained**: free host RAM is below the recommended 7.5–8 GB preflight target, especially with Docker Desktop Kubernetes and 18 active containers. |
| **Disk Space (`C:\`)** | 20.0 GB free | 35.0 – 50.0 GB free | **120.46 GB Free** | **Pass**: sufficient for Project 102 images, volumes, and local artifacts. |

---

## 3. Immediate Action Plan & Configuration Recommendations

To ensure your laptop runs the entire Docker Compose stack reliably without freezing or running out of memory, execute the following steps:

### Action 1: Create a Customized `.wslconfig`
By default, WSL 2 attempts to claim up to 50% of your total RAM (~8 GB). Because your host currently has only 3.58 GB free, creating an explicit memory cap prevents Docker from competing with your host OS.

Create a file named `.wslconfig` in your user home directory:  
**Path:** `C:\Users\ratz\.wslconfig`

```ini
[wsl2]
# Cap Docker/WSL2 at 6 GB RAM
memory=6GB

# Assign 4 cores to Docker, leaving 4 cores for Windows host responsiveness
processors=4

# Enable a 4 GB swap file on disk for transient spikes
swap=4GB

# Enable page reporting to free unused container memory back to Windows
pageReporting=true
```

*To apply changes, restart WSL in PowerShell:*
```powershell
wsl --shutdown
```

---

### Action 2: Free Host RAM Prior to Startup
Currently, your host system is at **77% utilization** (using ~12.3 GB of RAM).
- Close memory-intensive background applications (e.g., Chrome/Edge browser tabs, heavy IDE instances, Slack/Teams).
- Target: Bring host memory load down to **under 50%** so at least **6.0 to 8.0 GB of RAM** is free for the Docker engine.
- If Kubernetes is not needed for this implementation pass, disable Docker Desktop Kubernetes to reclaim the Kubernetes control-plane containers.

---

### Action 3: Free Disk Space on Drive `C:\`
The measured disk state is currently healthy. Avoid broad `docker system prune -a --volumes` because it can remove unrelated project volumes and images:
1. **Inspect Docker resource usage before cleanup:**
   ```powershell
   docker system df
   ```
2. Remove only specific, unused containers, images, or volumes after identifying them.

---

### Action 4: Run Optimized / Staged Docker Compose
Rather than booting all containers simultaneously, run them in logical tiers:

1. **Tier 1 (Storage & DB Foundation):**
   ```powershell
   docker-compose up -d postgres redis minio
   docker-compose run --rm airflow-init
   ```
2. **Tier 2 (Core Tracking & Pipelines):**
   ```powershell
   docker-compose up -d mlflow airflow-webserver airflow-scheduler
   ```
3. **Tier 3 (On-Demand Serving & Monitoring):**
   ```powershell
   docker-compose up -d model-server prometheus grafana
   ```

*(Tip: If not using Celery executor in Airflow, you can stop the `redis` container to save ~100 MB of RAM).*

---

## 4. Final Verdict

- **Can this laptop implement the project?** **YES, immediately.**
- **Can it launch the full Project 102 Compose stack now?** **Not yet.** Free host RAM is only 2.45 GB while 18 Docker/Kubernetes containers are already active.
- **The Good:** Your CPU (8 logical cores) is more than sufficient.
- **The Risks:** Host RAM pressure can cause WSL thrashing or OOM during image builds and Airflow startup.
- **The Solution:** Begin code implementation now; before full Compose startup, stop unrelated containers or Docker Desktop Kubernetes, close high-RAM host applications, and recheck for at least 6–8 GB of free host RAM.
