# Project 102 MLOps Pipeline: Comprehensive Review & Local Deployment Plan

**Target Project:** `C:\repos\ai-infra-engineer-learning\projects\project-102-mlops-pipeline`  
**Review Date:** November 2026  
**Document Purpose:** Review codebase state, identify gaps, and outline a realistic, step-by-step plan for local deployment and testing using Docker Compose.

> [!NOTE]
> The detailed defect remediation guides and the interactive implementation tracker have been separated into dedicated documents in the [`planning/`](planning/) folder:
> - **Remediation Plan:** [REMEDIATION_PLAN.md](planning/REMEDIATION_PLAN.md)
> - **Implementation Tracker:** [TRACKER.md](planning/TRACKER.md)

---

## 1. Executive Summary

`project-102-mlops-pipeline` provides an architectural blueprint for an end-to-end MLOps pipeline covering data ingestion, data validation, experiment tracking with MLflow, workflow orchestration with Apache Airflow, deployment automation, and monitoring via Prometheus and Grafana.

**Current State:**
- The repository is currently a **scaffolding/stub project**.
- Nearly all implementation modules in `src/` (`data/`, `training/`, `deployment/`, `monitoring/`) raise `NotImplementedError` or contain commented-out sample snippets.
- Airflow DAGs in `dags/` contain minimal inline mock data and synthetic tasks.
- All unit tests in `tests/` are skipped (`self.skipTest(...)`).
- `docker-compose.yml` configures 9 infrastructure services (PostgreSQL, Redis, MinIO, MLflow, Airflow Webserver, Airflow Scheduler, Airflow Init, Prometheus, Grafana), but contains operational gaps that prevent a smooth out-of-the-box local deployment.

---

## 2. Detailed Component Review & Gap Analysis

### 2.1 Core Source Code (`src/`)
| Module | Current State | Missing Requirements / Gaps |
| :--- | :--- | :--- |
| `src/data/ingestion.py` | Abstract classes defined; methods raise `NotImplementedError`. | Needs concrete dataset ingestion logic (e.g. CSV/synthetic dataset) that saves to `data/raw`. |
| `src/data/preprocessing.py` | Methods raise `NotImplementedError`. | Needs scikit-learn preprocessing pipeline (handling missing values, train/val/test split, scaler persistence). |
| `src/data/validation.py` | Methods raise `NotImplementedError`. | Needs lightweight schema and range validation (using Pandera or Great Expectations). |
| `src/training/train.py` | Methods raise `NotImplementedError`. | Needs scikit-learn model training (e.g., RandomForest/LogisticRegression) with parameter and metric logging to MLflow. |
| `src/training/evaluate.py` | Methods raise `NotImplementedError`. | Needs classification metrics calculation (Accuracy, F1, Precision, Recall, Confusion Matrix) and MLflow logging. |
| `src/deployment/deploy.py` | Methods raise `NotImplementedError`. | Needs logic to pull registered models from MLflow Model Registry for serving. |
| `src/monitoring/health.py` | Return `UNKNOWN` or `NotImplemented`. | Needs health checks for PostgreSQL, MLflow, Airflow, and the model server. |
| `src/monitoring/metrics.py` | Methods empty; collectors uninitialized. | Needs Prometheus metrics (`Counter`, `Histogram`) for inference latency and throughput. |

### 2.2 Orchestration (`dags/`)
- **`data_pipeline.py`**: Operates on a hardcoded 5-row synthetic DataFrame; does not invoke `src.data` modules. Uses a mock DVC MD5 hash rather than running real DVC or file versioning.
- **`training_pipeline.py`**: Trains on 3 hardcoded coordinates; model registry registration is commented out.
- **`deployment_pipeline.py`**: Completely simulates Docker image builds and Kubernetes rollouts using `time.sleep(2)` and mock dictionaries.

### 2.3 Docker Compose & Infrastructure (`docker-compose.yml`, `Dockerfile.airflow`)
1. **MinIO Bucket Auto-Creation Missing**:
   - MLflow server startup points to `s3://mlflow-artifacts/`.
   - MinIO container starts empty with no buckets. When MLflow or DVC attempts to store artifacts, S3 requests fail with `NoSuchBucket`.
   - *Resolution:* Add a transient `create-buckets` init service in Docker Compose using `minio/mc` (details in [REMEDIATION_PLAN.md](planning/REMEDIATION_PLAN.md#rem-01-minio-bucket-auto-creation)).
2. **`Dockerfile.airflow` & Dependency Bloat**:
   - `Dockerfile.airflow` runs `pip install -r requirements.txt`.
   - `requirements.txt` includes large libraries (`torch>=2.0.0`, `torchvision>=0.15.0`, `great-expectations`, `dvc`, etc.).
   - Building this inside Airflow 2.8.0 takes significant time, produces multi-gigabyte images, and risks dependency conflicts with Airflow constraints.
   - *Resolution:* Optimize `requirements.txt` for the core tabular ML stack (details in [REMEDIATION_PLAN.md](planning/REMEDIATION_PLAN.md#rem-02-airflow-docker-image-dependency-optimization)).
3. **No Local Model Serving Container**:
   - The project includes Kubernetes manifests (`kubernetes/model-deployment.yaml`) but does **not** include a container in `docker-compose.yml` for serving the model locally.
   - For complete local testing without a live Kubernetes cluster, an inference service (e.g. FastAPI app) should run directly inside Docker Compose on port 8000.
   - *Resolution:* Implement FastAPI service and Dockerfile (details in [REMEDIATION_PLAN.md](planning/REMEDIATION_PLAN.md#rem-03-local-containerized-model-serving-service)).
4. **Airflow Fernet Key and Secrets**:
   - `AIRFLOW__CORE__FERNET_KEY` is currently blank (`''`) in `docker-compose.yml`. Generating a static key in `.env` avoids Airflow encryption warnings and database issues.
5. **Volume Mounts on Windows**:
   - Directories `./logs`, `./plugins`, `./data`, `./models` are bind-mounted. These folders must exist before container startup to avoid permission anomalies.

### 2.4 Tests (`tests/`)
- `tests/test_data.py`, `tests/test_training.py`, and `tests/test_deployment.py` have test methods marked with `self.skipTest(...)`. No automated test suite runs during CI or local checks.

---

## 3. Plan for Local Deployment and Testing

To achieve a working, testable local deployment using Docker Compose, execute the following phased plan:

```
[Phase 1: Environment & Compose Config]
           │
           ▼
[Phase 2: Minimal Core Pipeline Implementation (src/)]
           │
           ▼
[Phase 3: Local Model Server Service (FastAPI)]
           │
           ▼
[Phase 4: Docker Compose Launch & Integration Testing]
           │
           ▼
[Phase 5: Monitoring & Verification]
```

### Phase 1: Environment & Infrastructure Preparation
1. **Create Active `.env` File**:
   - Copy `.env.example` to `.env`.
   - Generate and configure a valid `AIRFLOW__CORE__FERNET_KEY` and `AIRFLOW__WEBSERVER__SECRET_KEY`.
   - Ensure local port mappings do not conflict with existing host services (Postgres 5432, Airflow 8080, MLflow 5000, MinIO 9000/9001, Prometheus 9090, Grafana 3000, Model Server 8000).
2. **Add MinIO Bucket Initialization to `docker-compose.yml`**:
   - Add a transient `create-buckets` service using `minio/mc`:
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
3. **Prune and Optimize `requirements.txt` for Local Airflow**:
   - For local tabular ML demonstrations, scikit-learn, pandas, numpy, and mlflow suffice; defer or separate heavy PyTorch dependencies to keep the Airflow image lightweight and build times fast.
4. **Ensure Host Mount Directories Exist**:
   - Create directories: `data/raw`, `data/processed`, `models`, `logs`, `plugins`.

### Phase 2: Implement Functional Pipeline Logic (`src/` and `dags/`)
1. **Data Ingestion & Preprocessing**:
   - Implement `CSVDataSource` in `src/data/ingestion.py` using a standard sample tabular dataset (e.g., California Housing or Breast Cancer dataset).
   - Implement `DataPreprocessor` in `src/data/preprocessing.py` to handle scaling, splitting, and saving `train.csv` and `test.csv`.
   - Implement basic schema check in `src/data/validation.py`.
2. **Model Training & MLflow Logging**:
   - Implement `ModelTrainer.train()` in `src/training/train.py` using `RandomForestClassifier`.
   - Log parameters (`n_estimators`, `max_depth`), metrics (`accuracy`, `f1_score`), and the scikit-learn model artifact to MLflow via `mlflow.sklearn.log_model(..., registered_model_name="mlops-model")`.
3. **Wire DAGs to `src` Modules**:
   - Update `dags/data_pipeline.py` and `dags/training_pipeline.py` to call the implemented `src` functions.
   - Configure model promotion in MLflow to the `Production` stage upon meeting threshold criteria (e.g. `accuracy >= 0.85`).

### Phase 3: Implement Local Model Serving
1. **Create FastAPI Model Serving Application (`src/deployment/server.py`)**:
   - Endpoints:
     - `GET /health`: Liveness/readiness probe.
     - `POST /predict`: Accepts feature JSON payload, returns predictions.
     - `GET /metrics`: Exports Prometheus metrics (prediction count, latency histogram).
   - Loads the latest production model directly from MLflow tracking server or shared `/opt/airflow/models`.
2. **Add `model-server` Service to `docker-compose.yml`**:
   - Expose port `8000:8000`.
   - Connect to `mlops-network`.
   - Update `monitoring/prometheus/prometheus.yml` to scrape `model-server:8000/metrics`.

### Phase 4: Local Deployment Execution
1. **Build and Launch Services**:
   ```powershell
   # 1. Initialize databases and users
   docker-compose up -d postgres redis minio minio-create-bucket
   docker-compose run --rm airflow-init

   # 2. Start tracking, pipeline, and monitoring services
   docker-compose up -d mlflow airflow-webserver airflow-scheduler prometheus grafana model-server
   ```
2. **Service Verification Endpoints**:
   - **Airflow Web UI**: `http://localhost:8080` (admin/admin or airflow/airflow)
   - **MLflow Tracking UI**: `http://localhost:5000`
   - **MinIO Console**: `http://localhost:9001` (minioadmin/minioadmin)
   - **Prometheus UI**: `http://localhost:9090`
   - **Grafana UI**: `http://localhost:3000` (admin/admin)
   - **Model Serving API**: `http://localhost:8000/docs`

### Phase 5: End-to-End Pipeline & Integration Testing
1. **Trigger Data Pipeline**:
   - Trigger `data_pipeline` DAG in Airflow; verify raw and processed data artifacts are generated.
2. **Trigger Training Pipeline**:
   - Trigger `training_pipeline` DAG; inspect MLflow UI at `http://localhost:5000` to verify logged metrics, parameters, and model artifacts in MinIO.
3. **Verify Model Serving**:
   - Send test inference request:
     ```bash
     curl -X POST "http://localhost:8000/predict" -H "Content-Type: application/json" -d "{\"features\": [1.0, 2.0, 3.0, 4.0]}"
     ```
4. **Validate Monitoring Metrics**:
   - Verify Prometheus targets (`http://localhost:9090/targets`) show `model-server` as UP.
   - Inspect preconfigured dashboard in Grafana (`http://localhost:3000`).
5. **Run Automated Unit Tests**:
   - Unskip tests in `tests/test_data.py` and `tests/test_training.py` and run:
     ```bash
     pytest tests/ -v
     ```

---

## 4. Success Verification Matrix

| Validation Criteria | Target Metric | How to Verify |
| :--- | :--- | :--- |
| **Container Health** | 100% services healthy | `docker-compose ps` shows all containers `Up (healthy)` |
| **Storage Readiness**| Bucket available | MinIO CLI shows `mlflow-artifacts` ready |
| **Experiment Tracking**| >= 1 logged run | MLflow UI shows params, metrics, model artifacts |
| **Model Registry** | Model in `Production` | MLflow Model Registry contains registered model |
| **Inference Service**| < 100ms response time | `curl http://localhost:8000/predict` returns HTTP 200 |
| **Metrics Pipeline** | Target status `UP` | Prometheus shows `model-server` target scraping |
| **Test Coverage** | 100% tests passing | `pytest tests/` completes with 0 failures and 0 skips |

---

## 5. Planning References

For execution tracking and defect remediation specifications, consult:
- [REMEDIATION_PLAN.md](planning/REMEDIATION_PLAN.md)
- [TRACKER.md](planning/TRACKER.md)
