#!/bin/bash
# Builds Docker images inside minikube's daemon, applies all K8s manifests, and restarts deployments.
# Run from the project root: ./scripts/deploy.sh

set -e

echo "==> Switching to minikube's Docker daemon..."
# Building directly inside minikube's daemon means images are immediately available
# to Kubernetes without a separate load step, and avoids stale-cache issues with
# `minikube image load` not overwriting existing tags.
eval $(minikube docker-env)

echo "==> Building Docker images inside minikube..."
docker build -f backend/Dockerfile -t kuberange-backend:latest .
docker build -f worker/Dockerfile -t kuberange-worker:latest .
docker build -f frontend/Dockerfile -t kuberange-frontend:latest .

echo "==> Applying K8s manifests..."
kubectl apply -f k8s/database/
kubectl apply -f k8s/rbac/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/worker/
kubectl apply -f k8s/frontend/

echo "==> Restarting deployments to pick up new images..."
kubectl rollout restart deployment/backend deployment/worker deployment/frontend
kubectl rollout status deployment/backend deployment/worker deployment/frontend

echo ""
echo "==> Done! Getting frontend URL..."
minikube service frontend-service --url
