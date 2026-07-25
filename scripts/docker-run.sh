#!/bin/bash
# Run Docker container for Azure AI Infrastructure Platform

set -e

# Configuration
VERSION=${VERSION:-1.0.0}
IMAGE_NAME=${IMAGE_NAME:-azure-ai-platform}
CONTAINER_NAME=${CONTAINER_NAME:-azure-ai-platform-api}
PORT=${PORT:-8000}

# Environment variables (load from .env if exists)
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

echo "Running Docker container..."
echo "Image: ${IMAGE_NAME}:${VERSION}"
echo "Container: ${CONTAINER_NAME}"
echo "Port: ${PORT}"

# Stop and remove existing container if running
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "Stopping existing container..."
    docker stop ${CONTAINER_NAME}
    docker rm ${CONTAINER_NAME}
fi

# Run container
docker run \
    -d \
    --name ${CONTAINER_NAME} \
    -p ${PORT}:8000 \
    --restart unless-stopped \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/data:/app/data \
    -e AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT} \
    -e AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION:-2024-02-01} \
    -e AZURE_OPENAI_DEPLOYMENT_NAME=${AZURE_OPENAI_DEPLOYMENT_NAME} \
    -e AZURE_OPENAI_MODEL_NAME=${AZURE_OPENAI_MODEL_NAME:-gpt-4} \
    -e AZURE_SEARCH_ENDPOINT=${AZURE_SEARCH_ENDPOINT} \
    -e AZURE_SEARCH_INDEX_NAME=${AZURE_SEARCH_INDEX_NAME} \
    -e AZURE_SEARCH_API_VERSION=${AZURE_SEARCH_API_VERSION:-2023-11-01} \
    -e DEBUG=${DEBUG:-false} \
    -e LOG_LEVEL=${LOG_LEVEL:-INFO} \
    ${IMAGE_NAME}:${VERSION}

echo "Docker container started successfully!"
echo ""
echo "Access the application at: http://localhost:${PORT}"
echo "Health check: http://localhost:${PORT}/health"
echo ""
echo "View logs: docker logs -f ${CONTAINER_NAME}"
echo "Stop container: docker stop ${CONTAINER_NAME}"