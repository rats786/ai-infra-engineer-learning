# Project 103: LLM Deployment Remediation Tracker

This tracker monitors the step-by-step resolution of build blockers, infrastructure gaps, and deployment readiness for both local testing and cloud GPU rental.

---

## 1. Quick Status Overview

| Workstream | Items | Complete | In Progress | Pending |
| :--- | :---: | :---: | :---: | :---: |
| **Build Assets & Prerequisites** | 4 | 0 | 0 | 4 |
| **Application & Code Stubs** | 3 | 0 | 0 | 3 |
| **Local Compose & Observability** | 3 | 0 | 0 | 3 |
| **Testing & Quality Assurance** | 2 | 0 | 0 | 2 |
| **Cloud GPU Deployment & Testing** | 5 | 0 | 0 | 5 |
| **Cost Management & Teardown** | 1 | 0 | 0 | 1 |
| **TOTAL** | **18** | **0** | **0** | **18** |

---

## 2. Master Implementation Tracker

| Task ID | Item | Priority | Severity | Status | Dependencies | Owner / Target File |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **TRK-01** | Create `requirements.txt` with pinned dependencies | P0 | Blocker | `PENDING` | None | `requirements.txt` |
| **TRK-02** | Create `scripts/entrypoint.sh` with Uvicorn launcher | P0 | Blocker | `PENDING` | TRK-01 | `scripts/entrypoint.sh` |
| **TRK-03** | Create `scripts/init-db.sql` with schema definitions | P0 | Blocker | `PENDING` | None | `scripts/init-db.sql` |
| **TRK-04** | Generate `.env` from `.env.example` with local defaults | P0 | High | `PENDING` | None | `.env` |
| **TRK-05** | Add `docker-compose.override.yml` for CPU/mock fallback | P1 | High | `PENDING` | TRK-04 | `docker-compose.override.yml` |
| **TRK-06** | Complete Pydantic schemas in `src/api/models.py` | P1 | High | `PENDING` | TRK-01 | `src/api/models.py` |
| **TRK-07** | Implement lifespan, `/health`, and `/metrics` in `main.py` | P0 | Blocker | `PENDING` | TRK-06 | `src/api/main.py` |
| **TRK-08** | Implement inference wrapper with mock/CPU fallback | P1 | High | `PENDING` | TRK-06 | `src/llm/server.py` |
| **TRK-09** | Add static scrape target for `llm-server:8001` in Prometheus | P2 | Medium | `PENDING` | TRK-07 | `monitoring/prometheus/prometheus.yml` |
| **TRK-10** | Implement active test cases in `tests/test_api.py` | P1 | High | `PENDING` | TRK-07 | `tests/test_api.py` |
| **TRK-11** | Build and start local container stack via Docker Compose | P0 | Blocker | `PENDING` | TRK-01 to TRK-09 | Local Docker |
| **TRK-12** | Execute local health and inference smoke checks | P1 | High | `PENDING` | TRK-11 | Local Shell |
| **TRK-13** | Commit all resolved assets and push to remote Git branch | P0 | Blocker | `PENDING` | TRK-12 | Git |
| **TRK-14** | Provision 1x NVIDIA A10G/4090 instance on RunPod/Lambda | P0 | Blocker | `PENDING` | TRK-13 | Cloud GPU Console |
| **TRK-15** | Deploy full GPU stack with vLLM on remote cloud instance | P0 | Blocker | `PENDING` | TRK-14 | Remote Docker Compose |
| **TRK-16** | Setup SSH tunnel for local UI access (`:8000`, `:3000`, `:9090`) | P1 | High | `PENDING` | TRK-15 | SSH Tunnel |
| **TRK-17** | Run performance benchmarks (`scripts/benchmark.sh`) | P1 | High | `PENDING` | TRK-16 | Remote Shell |
| **TRK-18** | Terminate cloud GPU instance and verify zero idle charges | P0 | Blocker | `PENDING` | TRK-17 | Cost Management |

---

## 3. Milestone Checkpoints

- [ ] **Milestone 1: Build Assets Ready** (TRK-01 to TRK-04)
- [ ] **Milestone 2: Application Code Functional** (TRK-06 to TRK-08)
- [ ] **Milestone 3: Local Smoke Verification** (TRK-05, TRK-09, TRK-11, TRK-12)
- [ ] **Milestone 4: Test Suite Green** (TRK-10)
- [ ] **Milestone 5: Cloud GPU Deployment & Benchmarks** (TRK-13 to TRK-17)
- [ ] **Milestone 6: Clean Teardown** (TRK-18)
