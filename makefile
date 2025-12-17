K8S_NS  := ml-factory
K8S_DIR := k8s

# Docker Hub configuration
DOCKER_USERNAME ?= classique # Change to your Docker Hub username
DOCKER_REGISTRY ?= docker.io
VERSION ?= latest

# Service names
BACKEND_IMAGE := ml-factory-backend
FRONTEND_IMAGE := ml-factory-frontend
SYNC_SERVICE_IMAGE := ml-factory-sync-service
MLFLOW_IMAGE := ml-factory-mlflow

.PHONY: k8s-start k8s-build k8s-apply k8s-wait k8s-up k8s-port-forward k8s-down
.PHONY: docker-build docker-push docker-build-push
.PHONY: test test-unit test-integration
.PHONY: lint lint-check lint-fix

k8s-start:
	minikube start --driver=docker

k8s-build:
	eval $$(minikube docker-env) && \
		docker build -t ml-factory-backend:latest -f backend/Dockerfile . && \
		docker build -t ml-factory-frontend:latest -f frontend/Dockerfile . && \
		docker build -t ml-factory-sync-service:latest -f sync_service/Dockerfile . && \
		docker build -t ml-factory-mlflow:latest -f mlflow/Dockerfile .

k8s-apply-minio:
	kubectl apply -f $(K8S_DIR)/namespace.yaml
	kubectl apply -f $(K8S_DIR)/configmap.yaml
	kubectl apply -f $(K8S_DIR)/secret.yaml
	kubectl apply -f $(K8S_DIR)/minio.yaml

k8s-wait-minio:
	@echo "Ожидание готовности MinIO..."
	kubectl wait --for=condition=available deployment/minio -n $(K8S_NS) --timeout=180s
	@echo "MinIO готов"

k8s-apply-rest:
	kubectl apply -f $(K8S_DIR)/backend.yaml
	kubectl apply -f $(K8S_DIR)/frontend.yaml
	kubectl apply -f $(K8S_DIR)/sync-service.yaml
	kubectl apply -f $(K8S_DIR)/mlflow.yaml
	- kubectl apply -f $(K8S_DIR)/ingress.yaml

k8s-wait-rest:
	@echo "Ожидание запуска остальных деплоев..."
	kubectl wait --for=condition=available deployment/backend -n $(K8S_NS) --timeout=180s
	kubectl wait --for=condition=available deployment/dvc-sync-agent -n $(K8S_NS) --timeout=180s
	kubectl wait --for=condition=available deployment/frontend -n $(K8S_NS) --timeout=180s
	kubectl wait --for=condition=available deployment/mlflow -n $(K8S_NS) --timeout=180s
	@echo "Все деплои готовы"

k8s-up: k8s-start k8s-build k8s-apply-minio k8s-wait-minio k8s-apply-rest k8s-wait-rest k8s-port-forward
	@echo "Kubernetes кластер готов"

k8s-port-forward:
	@echo "🌐 Доступ:"
	@echo "Frontend: http://localhost:8501"
	@echo "Backend:  http://localhost:8080/docs"
	@echo "minio: http://localhost:9001"
	@echo "mlflow: http://localhost:5001"
	kubectl port-forward svc/frontend 8501:8501 -n $(K8S_NS) &
	kubectl port-forward svc/backend 8080:8080 -n $(K8S_NS) &
	kubectl port-forward svc/minio 9001:9001 -n $(K8S_NS) &
	kubectl port-forward svc/mlflow 5001:5001 -n $(K8S_NS)

k8s-down:
	- kubectl delete -f $(K8S_DIR)/frontend.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/backend.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/minio.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/ingress.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/configmap.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/secret.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/namespace.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/sync-service.yaml -n $(K8S_NS)
	- kubectl delete -f $(K8S_DIR)/mlflow.yaml -n $(K8S_NS)
	minikube stop

# ========================
# Docker Build & Push
# ========================

docker-build:
	@echo "Сборка Docker образов..."
	docker build -t $(DOCKER_USERNAME)/$(BACKEND_IMAGE):$(VERSION) -f backend/Dockerfile .
	docker build -t $(DOCKER_USERNAME)/$(FRONTEND_IMAGE):$(VERSION) -f frontend/Dockerfile .
	docker build -t $(DOCKER_USERNAME)/$(SYNC_SERVICE_IMAGE):$(VERSION) -f sync_service/Dockerfile .
	docker build -t $(DOCKER_USERNAME)/$(MLFLOW_IMAGE):$(VERSION) -f mlflow/Dockerfile .
	@echo "✅ Образы собраны"

docker-push:
	@echo "Отправка образов в Docker Hub..."
	docker push $(DOCKER_USERNAME)/$(BACKEND_IMAGE):$(VERSION)
	docker push $(DOCKER_USERNAME)/$(FRONTEND_IMAGE):$(VERSION)
	docker push $(DOCKER_USERNAME)/$(SYNC_SERVICE_IMAGE):$(VERSION)
	docker push $(DOCKER_USERNAME)/$(MLFLOW_IMAGE):$(VERSION)
	@echo "✅ Образы отправлены в Docker Hub"

docker-build-push: docker-build docker-push
	@echo "✅ Сборка и отправка завершены"

# ========================
# Tests
# ========================

test:
	@echo "Запуск всех тестов..."
	python -m pytest tests/ -v
	@echo "✅ Тесты завершены"

test-unit:
	@echo "Запуск unit-тестов..."
	python -m pytest tests/test_unit_*.py -v
	@echo "✅ Unit-тесты завершены"

test-integration:
	@echo "Запуск интеграционных тестов..."
	python -m pytest tests/test_integr_*.py -v
	@echo "✅ Интеграционные тесты завершены"

# ========================
# Linters
# ========================

lint-check:
	@echo "Проверка кода линтером..."
	ruff check .
	@echo "✅ Проверка завершена"

lint-fix:
	@echo "Автоматическое исправление ошибок линтера..."
	ruff check --fix .
	@echo "✅ Исправления применены"

lint: lint-check
	@echo "✅ Линтинг завершен"