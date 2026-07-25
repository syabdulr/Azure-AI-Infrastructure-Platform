#!/bin/bash
# Build Docker image for Azure AI Infrastructure Platform

set -e

# Configuration
VERSION=${VERSION:-1.0.0}
IMAGE_NAME="azure-ai-platform"
REGISTRY=${REGISTRY:-}

# Build arguments
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

echo "Building Docker image..."
echo "Image: ${IMAGE_NAME}"
echo "Version: ${VERSION}"
echo "Build Date: ${BUILD_DATE}"
echo "VCS Ref: ${VCS_REF}"

# Build image
if [ -n "$REGISTRY" ]; then
    docker build \
        -t ${REGISTRY}/${IMAGE_NAME}:${VERSION} \
        -t ${REGISTRY}/${IMAGE_NAME}:latest \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VERSION="${VERSION}" \
        --build-arg VCS_REF="${VCS_REF}" \
        .
else
    docker build \
        -t ${IMAGE_NAME}:${VERSION} \
        -t ${IMAGE_NAME}:latest \
        --build-arg BUILD_DATE="${BUILD_DATE}" \
        --build-arg VERSION="${VERSION}" \
        --build-arg VCS_REF="${VCS_REF}" \
        .
fi

echo "Docker image built successfully!"

# Show image size
echo ""
echo "Image sizes:"
docker images ${IMAGE_NAME} --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}"