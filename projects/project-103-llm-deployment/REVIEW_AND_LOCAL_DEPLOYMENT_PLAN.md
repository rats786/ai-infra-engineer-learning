# Project 103 LLM Deployment Platform: Comprehensive Review, Remediation Plan & Tracker

**Target Project:** `C:\repos\ai-infra-engineer-learning\projects\project-103-llm-deployment`  
**Review Date:** November 2026  
**Document Purpose:** Review current codebase readiness, provide a structured remediation plan for all build and deployment defects, establish an implementation tracker, and outline execution runbooks for both local development and cloud GPU deployment.

---

## 1. Executive Summary

`project-103-llm-deployment` provides an architectural blueprint for serving open-source Large Language Models (such as `Mistral-7B-Instruct-v0.2` or `LLaMA-3`) with vLLM, RAG (Retrieval-Augmented Generation) via Milvus, caching via Redis, metadata storage via PostgreSQL, and observability via Prometheus and Grafana.

**Current State & Findings:**
- The repository is currently a **scaffolding/stub project**.
- Core modules in `src/` (`api/`, `llm/`, `rag/`, `monitoring/`) define classes and method signatures, but the operational code consists of `# TODO:` placeholders.
- All unit and integration tests in `tests/` contain empty placeholder functions with `pass`.
- **Immediate Build Blockers**: `requirements.txt`, `scripts/entrypoint.sh`, and `scripts/init-db.sql` are referenced across `Dockerfile` and `docker-compose.yml` but do not exist on disk.
- **Hardware & Compose Constraints**: `docker-compose.yml` strictly enforces NVIDIA GPU reservations and configures heavy default services (Mistral-7B and multi-container Milvus: `etcd`, `minio`, `milvus`), preventing local execution without NVIDIA hardware and large memory pools.

---

## 2. Detailed Component Review & Gap Analysis

### 2.1 Core Source Code (`src/`)
| Module | Current State | Missing Requirements / Gaps |
| :--- | :--- | :--- |
| `src/api/main.py` | Lifespan and endpoints stubbed out with `# TODO`. | Needs active lifespan handling for engine/mock initialization, `/health`, `/metrics`, and `/generate` routes. |
| `src/api/models.py` | Pydantic models defined with commented-out field definitions. | Needs concrete Pydantic schemas for `GenerateRequest`, `GenerateResponse`, `RAGGenerateRequest`, and `HealthResponse`. |
| `src/llm/server.py` | vLLM wrapper class initialized; inference methods stubbed. | Needs vLLM engine initialization with fallback/mock option when CUDA is unavailable. |
| `src/rag/pipeline.py` | RAG pipeline skeleton with TODOs. | Needs concrete text chunking, embedding generation (`all-MiniLM-L6-v2`), and vector DB retrieval. |
| `src/monitoring/metrics.py` | Metric collectors uninitialized. | Needs Prometheus counters and histograms for inference latency, token counts, and request throughput. |

### 2.2 Docker & Compose Setup (`Dockerfile`, `docker-compose.yml`)
1. **Missing `requirements.txt`**:
   - `Dockerfile` lines 52 & 76 attempt `COPY requirements.txt .` and `pip install -r requirements.txt`.
   - Build halts immediately at Stage 2.
2. **Missing `scripts/entrypoint.sh`**:
   - `Dockerfile` line 128 attempts `COPY scripts/entrypoint.sh /app/entrypoint.sh` and designates it as `ENTRYPOINT`.
   - Build halts at Stage 4.
3. **Missing `scripts/init-db.sql`**:
   - `docker-compose.yml` line 116 mounts `./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql`.
   - Docker daemon creates an empty directory if missing, disrupting PostgreSQL database startup.
4. **Hardcoded NVIDIA GPU Reservation**:
   - `docker-compose.yml` line 181 reserves an NVIDIA GPU (`driver: nvidia, count: 1`).
   - Machines lacking an NVIDIA GPU or the NVIDIA Container Toolkit fail on `docker compose up`.
5. **High Memory Footprint (Milvus Standalone)**:
   - Spinning up `etcd`, `minio`, and `milvus-standalone` requires >8 GB RAM with a 90-second healthcheck start period.
6. **Prometheus Scrape Configuration**:
   - `monitoring/prometheus/prometheus.yml` uses `kubernetes_sd_configs` for pod discovery, which does not scrape containers in Docker Compose without static target declarations.

### 2.3 Tests (`tests/`)
- `tests/test_api.py`, `tests/test_llm.py`, and `tests/test_rag.py` contain empty test functions with `pass`. Automated CI/CD or local pytest runs do not validate system behavior.

---

## 3. Remediation Plan

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REMEDIATION WORKSTREAMS                         │
├─────────────────┬──────────────────┬─────────────────┬────────────────┤
│ 1. BUILD ASSETS │ 2. RUNTIME STACK │ 3. APP CODE     │ 4. TEST & OBS  │
│ - requirements  │ - CPU/GPU Profile│ - Lifespan Init │ - Active Tests │
│ - entrypoint.sh │ - Lightweight DB │ - Pydantic Model│ - Scrape Setup │
│ - init-db.sql   │ - .env defaults  │ - Model Serving │ - Smoke Probes │
└─────────────────┴──────────────────┴─────────────────┴────────────────┘
```

### Issue REM-01: Missing `requirements.txt`
- **Defect**: Docker image build and `scripts/setup.sh` fail because `requirements.txt` is absent.
- **Root Cause**: Dependency specification was omitted during initial scaffolding.
- **Remediation**:
  1. Author `requirements.txt` with pinned versions of:
     `fastapi==0.109.0`, `uvicorn[standard]==0.27.0`, `pydantic==2.6.0`, `pydantic-settings==2.1.0`, `sse-starlette==1.8.2`, `torch>=2.2.0`, `transformers>=4.38.0`, `sentence-transformers>=2.4.0`, `redis>=5.0.0`, `pymilvus>=2.3.0`, `psycopg2-binary>=2.9.0`, `prometheus-client>=0.19.0`, `pytest>=7.4.0`, `pytest-asyncio>=0.21.0`.
- **Files Affected**: `requirements.txt` (new file)
- **Verification**: `pip install -r requirements.txt` / Docker stage 2 succeeds.

### Issue REM-02: Missing `scripts/entrypoint.sh`
- **Defect**: Container startup fails because the executable entrypoint script is absent.
- **Root Cause**: Entrypoint script referenced in `Dockerfile` was never created.
- **Remediation**:
  1. Create `scripts/entrypoint.sh` with bash shebang, environment variable verification, database connectivity wait-loop, and exec command to launch Uvicorn:
     `exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${API_PORT:-8000}`.
  2. Grant executable permissions (`chmod +x scripts/entrypoint.sh`).
- **Files Affected**: `scripts/entrypoint.sh` (new file)
- **Verification**: `docker build` completes stage 4 without file copy errors.

### Issue REM-03: Missing `scripts/init-db.sql`
- **Defect**: PostgreSQL service attempts to mount non-existent `./scripts/init-db.sql`.
- **Root Cause**: Database initialization SQL schema was omitted.
- **Remediation**:
  1. Create `scripts/init-db.sql` defining baseline schema (`api_keys`, `generations_log`, `conversations`).
- **Files Affected**: `scripts/init-db.sql` (new file)
- **Verification**: PostgreSQL starts cleanly and creates initial tables.

### Issue REM-04: Strict GPU Reservation Breaks Local Execution
- **Defect**: `docker-compose.yml` mandates NVIDIA GPU hardware, preventing local testing when GPUs are unavailable.
- **Root Cause**: Deployment configuration assumed dedicated cloud GPU instances only.
- **Remediation**:
  1. Add a Compose profile or override configuration (`docker-compose.override.yml`) allowing CPU fallback or mock serving for local functional verification.
  2. Document running on cloud GPU instances (RunPod/Lambda) for full vLLM performance testing.
- **Files Affected**: `docker-compose.yml`, `docker-compose.override.yml`
- **Verification**: `docker compose up` starts without device reservation failure on standard local machines.

### Issue REM-05: Heavy Default Model Footprint (Mistral-7B)
- **Defect**: Downloading Mistral-7B weights (15 GB) on container startup causes extreme memory pressure and download timeouts.
- **Root Cause**: Production model identifier configured as the default for initial testing.
- **Remediation**:
  1. Support configuring a lightweight test model (e.g., `Qwen/Qwen2.5-0.5B-Instruct` or mock test mode) in `.env` for local validation.
  2. Reserve `Mistral-7B-Instruct-v0.2` for cloud GPU instances with attached persistent volumes.
- **Files Affected**: `.env.example`, `.env`, `src/llm/config.py`
- **Verification**: Model server loads in <30 seconds in local dev mode.

### Issue REM-06: Milvus Multi-Container Topology Overhead
- **Defect**: Running `etcd`, `minio`, and `milvus-standalone` requires >8 GB RAM.
- **Root Cause**: Production cluster architecture used for early developer iterations.
- **Remediation**:
  1. Provide a lightweight local option (e.g. ChromaDB or in-memory vector index) enabled via `VECTOR_DB_TYPE=chroma` or `mock`.
  2. Retain full Milvus stack for cloud GPU deployment.
- **Files Affected**: `docker-compose.yml`, `src/rag/retriever.py`
- **Verification**: Developer stack launches with <4 GB total RAM footprint.

### Issue REM-07: Uninitialized Environment Configuration (`.env`)
- **Defect**: No active `.env` file exists in the directory.
- **Root Cause**: Only `.env.example` was committed.
- **Remediation**:
  1. Generate `.env` with default local testing settings, secure dummy API keys, and database passwords.
- **Files Affected**: `.env` (new file)
- **Verification**: Configuration loads without missing environment variable warnings.

### Issue REM-08: Prometheus Scrape Target Misalignment
- **Defect**: `prometheus.yml` relies on Kubernetes discovery, failing inside Docker Compose.
- **Root Cause**: Kubernetes manifest configurations were copied to Docker Compose monitoring.
- **Remediation**:
  1. Add static scrape targets for `llm-server:8001` (metrics port) in `monitoring/prometheus/prometheus.yml`.
- **Files Affected**: `monitoring/prometheus/prometheus.yml`
- **Verification**: Prometheus UI at `http://localhost:9090/targets` displays `llm-server` with state `UP`.

### Issue REM-09: Unimplemented Application Stubs and Skipped Tests
- **Defect**: Application routes and tests are placeholders (`pass` / `TODO`).
- **Root Cause**: Scaffold generated ahead of functional implementation.
- **Remediation**:
  1. Implement concrete `/health` and `/generate` handlers in `src/api/main.py`.
  2. Implement active pytest cases in `tests/test_api.py`.
- **Files Affected**: `src/api/main.py`, `src/api/models.py`, `tests/test_api.py`
- **Verification**: `pytest tests/ -v` passes with 0 errors.

---

## 4. Implementation Tracker & Task Board

### 4.1 Master Task Board
| Task ID | Workstream | Item / Description | Priority | Severity | Status | Dependencies | Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TRK-01** | Build Prep | Author `requirements.txt` with pinned dependencies | P0 | Blocker | `PENDING` | None | Root |
| **TRK-02** | Build Prep | Create `scripts/entrypoint.sh` with Uvicorn launcher | P0 | Blocker | `PENDING` | TRK-01 | Scripts |
| **TRK-03** | Build Prep | Create `scripts/init-db.sql` with relational schemas | P0 | Blocker | `PENDING` | None | Scripts |
| **TRK-04** | Config | Generate `.env` from `.env.example` with local defaults | P0 | High | `PENDING` | None | Root |
| **TRK-05** | Compose | Create `docker-compose.override.yml` for CPU/mock fallback | P1 | High | `PENDING` | TRK-04 | Docker |
| **TRK-06** | Core App | Implement Pydantic request/response schemas in `models.py` | P1 | High | `PENDING` | TRK-01 | API |
| **TRK-07** | Core App | Implement Lifespan manager, `/health`, and `/metrics` in `main.py`| P0 | Blocker | `PENDING` | TRK-06 | API |
| **TRK-08** | Core App | Implement inference wrapper with mock/CPU fallback in `server.py`| P1 | High | `PENDING` | TRK-06 | LLM Server |
| **TRK-09** | Monitoring | Add static scrape target for `llm-server:8001` in `prometheus.yml`| P2 | Medium | `PENDING` | TRK-07 | Prometheus |
| **TRK-10** | Testing | Implement active test cases in `tests/test_api.py` | P1 | High | `PENDING` | TRK-07 | Pytest |
| **TRK-11** | Local Run | Build and launch local container stack via Docker Compose | P0 | Blocker | `PENDING` | TRK-01 to TRK-09 | Local Docker |
| **TRK-12** | Local Run | Execute local health and inference smoke tests | P1 | High | `PENDING` | TRK-11 | Smoke Test |
| **TRK-13** | Cloud Prep | Commit all fixed assets and push to remote Git branch | P0 | Blocker | `PENDING` | TRK-12 | Git |
| **TRK-14** | Cloud GPU | Provision 1x NVIDIA A10G/4090 instance (RunPod/Lambda) | P0 | Blocker | `PENDING` | TRK-13 | Cloud GPU |
| **TRK-15** | Cloud GPU | Clone repository and deploy full GPU vLLM stack | P0 | Blocker | `PENDING` | TRK-14 | Cloud GPU |
| **TRK-16** | Cloud GPU | Establish SSH tunnel for local UI access (`:8000`, `:3000`, `:9090`)| P1 | High | `PENDING` | TRK-15 | SSH |
| **TRK-17** | Cloud GPU | Run performance benchmarks (`scripts/benchmark.sh`) | P1 | High | `PENDING` | TRK-16 | Benchmark |
| **TRK-18** | Teardown | Stop/terminate cloud GPU instance and verify zero idle cost | P0 | Blocker | `PENDING` | TRK-17 | Cost Mgmt |

### 4.2 Milestone Progress Checklist
- [ ] **Milestone 1: Build & Config Prerequisites Ready** (TRK-01 to TRK-04)
- [ ] **Milestone 2: Application Stubs & Schemas Functional** (TRK-06 to TRK-08)
- [ ] **Milestone 3: Local Compose & Monitoring Verified** (TRK-05, TRK-09, TRK-11, TRK-12)
- [ ] **Milestone 4: Test Suite Passing** (TRK-10)
- [ ] **Milestone 5: Cloud GPU Deployment & Benchmarks** (TRK-13 to TRK-17)
- [ ] **Milestone 6: Cloud Teardown & Final Evaluation** (TRK-18)

---

## 5. Deployment & Execution Runbooks

### 5.1 Local Execution Runbook (CPU / Mock Mode)
1. **Prepare Environment**:
   ```powershell
   Copy-Item .env.example .env
   ```
2. **Build Local Images**:
   ```powershell
   docker compose build
   ```
3. **Start Auxiliary Infrastructure**:
   ```powershell
   docker compose up -d redis postgres
   ```
4. **Start Application & Monitoring**:
   ```powershell
   docker compose up -d llm-server prometheus grafana
   ```
5. **Verify Local Endpoints**:
   ```bash
   curl -s http://localhost:8000/health
   curl -s http://localhost:8001/metrics
   ```

### 5.2 Cloud GPU Rental Runbook (Full vLLM Stack)
Refer to [CLOUD_GPU_RENTAL_PLAN.md](docs/CLOUD_GPU_RENTAL_PLAN.md) for full pricing and provider specifications:
1. **Provision Instance**: RunPod or Lambda Labs 1x NVIDIA A10G (24 GB) or RTX 4090 (24 GB) with 80 GB NVMe SSD.
2. **Launch Remote Stack**:
   ```bash
   git clone <REPO_URL>
   cd ai-infra-engineer-learning/projects/project-103-llm-deployment
   docker compose up -d
   ```
3. **SSH Local Tunneling**:
   ```bash
   ssh -N -L 8000:localhost:8000 -L 3000:localhost:3000 -L 9090:localhost:9090 root@<CLOUD_IP> -p <PORT>
   ```
4. **Access in Local Browser**:
   - Swagger API: `http://localhost:8000/docs`
   - Grafana Dashboard: `http://localhost:3000`
   - Prometheus Targets: `http://localhost:9090/targets`

---

## 6. Success Verification Matrix

| Validation Criteria | Target Metric | How to Verify |
| :--- | :--- | :--- |
| **Docker Build** | Exit code 0 | `docker compose build` completes without layer errors |
| **Container Health** | All containers `healthy` | `docker compose ps` displays status `Up (healthy)` |
| **API Health Probe** | HTTP 200 | `curl http://localhost:8000/health` returns `{"status": "healthy"}` |
| **Inference Generation** | TTFT < 1s, HTTP 200 | `POST /generate` returns valid completion token stream |
| **Metrics Pipeline** | Scrape state `UP` | Prometheus `http://localhost:9090/targets` shows `llm-server:8001` UP |
| **Test Suite** | 100% tests passing | `pytest tests/ -v` completes with 0 errors and 0 skips |
| **Cost Control** | $0 idle cost | Cloud GPU instance verified stopped/deleted after testing |
