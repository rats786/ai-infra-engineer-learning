# MLOps Pipeline Implementation Tracker

**Target Project:** `C:\repos\ai-infra-engineer-learning\projects\project-102-mlops-pipeline`  
**Associated Remediation Plan:** [REMEDIATION_PLAN.md](REMEDIATION_PLAN.md)  
**Main Review Document:** [LOCAL_DEPLOYMENT_REVIEW_AND_PLAN.md](../LOCAL_DEPLOYMENT_REVIEW_AND_PLAN.md)  
**Last Updated:** November 2026  

---

## 1. Executive Status Dashboard

| Metric | Value |
| :--- | :--- |
| **Total Tasks** | 18 |
| **Completed** | 3 |
| **In Progress** | 0 |
| **Pending** | 15 |
| **Current Project Phase** | Phase 1: Environment & Config Preparation |
| **Overall Completion** | 17% |

---

## 2. Master Task Board

| Task ID | Workstream | Item / Description | Priority | Severity | Status | Dependencies | Owner / Target |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TRK-01** | Infrastructure | Generate `.env` with valid Fernet & Webserver secret keys | P0 | Blocker | `PENDING - USER ACTION` | None | Local Env |
| **TRK-02** | Infrastructure | Create pre-requisite host directories (`data/`, `models/`, `logs/`, `plugins/`) | P0 | High | `CODE COMPLETE` | None | Filesystem |
| **TRK-03** | Infrastructure | Add `minio-create-bucket` init container in `docker-compose.yml` | P0 | Blocker | `CODE COMPLETE` | TRK-01 | Docker Compose |
| **TRK-04** | Infrastructure | Optimize `requirements.txt` to avoid heavy Torch build in Airflow | P1 | High | `CODE COMPLETE` | None | Airflow Image |
| **TRK-05** | Core ML | Implement data ingestion & validation in `src/data/` | P1 | High | `PENDING` | TRK-02 | Pipeline |
| **TRK-06** | Core ML | Implement preprocessing pipeline in `src/data/preprocessing.py` | P1 | High | `PENDING` | TRK-05 | Pipeline |
| **TRK-07** | Core ML | Implement scikit-learn model trainer with MLflow logging | P1 | High | `PENDING` | TRK-06 | Pipeline |
| **TRK-08** | Core ML | Implement model evaluation & metrics export in `src/training/` | P1 | Medium | `PENDING` | TRK-07 | Pipeline |
| **TRK-09** | Orchestration | Wire `dags/data_pipeline.py` to functional `src/data/` modules | P1 | High | `PENDING` | TRK-05, TRK-06 | Airflow |
| **TRK-10** | Orchestration | Wire `dags/training_pipeline.py` to functional `src/training/` | P1 | High | `PENDING` | TRK-07, TRK-08 | Airflow |
| **TRK-11** | Serving | Build FastAPI model serving app (`src/deployment/server.py`) | P0 | Blocker | `PENDING` | TRK-07 | Model Server |
| **TRK-12** | Serving | Create `Dockerfile.model-server` and add service to compose | P0 | Blocker | `PENDING` | TRK-11 | Docker Compose |
| **TRK-13** | Monitoring | Add `model-server:8000` static scrape target in `prometheus.yml` | P2 | Medium | `PENDING` | TRK-12 | Prometheus |
| **TRK-14** | Testing | Implement active test cases in `tests/test_data.py` | P2 | Medium | `PENDING` | TRK-05, TRK-06 | Pytest |
| **TRK-15** | Testing | Implement active test cases in `tests/test_training.py` | P2 | Medium | `PENDING` | TRK-07, TRK-08 | Pytest |
| **TRK-16** | Testing | Implement active test cases in `tests/test_deployment.py` | P2 | Medium | `PENDING` | TRK-11 | Pytest |
| **TRK-17** | Verification | Run end-to-end Docker Compose launch and UI smoke tests | P0 | Blocker | `PENDING` | TRK-01 to TRK-13| Integration |
| **TRK-18** | Verification | Run inference curl requests and confirm Prometheus/Grafana graphs | P1 | High | `PENDING` | TRK-17 | Monitoring |

---

## 3. Milestone Progress Checklist

### Milestone 1: Environment & Config Readiness
- [ ] **TRK-01**: Generate the local ignored `.env` file with Fernet and webserver secret keys.
- [x] **TRK-02**: Track required host volume directories (`data/raw`, `data/processed`, `models`, `logs`, `plugins`) with `.gitkeep` files.
- [x] **TRK-03**: Configure the health-gated `minio-create-bucket` service and make MLflow wait for successful bucket creation.
- [x] **TRK-04**: Keep Airflow dependencies lightweight and separate optional/development dependencies.

### Milestone 2: Functional Pipeline Logic
- [ ] **TRK-05**: Implement dataset ingestion in `src/data/ingestion.py` and schema checks in `src/data/validation.py`.
- [ ] **TRK-06**: Implement preprocessing transformations, imputation, scaling, and train/test splits in `src/data/preprocessing.py`.
- [ ] **TRK-07**: Implement scikit-learn model training with MLflow parameter, metric, and artifact logging in `src/training/train.py`.
- [ ] **TRK-08**: Implement model evaluation metrics (`accuracy`, `f1_score`, confusion matrix) in `src/training/evaluate.py`.

### Milestone 3: Airflow DAG Integration
- [ ] **TRK-09**: Refactor `dags/data_pipeline.py` to trigger `src.data` operations and save processed files.
- [ ] **TRK-10**: Refactor `dags/training_pipeline.py` to trigger `src.training` and promote models in MLflow Model Registry.

### Milestone 4: Containerized Model Serving
- [ ] **TRK-11**: Implement FastAPI serving application (`src/deployment/server.py`) with `/health`, `/predict`, and `/metrics` endpoints.
- [ ] **TRK-12**: Create `Dockerfile.model-server` and add `model-server` service into `docker-compose.yml`.

### Milestone 5: Observability & Scrape Wiring
- [ ] **TRK-13**: Add static scrape target for `model-server:8000` in `monitoring/prometheus/prometheus.yml`.

### Milestone 6: Automated Test Suite
- [ ] **TRK-14**: Implement data pipeline unit tests in `tests/test_data.py`.
- [ ] **TRK-15**: Implement model training unit tests in `tests/test_training.py`.
- [ ] **TRK-16**: Implement model serving API unit tests in `tests/test_deployment.py`.
- [ ] Run `pytest tests/ -v` and confirm 100% pass rate.

### Milestone 7: Local System Verification
- [ ] **TRK-17**: Bring up all containers using `docker-compose up -d` and verify all endpoints (`:8080`, `:5000`, `:9001`, `:8000`, `:9090`, `:3000`).
- [ ] **TRK-18**: Execute sample inference via `curl`, trigger Airflow DAGs, and verify Grafana metric visualization.

---

## 4. Change Log & Audit History

| Date | Phase | Action / Update | Modified By |
| :--- | :--- | :--- | :--- |
| Nov 2026 | Initialization | Initialized Master Task Board with 18 tasks across 7 milestones | Antigravity |
| Nov 2026 | Documentation | Separated tracker and remediation into dedicated `planning/` folder | Antigravity |
| 25 Nov 2026 | Phase 1 | Completed directory, MinIO bootstrap, and dependency configuration; local `.env` generation remains a user-run step | Copilot |
