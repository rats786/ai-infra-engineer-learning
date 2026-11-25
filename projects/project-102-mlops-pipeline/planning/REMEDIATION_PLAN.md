# MLOps Pipeline Remediation Plan

**Target Project:** `C:\repos\ai-infra-engineer-learning\projects\project-102-mlops-pipeline`  
**Associated Tracker:** [TRACKER.md](TRACKER.md)  
**Main Review:** [LOCAL_DEPLOYMENT_REVIEW_AND_PLAN.md](../LOCAL_DEPLOYMENT_REVIEW_AND_PLAN.md)  
**Status:** Approved for Implementation  
**Target Environment:** Local Docker Compose

---

## 1. Remediation Strategy Overview

This document specifies the technical remediation procedures for all structural, code, and infrastructure defects identified during the review of `project-102-mlops-pipeline`.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        REMEDIATION WORKSTREAMS                         │
├─────────────────┬──────────────────┬─────────────────┬────────────────┤
│ 1. INFRASTRUCTURE│ 2. PIPELINE CORE │ 3. SERVING & API│ 4. TEST & OBS  │
│ - MinIO Buckets │ - Data Ingestion │ - FastAPI App   │ - Unskip Tests │
│ - Slim Airflow  │ - Preprocessing  │ - MLflow Client │ - Scrape Config│
│ - Fernet / .env │ - Model Trainer  │ - Health Probes │ - Grafana View │
│ - Compose Mounts│ - Wire DAG Tasks │ - Port 8000     │ - Pass Rate 100│
└─────────────────┴──────────────────┴─────────────────┴────────────────┘
```

---

## 2. Detailed Remediation Items

### REM-01: MinIO Bucket Auto-Creation
- **Issue**: MLflow server launches with `--default-artifact-root s3://mlflow-artifacts/`, but MinIO initializes empty. Artifact logging fails with `404 NoSuchBucket`.
- **Root Cause**: MinIO lacks automatic bucket creation on startup.
- **Affected Files**: `docker-compose.yml`
- **Technical Fix**:
  Add an init container `minio-create-bucket` in `docker-compose.yml` using `minio/mc`:
  ```yaml
  minio-create-bucket:
    image: minio/mc:latest
    depends_on:
      minio:
        condition: service_healthy
    entrypoint: >
      /bin/sh -c "
      /usr/bin/mc alias set local http://minio:9000 minioadmin minioadmin;
      /usr/bin/mc mb --ignore-existing local/mlflow-artifacts;
      exit 0;
      "
    networks:
      - mlops-network
  ```
- **Verification**:
  `docker-compose up minio-create-bucket` exits with code 0; bucket `mlflow-artifacts` is visible in MinIO Console at `http://localhost:9001`.

---

### REM-02: Airflow Docker Image Dependency Optimization
- **Issue**: Installing `torch`, `torchvision`, `great-expectations`, and `dvc` in `Dockerfile.airflow` inflates image size to over 5GB and causes build timeouts or constraint conflicts.
- **Root Cause**: `requirements.txt` bundles heavy deep learning libraries not required for the initial scikit-learn tabular pipeline.
- **Affected Files**: `requirements.txt`, `Dockerfile.airflow`, `requirements-optional.txt` (new)
- **Technical Fix**:
  1. Move deep learning frameworks to `requirements-optional.txt`.
  2. Keep `requirements.txt` scoped to tabular MLOps:
     ```text
     numpy>=1.24.0
     pandas>=2.0.0
     scikit-learn>=1.3.0
     mlflow>=2.10.0
     fastapi>=0.109.0
     uvicorn[standard]>=0.27.0
     pydantic>=2.5.0
     sqlalchemy>=2.0.0
     psycopg2-binary>=2.9.0
     boto3>=1.34.0
     prometheus-client>=0.19.0
     pytest>=8.0.0
     requests>=2.31.0
     python-dotenv>=1.0.0
     ```
- **Verification**:
  `docker-compose build airflow-webserver` finishes in under 3 minutes with zero dependency resolution errors.

---

### REM-03: Local Containerized Model Serving Service
- **Issue**: Model deployment targets Kubernetes manifests only, with no local container for serving predictions under Docker Compose.
- **Root Cause**: Absence of a local model server definition in `docker-compose.yml`.
- **Affected Files**: `src/deployment/server.py` (new), `Dockerfile.model-server` (new), `docker-compose.yml`
- **Technical Fix**:
  1. Create `src/deployment/server.py` using FastAPI:
     - `GET /health`: Liveness and readiness probe.
     - `POST /predict`: Accepts feature JSON, runs inference using the model, returns predictions.
     - `GET /metrics`: Exports Prometheus metrics.
  2. Create `Dockerfile.model-server`:
     ```dockerfile
     FROM python:3.9-slim
     WORKDIR /app
     COPY requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     COPY src/ /app/src/
     ENV PYTHONPATH="/app"
     EXPOSE 8000
     CMD ["uvicorn", "src.deployment.server:app", "--host", "0.0.0.0", "--port", "8000"]
     ```
  3. Add `model-server` service to `docker-compose.yml` on port `8000:8000`.
- **Verification**:
  `curl http://localhost:8000/health` returns `{"status": "healthy"}`.

---

### REM-04: Concrete Implementation of Core `src/` Modules
- **Issue**: Modules `src/data/ingestion.py`, `src/data/preprocessing.py`, `src/data/validation.py`, `src/training/train.py`, and `src/training/evaluate.py` raise `NotImplementedError`.
- **Root Cause**: Boilerplate stub code without business logic.
- **Affected Files**: `src/data/*.py`, `src/training/*.py`
- **Technical Fix**:
  1. `src/data/ingestion.py`: Implement `CSVDataSource` that fetches or generates a standard dataset (e.g., California Housing or Breast Cancer) and writes to `data/raw/data.csv`.
  2. `src/data/preprocessing.py`: Implement `DataPreprocessor` to perform `StandardScaler` transformations, categorical imputation, and export train/validation/test splits to `data/processed/`.
  3. `src/data/validation.py`: Implement schema checks (column presence, null thresholds).
  4. `src/training/train.py`: Implement `ModelTrainer.train()` using `RandomForestClassifier` with MLflow tracking (`mlflow.log_params`, `mlflow.log_metrics`, `mlflow.sklearn.log_model`).
  5. `src/training/evaluate.py`: Implement `ModelEvaluator.evaluate_classification()` computing accuracy, precision, recall, and F1.
- **Verification**:
  Running `python -m src.training.train` executes training and successfully logs run artifacts to MLflow.

---

### REM-05: Airflow DAG Wiring to Package Modules
- **Issue**: Airflow DAGs (`dags/data_pipeline.py`, `dags/training_pipeline.py`) use hardcoded mock matrices instead of calling `src/` functions.
- **Root Cause**: Scaffolding separated DAG definition from package code.
- **Affected Files**: `dags/data_pipeline.py`, `dags/training_pipeline.py`
- **Technical Fix**:
  1. Refactor `dags/data_pipeline.py` tasks to import and invoke `src.data.ingestion` and `src.data.preprocessing`.
  2. Refactor `dags/training_pipeline.py` tasks to invoke `src.training.train.ModelTrainer`.
  3. Enable model registration and transition to `Production` stage upon meeting threshold criteria (`val_accuracy >= 0.85`).
- **Verification**:
  Triggering `data_pipeline` and `training_pipeline` DAGs in Airflow completes with state `success`.

---

### REM-06: Activation and Implementation of Unit Tests
- **Issue**: All tests in `tests/test_data.py`, `tests/test_training.py`, and `tests/test_deployment.py` call `self.skipTest(...)`.
- **Root Cause**: Tests were scaffolded before logic was built.
- **Affected Files**: `tests/test_data.py`, `tests/test_training.py`, `tests/test_deployment.py`
- **Technical Fix**:
  1. `tests/test_data.py`: Add test cases for CSV ingestion and preprocessor scaling.
  2. `tests/test_training.py`: Add test cases for model training output and metric ranges.
  3. `tests/test_deployment.py`: Add test cases for FastAPI predict and health endpoints.
  4. Remove `self.skipTest(...)` statements.
- **Verification**:
  `pytest tests/ -v` passes 100% of tests.

---

### REM-07: Environment Configuration Initialization
- **Issue**: No `.env` file exists; `AIRFLOW__CORE__FERNET_KEY` is blank in `docker-compose.yml`.
- **Root Cause**: Deployment configuration omitted active `.env` generation.
- **Affected Files**: `.env` (new file)
- **Technical Fix**:
  1. Create `.env` from `.env.example`.
  2. Populate generated base64 32-byte Fernet key:
     ```bash
     python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
     ```
  3. Set `AIRFLOW__CORE__FERNET_KEY` and `AIRFLOW__WEBSERVER__SECRET_KEY`.
- **Verification**:
  Airflow containers start without Fernet or secret key warnings in logs.

---

### REM-08: Local Prometheus Scrape Configuration
- **Issue**: `monitoring/prometheus/prometheus.yml` relies on Kubernetes service discovery, failing to scrape metrics under local Docker Compose.
- **Root Cause**: Monitoring setup targeted Kubernetes exclusively.
- **Affected Files**: `monitoring/prometheus/prometheus.yml`
- **Technical Fix**:
  Add a static scrape target for the local model server:
  ```yaml
  - job_name: 'model-server'
    static_configs:
      - targets: ['model-server:8000']
    metrics_path: '/metrics'
  ```
- **Verification**:
  `http://localhost:9090/targets` displays `model-server` with state `UP`.

---

## 3. Risk Mitigation & Rollback Strategy

| Remediation | Potential Risk | Mitigation / Rollback |
| :--- | :--- | :--- |
| **REM-01 (MinIO Init)** | `mc` container fails if MinIO is slow to boot | Healthcheck dependency `condition: service_healthy` ensures MinIO is ready before `mc` runs. |
| **REM-02 (Requirements)**| Missing deep learning dependencies | Optional packages are isolated in `requirements-optional.txt` and installable on demand. |
| **REM-03 (Model Server)**| Port 8000 conflict on host | Port mapping can be modified in `.env` (`MODEL_SERVING_PORT=8001`). |
| **REM-05 (Airflow DAGs)**| Python path resolution error in container | `PYTHONPATH=/opt/airflow/src` is set in `Dockerfile.airflow`. |
