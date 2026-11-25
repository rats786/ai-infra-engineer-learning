# Local Host Resource Remediation Tracker

**Target Machine:** Local Windows Workstation (Docker Desktop + WSL 2)  
**Associated Project:** `project-102-mlops-pipeline`  
**Location:** `planning/LOCAL_RESOURCE_REMEDIATION_TRACKER.md`  
**Audit Reference:** [RESOURCE_ANALYSIS_AND_RECOMMENDATIONS.md](../RESOURCE_ANALYSIS_AND_RECOMMENDATIONS.md)  
**Status:** Disk guardrails complete | Kubernetes disabled | Runtime memory remains the active full-stack gate  
**Last Updated:** 25 November 2026  

---

## 1. Executive Resource Dashboard (Live Status)

| Resource Metric | Baseline (Audited) | Current Measured | Target Threshold | Readiness Gate |
| :--- | :--- | :--- | :--- | :--- |
| **Available Host RAM** | 3.58 GB (77% load) | **4.56 GB (71.3% load)** | $\ge$ 6.0 – 8.0 GB Free | 🟡 **IMPROVED (Below Full-Stack Target)** |
| **Free Disk Space (`C:\`)** | 24.66 GB | **120.44 GB** | $\ge$ 35.0 – 40.0 GB Free | ✅ **PASS** |
| **Docker Virtual Disk (`docker_data.vhdx`)** | 97.86 GB | **3.95 GB** on disk | Stable, sparse VHD | ✅ **PASS (Compacted)** |
| **WSL 2 Memory Boundary** | Uncapped (8GB default) | **6 GB Hard Cap + 4 vCPUs** | Configured in `.wslconfig` | ✅ **PASS (Applied)** |
| **WSL 2 Storage Guardrail**| Uncapped (`ext4.vhdx` balloons) | **`sparseVhd=true`** | Set in `.wslconfig` & `fsutil` | ✅ **PASS (Applied)** |
| **WSL 2 Memory Reclaim** | Manual / Static | **`autoMemoryReclaim=gradual`** | Dynamic idle RAM release | ✅ **PASS (Applied)** |
| **Docker Desktop Kubernetes** | Enabled with 18 active control-plane/workload containers | **Disabled; 0 active containers reported** | Disabled for the Compose pass | ✅ **PASS (Resources Reclaimed)** |

---

## 2. Current Constraint

Disk compaction is complete: `C:\Users\ratz\AppData\Local\Docker\wsl\disk\docker_data.vhdx` now measures **3.95 GB**, and drive C: has **120.44 GB free**. The active constraint is host RAM, not storage.

Docker Desktop currently reports a 6 GB memory limit, 4 CPUs, and no active containers. Docker Desktop Kubernetes is disabled, and its API endpoint no longer responds. Host Windows RAM improved to 4.56 GB free, which permits a staged Tier 1 smoke test, but not the full Project 102 stack until the 6–8 GB preflight target is met.

---

## 3. Master Remediation Task Board

| Task ID | Category | Action Item | Target Yield | Priority | Status | Verification & Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RES-01** | **WSL Guardrail** | Create `C:\Users\ratz\.wslconfig` with 6GB RAM, 4 CPUs, 4GB swap, `sparseVhd=true`, `autoMemoryReclaim=gradual` | Memory + Storage guardrails | **P0** | **COMPLETED** | Verified file written to `C:\Users\ratz\.wslconfig` |
| **RES-02** | **WSL Guardrail** | Restart WSL 2 to activate new boundaries (`wsl --shutdown`) | Activates limits | **P0** | **COMPLETED** | WSL restarted; memory freed |
| **RES-03** | **Disk Recovery** | Purge dangling Docker images, build cache, and unused volumes | +15.29 GB internal | **P0** | **COMPLETED** | Pruned 17 containers, 6 images, 14 build caches (**15.29 GB freed**) |
| **RES-04** | **Disk Recovery** | Purge Windows Temp files (`$env:TEMP`) | +1 – 3 GB disk | **P1** | **COMPLETED** | Purged 274 items; recovered ~500 MB (now 26.54 GB free) |
| **RES-05** | **Disk Recovery** | Compact `docker_data.vhdx` to release unused blocks | +15 GB on C: | **P0** | **COMPLETED** | VHDX now measures 3.95 GB; C: has 120.44 GB free |
| **RES-06** | **RAM Recovery** | Audit top host memory consumers | Reclaim host RAM | **P0** | **COMPLETED** | Relieved host memory pressure |
| **RES-07** | **RAM Recovery** | Reclaim uncommitted RAM down to `< 50%` load | Target $\ge$ 6 – 8 GB free | **P0** | **IMPROVED** | 4.56 GB free after disabling Kubernetes; continue closing high-memory applications |
| **RES-08** | **Pre-Flight** | Run pre-flight health script to confirm RAM & Disk readiness | Tiered or full-stack gate | **P0** | **TIER 1 READY** | Disk passes; staged Tier 1 may run, while the full stack waits for 6–8 GB free |
| **RES-09** | **Docker Startup** | Execute Tier 1 launch (Postgres, MinIO, Redis, init-db) | Base services UP | **P1** | **READY** | Start only the base tier and measure memory |
| **RES-10** | **Docker Startup** | Execute Tier 2 launch (Airflow, MLflow, Model Server) | Pipelines UP | **P1** | **PENDING** | Blocked on Tier 1 |

---

## 4. Runtime RAM Preflight

Before starting Project 102:

1. Stop unrelated containers and services.
2. Disable Docker Desktop Kubernetes if the local Kubernetes cluster is not needed.
3. Close high-memory desktop applications.
4. Recheck `Get-CimInstance Win32_OperatingSystem | Select-Object FreePhysicalMemory`.
5. Proceed when at least 6–8 GB of host RAM is free.

Do not use broad image or volume pruning while other projects are active; inspect `docker system df` and remove only named, unused resources.

---

## 5. Phase-by-Phase Roadmap

```
[Phase 1: WSL Guardrails] ➔ COMPLETED ✅ (6GB RAM, 4 CPUs, sparseVhd, autoMemoryReclaim)
           │
[Phase 3: RAM Recovery]   ➔ IMPROVED 🟡 (4.56 GB Free / 71.3% Host Load)
           │
[Phase 2: Disk Recovery]  ➔ COMPLETED ✅
           ├── Step 2.1: Purged Windows Temp Files ✅ (+0.5 GB)
           ├── Step 2.2: Docker Prune ✅ (15.29 GB freed internally)
           └── Step 2.3: Compact docker_data.vhdx ✅ (Now 3.95 GB; C: has 120.46 GB free)
           │
[Phase 4: Pre-Flight Gate]➔ TIER 1 READY 🟡 / FULL STACK BLOCKED 🔴
           │
[Phase 5: Staged Launch]  ➔ Tier 1 (Postgres/MinIO) ➔ Tier 2 (Airflow/MLflow)
```
