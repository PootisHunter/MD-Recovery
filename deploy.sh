#!/bin/bash

# Set DockerHub Username (Replace with your actual username)
DOCKER_USER="your-dockerhub-user"

# Kubernetes Manifests
MANIFESTS=(
    "clientAgent-deployment.yaml"
    "alertHandler-deployment.yaml"
    "prometheus-deployment.yaml"
    "grafana-deployment.yaml"
    "prometheus-configmap.yaml"
)

echo "🚀 Starting Deployment Process..."

# Step 1: Build Docker Images
echo "🔨 Building Docker Images..."
docker build -t client-agent ./clientAgent
docker build -t alert-handler ./alertHandler

# Step 2: Push Images to DockerHub
echo "📤 Pushing Images to DockerHub..."
docker tag client-agent $DOCKER_USER/client-agent:latest
docker tag alert-handler $DOCKER_USER/alert-handler:latest

docker push $DOCKER_USER/client-agent:latest
docker push $DOCKER_USER/alert-handler:latest

# Step 3: Deploy to Kubernetes
echo "🚀 Applying Kubernetes Manifests..."
for manifest in "${MANIFESTS[@]}"; do
    kubectl apply -f $manifest
done

# Step 4: Set Up Port Forwarding
echo "🌍 Setting up port forwarding for Prometheus & Grafana..."
kubectl port-forward service/grafana 32000:3000 &
kubectl port-forward service/prometheus 9090:9090 &

echo "✅ Deployment Complete!"
echo "📊 Grafana: http://localhost:32000 (default login: admin/admin)"
echo "📈 Prometheus: http://localhost:9090"
