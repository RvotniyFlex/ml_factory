K8S_NS  := ml-factory
K8S_DIR := k8s

.PHONY: k8s-start k8s-build k8s-apply k8s-wait k8s-up k8s-port-forward k8s-down

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
