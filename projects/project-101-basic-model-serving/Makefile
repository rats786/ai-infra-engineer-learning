ifeq ($(OS),Windows_NT)
SHELL := C:/Program Files/Git/bin/sh.exe
.SHELLFLAGS := -c
endif

KUBECTL ?= kubectl
KUBECTL_CONTEXT ?=
KUBECTL_CMD := $(KUBECTL) $(if $(KUBECTL_CONTEXT),--context $(KUBECTL_CONTEXT))
DOCKER ?= docker

IMAGE_NAME ?= ghcr.io/rats786/project-101-basic-model-serving
IMAGE_TAG ?= v1.1
APP_IMAGE ?= $(IMAGE_NAME):$(IMAGE_TAG)

API_NAMESPACE ?= ml-serving
MONITORING_NAMESPACE ?= monitoring
API_DEPLOYMENT ?= ml-model-serving-deployment
API_SERVICE ?= ml-model-serving-service
PROMETHEUS_SERVICE ?= prometheus
GRAFANA_SERVICE ?= grafana

API_LOCAL_PORT ?= 8000
PROMETHEUS_LOCAL_PORT ?= 9090
GRAFANA_LOCAL_PORT ?= 3000
RUNTIME_DIR := .runtime

.PHONY: help build-image push-image context deploy deploy-api deploy-monitoring delete delete-api delete-monitoring \
	status status-api status-monitoring api-running forward-api forward-prometheus forward-grafana forward-all \
	health-api health-prometheus health-grafana health-all review stop-port-forwards

help: ## Show available image and AKS operations
	@printf '%s\n' \
		'Image, API, and monitoring commands (checked-in manifests are the source of truth):' \
		'  make build-image            Build the application image ($(APP_IMAGE))' \
		'  make push-image             Push the application image to GHCR' \
		'  make deploy                 Apply API and monitoring Kustomize manifests' \
		'  make delete                 Delete API and monitoring Kustomize resources' \
		'  make status                 Show API, Prometheus, Grafana, pods, and services' \
		'  make forward-all            Start local port forwards for all running services' \
		'  make health-all             Check locally forwarded health endpoints' \
		'  make review                 Report status, start forwards, and run health checks' \
		'  make stop-port-forwards     Stop port forwards started by this Makefile' \
		'' \
		'Optional: make IMAGE_TAG=v1.2 build-image push-image' \
		'Optional: make KUBECTL_CONTEXT=my-aks-context review'

build-image: ## Build the application image
	$(DOCKER) build --tag $(APP_IMAGE) .

push-image: build-image ## Build and push the application image
	$(DOCKER) push $(APP_IMAGE)

context: ## Show the Kubernetes context that will be used
	@if [ -n "$(KUBECTL_CONTEXT)" ]; then \
		echo "Configured context: $(KUBECTL_CONTEXT)"; \
	else \
		echo "Current context: $$($(KUBECTL_CMD) config current-context)"; \
	fi
	@$(KUBECTL_CMD) cluster-info >/dev/null
	@echo "Cluster is reachable."

deploy: deploy-api deploy-monitoring ## Declaratively deploy the API and monitoring stack

deploy-api: context ## Apply the API Kustomize configuration
	@test -f kubernetes/.secrets/ghcr-dockerconfig.json || { \
		echo "ERROR: kubernetes/.secrets/ghcr-dockerconfig.json is required for ghcr-pull." >&2; \
		echo "Use the approved secret-generation workflow; do not commit this file." >&2; \
		exit 1; \
	}
	$(KUBECTL_CMD) apply -k kubernetes
	$(KUBECTL_CMD) -n $(API_NAMESPACE) rollout status deployment/$(API_DEPLOYMENT) --timeout=5m

deploy-monitoring: context ## Apply Prometheus and Grafana Kustomize configuration
	@$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) get secret grafana-credentials >/dev/null 2>&1 || { \
		echo "ERROR: monitoring/grafana-credentials does not exist." >&2; \
		echo "Create it through the approved secure declarative secret workflow first." >&2; \
		exit 1; \
	}
	$(KUBECTL_CMD) apply -k monitoring
	$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) rollout status deployment/prometheus --timeout=3m
	$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) rollout status deployment/grafana --timeout=3m

delete: stop-port-forwards delete-monitoring delete-api ## Delete API and monitoring resources declaratively

delete-api: context ## Delete resources managed by the API Kustomize configuration
	$(KUBECTL_CMD) delete -k kubernetes --ignore-not-found

delete-monitoring: context ## Delete resources managed by the monitoring Kustomize configuration
	$(KUBECTL_CMD) delete -k monitoring --ignore-not-found

status: context status-api status-monitoring ## Report AKS deployment status

status-api: ## Report API deployment, pod, and service status
	@echo "=== API ($(API_NAMESPACE)) ==="
	@$(KUBECTL_CMD) -n $(API_NAMESPACE) get deployment/$(API_DEPLOYMENT) -o wide || true
	@$(KUBECTL_CMD) -n $(API_NAMESPACE) get pods -l app=ml-model-serving -o wide || true
	@$(KUBECTL_CMD) -n $(API_NAMESPACE) get service/$(API_SERVICE) -o wide || true

status-monitoring: ## Report Prometheus and Grafana status
	@echo "=== Monitoring ($(MONITORING_NAMESPACE)) ==="
	@$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) get deployments prometheus grafana -o wide || true
	@$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) get pods -l 'app in (prometheus,grafana)' -o wide || true
	@$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) get services prometheus grafana -o wide || true
	@$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) get pvc grafana-data -o wide || true

api-running: context ## Fail unless the API has at least one available replica
	@available="$$($(KUBECTL_CMD) -n $(API_NAMESPACE) get deployment/$(API_DEPLOYMENT) -o jsonpath='{.status.availableReplicas}' 2>/dev/null || true)"; \
	if [ -z "$$available" ] || [ "$$available" -lt 1 ]; then \
		echo "ERROR: $(API_DEPLOYMENT) is not running in $(API_NAMESPACE)." >&2; \
		exit 1; \
	fi; \
	echo "API is running: $$available available replica(s)."

forward-api: api-running ## Start API port-forward after verifying that it is running
	@mkdir -p $(RUNTIME_DIR); \
	if [ -f $(RUNTIME_DIR)/api.pid ] && kill -0 $$(cat $(RUNTIME_DIR)/api.pid) 2>/dev/null; then \
		echo "API port-forward already running on localhost:$(API_LOCAL_PORT)."; \
	else \
		$(KUBECTL_CMD) -n $(API_NAMESPACE) port-forward service/$(API_SERVICE) $(API_LOCAL_PORT):80 >$(RUNTIME_DIR)/api.log 2>&1 & \
		echo $$! >$(RUNTIME_DIR)/api.pid; \
		sleep 2; \
		kill -0 $$(cat $(RUNTIME_DIR)/api.pid) 2>/dev/null || { cat $(RUNTIME_DIR)/api.log >&2; exit 1; }; \
		echo "API forwarded to http://localhost:$(API_LOCAL_PORT)"; \
	fi

forward-prometheus: context ## Start Prometheus port-forward
	@mkdir -p $(RUNTIME_DIR); \
	if [ -f $(RUNTIME_DIR)/prometheus.pid ] && kill -0 $$(cat $(RUNTIME_DIR)/prometheus.pid) 2>/dev/null; then \
		echo "Prometheus port-forward already running on localhost:$(PROMETHEUS_LOCAL_PORT)."; \
	else \
		$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) port-forward service/$(PROMETHEUS_SERVICE) $(PROMETHEUS_LOCAL_PORT):9090 >$(RUNTIME_DIR)/prometheus.log 2>&1 & \
		echo $$! >$(RUNTIME_DIR)/prometheus.pid; \
		sleep 2; \
		kill -0 $$(cat $(RUNTIME_DIR)/prometheus.pid) 2>/dev/null || { cat $(RUNTIME_DIR)/prometheus.log >&2; exit 1; }; \
		echo "Prometheus forwarded to http://localhost:$(PROMETHEUS_LOCAL_PORT)"; \
	fi

forward-grafana: context ## Start Grafana port-forward
	@mkdir -p $(RUNTIME_DIR); \
	if [ -f $(RUNTIME_DIR)/grafana.pid ] && kill -0 $$(cat $(RUNTIME_DIR)/grafana.pid) 2>/dev/null; then \
		echo "Grafana port-forward already running on localhost:$(GRAFANA_LOCAL_PORT)."; \
	else \
		$(KUBECTL_CMD) -n $(MONITORING_NAMESPACE) port-forward service/$(GRAFANA_SERVICE) $(GRAFANA_LOCAL_PORT):3000 >$(RUNTIME_DIR)/grafana.log 2>&1 & \
		echo $$! >$(RUNTIME_DIR)/grafana.pid; \
		sleep 2; \
		kill -0 $$(cat $(RUNTIME_DIR)/grafana.pid) 2>/dev/null || { cat $(RUNTIME_DIR)/grafana.log >&2; exit 1; }; \
		echo "Grafana forwarded to http://localhost:$(GRAFANA_LOCAL_PORT)"; \
	fi

forward-all: forward-api forward-prometheus forward-grafana ## Forward API, Prometheus, and Grafana

health-api: ## Check the API through its local port-forward
	@curl --fail --silent --show-error --max-time 10 \
		--retry 5 --retry-connrefused --retry-delay 1 \
		--write-out 'API /health: HTTP %{http_code}\n' \
		http://localhost:$(API_LOCAL_PORT)/health

health-prometheus: ## Check Prometheus through its local port-forward
	@curl --fail --silent --show-error --max-time 10 \
		--retry 5 --retry-connrefused --retry-delay 1 \
		--write-out 'Prometheus ready: HTTP %{http_code}\n' \
		http://localhost:$(PROMETHEUS_LOCAL_PORT)/-/ready

health-grafana: ## Check Grafana through its local port-forward
	@curl --fail --silent --show-error --max-time 10 \
		--retry 5 --retry-connrefused --retry-delay 1 \
		--write-out 'Grafana health: HTTP %{http_code}\n' \
		http://localhost:$(GRAFANA_LOCAL_PORT)/api/health

health-all: health-api health-prometheus health-grafana ## Check all local health endpoints

review: status forward-all health-all ## Status report plus local forwarding and health checks
	@echo "Review endpoints ready for testing:"
	@echo "  API:        http://localhost:$(API_LOCAL_PORT)"
	@echo "  Prometheus: http://localhost:$(PROMETHEUS_LOCAL_PORT)"
	@echo "  Grafana:    http://localhost:$(GRAFANA_LOCAL_PORT)"

stop-port-forwards: ## Stop port forwards started by this Makefile
	@for name in api prometheus grafana; do \
		if [ -f $(RUNTIME_DIR)/$$name.pid ]; then \
			pid=$$(cat $(RUNTIME_DIR)/$$name.pid); \
			if kill -0 "$$pid" 2>/dev/null; then kill "$$pid"; fi; \
			rm -f $(RUNTIME_DIR)/$$name.pid; \
		fi; \
	done
	@echo "Stopped managed port-forwards."
