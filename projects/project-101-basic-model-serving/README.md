# Project 101: Basic Model Serving System

This repository is a practical model-serving project for a FastAPI + PyTorch image-classification service, with local Compose validation, monitoring work, and a Kubernetes remediation track that documents the production-hardening items discovered during review.

## Current Status

This fork is currently focused on:

- making the FastAPI app and metrics endpoints work reliably,
- validating the monitoring stack locally with Prometheus and Grafana,
- documenting Kubernetes deployment risks and remediation steps,
- and preparing a clean PR-ready branch with repo hygiene updates.

The active branch is `feature/k8s-remediation-docs`.

## What is already in place

### API and serving basics

- FastAPI application with image prediction flow and HTTP health checks
- `/predict`, `/health`, and `/metrics` endpoints in the application layer
- Local app startup and smoke testing workflow via Docker Compose and direct API calls

### Monitoring work

The project includes a monitoring remediation track and implementation notes for the fixes that were made and reviewed:

- [remediation/monitoring/tracker.md](remediation/monitoring/tracker.md)
- [remediation/monitoring/MON-1-prometheus-format.md](remediation/monitoring/MON-1-prometheus-format.md)
- [remediation/monitoring/MON-2-api-instrumentation.md](remediation/monitoring/MON-2-api-instrumentation.md)
- [remediation/monitoring/MON-3-metrics-setting.md](remediation/monitoring/MON-3-metrics-setting.md)
- [remediation/monitoring/MON-4-grafana-dashboard.md](remediation/monitoring/MON-4-grafana-dashboard.md)
- [remediation/monitoring/MON-5-end-to-end-check.md](remediation/monitoring/MON-5-end-to-end-check.md)

This work includes:

- Prometheus-compatible metric exposition
- bounded-cardinality request and inference metrics
- consistent metrics configuration for the scrape path
- Grafana dashboard provisioning
- end-to-end monitoring validation guidance

### Kubernetes remediation documentation

The repository also contains a Kubernetes hardening tracker with issue-specific notes for the discovered deployment concerns:

- [remediation/k8s/tracker.md](remediation/k8s/tracker.md)
- [remediation/k8s/K8S-1-readiness-model-failure.md](remediation/k8s/K8S-1-readiness-model-failure.md)
- [remediation/k8s/K8S-2-external-exposure.md](remediation/k8s/K8S-2-external-exposure.md)
- [remediation/k8s/K8S-3-configmap-env-usage.md](remediation/k8s/K8S-3-configmap-env-usage.md)
- [remediation/k8s/K8S-4-image-reference.md](remediation/k8s/K8S-4-image-reference.md)
- [remediation/k8s/K8S-5-startup-probe.md](remediation/k8s/K8S-5-startup-probe.md)
- [remediation/k8s/K8S-6-prometheus-platform.md](remediation/k8s/K8S-6-prometheus-platform.md)
- [remediation/k8s/K8S-7-grafana-platform.md](remediation/k8s/K8S-7-grafana-platform.md)
- [remediation/k8s/K8S-8-ingress-controller.md](remediation/k8s/K8S-8-ingress-controller.md)

These capture the main Kubernetes issues that were discovered during review, specifically around:

- readiness/liveness logic,
- external exposure and access control,
- ConfigMap and env-variable wiring,
- image sourcing and deployment reliability,
- startup behavior,
- platform separation for Prometheus, Grafana, and ingress,
- and cluster-level monitoring architecture.

### Repository hygiene

This branch also includes repo-level project hygiene for a cleaner PR workflow:

- [.gitignore](.gitignore)
- [.dockerignore](.dockerignore)
- [.github/pull_request_template.md](.github/pull_request_template.md)

## Project structure

```text
project-101-basic-model-serving/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pytest.ini
├── src/
│   ├── api.py
│   ├── config.py
│   ├── model.py
│   └── utils.py
├── tests/
│   ├── test_api.py
│   ├── test_config.py
│   ├── test_model.py
│   └── test_utils.py
├── kubernetes/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── hpa.yaml
│   └── service.yaml
├── monitoring/
│   ├── prometheus.yml
│   └── grafana/
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── TROUBLESHOOTING.md
├── remediation/
│   ├── k8s/
│   └── monitoring/
├── .github/
│   └── pull_request_template.md
├── .gitignore
├── .dockerignore
├── .env.example
└── README.md
```

## Local validation workflow

Useful commands for this project include:

```bash
docker compose up -d
docker compose ps
curl http://localhost:8000/health
curl http://localhost:8000/metrics
pytest -q
```

For the monitoring setup, Prometheus and Grafana are expected to be validated through the local Compose stack and the files under [monitoring/](monitoring/).

## Notes on scope

This project is in a learning and hardening phase rather than a final production deployment. The current branch emphasizes:

- documentation-first remediation,
- monitoring correctness,
- Kubernetes readiness review,
- and a clean, reviewable PR state.

No production Kubernetes deployment or production-level cluster rollout has been treated as complete in this branch yet.

## Next steps

Recommended follow-up work is tracked in [remediation/k8s/tracker.md](remediation/k8s/tracker.md), with the next implementation focus being the Kubernetes readiness, exposure, startup, and platform separation fixes described there.

This branch is intentionally documentation and hardening focused: it captures the real issues discovered during validation and sets up a clean PR-ready state without making additional runtime code changes yet.
