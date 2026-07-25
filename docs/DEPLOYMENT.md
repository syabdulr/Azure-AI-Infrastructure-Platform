# Deployment Guide

## Deployment Overview

This guide covers deploying the Azure AI Infrastructure Platform to Azure using different strategies:

1. **Azure Container Apps** (Recommended for production)
2. **Azure App Service** (Simplified deployment)
3. **Docker Compose** (Local development)
4. **Azure Kubernetes Service (AKS)** (Enterprise-scale)

---

## Strategy 1: Azure Container Apps (Production)

### Prerequisites

```bash
# Install Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Login to Azure
az login

# Install Container Apps extension
az extension add --name containerapp --upgrade
```

### Step 1: Create Resource Group

```bash
# Create resource group
az group create \
  --name rg-azure-ai-platform \
  --location eastus

# Create Azure OpenAI resource
az cognitiveservices account create \
  --name ai-platform-openai \
  --resource-group rg-azure-ai-platform \
  --kind OpenAI \
  --sku S0 \
  --location eastus

# Create Cognitive Search resource
az search service create \
  --name ai-platform-search \
  --resource-group rg-azure-ai-platform \
  --sku Basic \
  --location eastus

# Create Storage Account
az storage account create \
  --name aiplatformstorage \
  --resource-group rg-azure-ai-platform \
  --sku Standard_LRS \
  --location eastus

# Create Key Vault
az keyvault create \
  --name ai-platform-kv \
  --resource-group rg-azure-ai-platform \
  --location eastus
```

### Step 2: Configure Azure Services

```bash
# Get API keys and endpoints
OPENAI_KEY=$(az cognitiveservices account keys list \
  --name ai-platform-openai \
  --resource-group rg-azure-ai-platform \
  --query key1 -o tsv)

OPENAI_ENDPOINT=$(az cognitiveservices account show \
  --name ai-platform-openai \
  --resource-group rg-azure-ai-platform \
  --query properties.endpoint -o tsv)

SEARCH_KEY=$(az search admin-key show \
  --service-name ai-platform-search \
  --resource-group rg-azure-ai-platform \
  --query primaryKey -o tsv)

SEARCH_ENDPOINT=$(az search service show \
  --name ai-platform-search \
  --resource-group rg-azure-ai-platform \
  --query properties.endpoint -o tsv)

# Store secrets in Key Vault
az keyvault secret set \
  --vault-name ai-platform-kv \
  --name AzureOpenAIKey \
  --value $OPENAI_KEY

az keyvault secret set \
  --vault-name ai-platform-kv \
  --name AzureSearchKey \
  --value $SEARCH_KEY
```

### Step 3: Deploy Application

```bash
# Build Docker image
docker build -t azure-ai-platform:latest .

# Tag for Azure Container Registry
az acr create \
  --name aiplatformacr \
  --resource-group rg-azure-ai-platform \
  --sku Basic

az acr login --name aiplatformacr

docker tag azure-ai-platform:latest aiplatformacr.azurecr.io/azure-ai-platform:latest
docker push aiplatformacr.azurecr.io/azure-ai-platform:latest

# Create Container App Environment
az containerapp env create \
  --name azure-ai-env \
  --resource-group rg-azure-ai-platform \
  --location eastus

# Deploy Container App
az containerapp create \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --environment azure-ai-env \
  --image aiplatformacr.azurecr.io/azure-ai-platform:latest \
  --target-port 8000 \
  --ingress external \
  --cpu 0.5 \
  --memory 1Gi \
  --min-replicas 2 \
  --max-replicas 10 \
  --env-vars \
    AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT \
    AZURE_OPENAI_API_KEY=secretref:ai-platform-kv/AzureOpenAIKey \
    AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT \
    AZURE_SEARCH_API_KEY=secretref:ai-platform-kv/AzureSearchKey
```

### Step 4: Configure Monitoring

```bash
# Create Log Analytics Workspace
az monitor log-analytics workspace create \
  --name azure-ai-logs \
  --resource-group rg-azure-ai-platform \
  --location eastus

# Enable Application Insights
az monitor app-insights component create \
  --app azure-ai-platform \
  --location eastus \
  --resource-group rg-azure-ai-platform \
  --application-type web

# Configure Container App with Application Insights
az containerapp update \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --enable-dapr true
```

---

## Strategy 2: Azure App Service (Simplified)

### Step 1: Create Web App

```bash
# Create App Service Plan
az appservice plan create \
  --name azure-ai-plan \
  --resource-group rg-azure-ai-platform \
  --sku B1 \
  --location eastus

# Create Web App
az webapp create \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --plan azure-ai-plan \
  --runtime "PYTHON:3.11"

# Configure startup command
az webapp config set \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --startup-file "uvicorn src.main:app --host 0.0.0.0 --port 8000"

# Set environment variables
az webapp config appsettings set \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --settings \
    AZURE_OPENAI_ENDPOINT=$OPENAI_ENDPOINT \
    AZURE_OPENAI_API_KEY=$OPENAI_KEY \
    AZURE_SEARCH_ENDPOINT=$SEARCH_ENDPOINT \
    AZURE_SEARCH_API_KEY=$SEARCH_KEY
```

### Step 2: Deploy Code

```bash
# Deploy using Git (requires remote repository)
az webapp deployment source config \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --repo-url https://github.com/syabdulr/Azure-AI-Infrastructure-Platform \
  --branch main

# Or deploy using ZIP
az webapp deployment source config-zip \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --src azure-ai-platform.zip
```

---

## Strategy 3: Docker Compose (Local Development)

### Step 1: Create Docker Compose File

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}
      - AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}
      - AZURE_SEARCH_ENDPOINT=${AZURE_SEARCH_ENDPOINT}
      - AZURE_SEARCH_API_KEY=${AZURE_SEARCH_API_KEY}
    depends_on:
      - prometheus
      - grafana
    volumes:
      - ./logs:/app/logs

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/dashboards:/etc/grafana/provisioning/dashboards

volumes:
  prometheus-data:
  grafana-data:
```

### Step 2: Run Application

```bash
# Create .env file
cp .env.example .env
# Edit .env with your Azure credentials

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose logs -f app

# Stop services
docker-compose -f docker-compose.prod.yml down
```

---

## Strategy 4: Azure Kubernetes Service (AKS) - Enterprise

### Step 1: Create AKS Cluster

```bash
# Create AKS cluster
az aks create \
  --name azure-ai-aks \
  --resource-group rg-azure-ai-platform \
  --node-count 3 \
  --node-vm-size Standard_DS3_v2 \
  --enable-cluster-autoscaler \
  --min-count 2 \
  --max-count 10 \
  --location eastus

# Get cluster credentials
az aks get-credentials \
  --name azure-ai-aks \
  --resource-group rg-azure-ai-platform
```

### Step 2: Create Kubernetes Manifests

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: azure-ai-platform
spec:
  replicas: 3
  selector:
    matchLabels:
      app: azure-ai-platform
  template:
    metadata:
      labels:
        app: azure-ai-platform
    spec:
      containers:
      - name: app
        image: aiplatformacr.azurecr.io/azure-ai-platform:latest
        ports:
        - containerPort: 8000
        env:
        - name: AZURE_OPENAI_ENDPOINT
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: openai-endpoint
        - name: AZURE_OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: azure-secrets
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: azure-ai-platform-service
spec:
  selector:
    app: azure-ai-platform
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: azure-ai-platform-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: azure-ai-platform
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

### Step 3: Create Secrets

```bash
# Create Kubernetes secret
kubectl create secret generic azure-secrets \
  --from-literal=openai-endpoint=$OPENAI_ENDPOINT \
  --from-literal=openai-key=$OPENAI_KEY \
  --from-literal=search-endpoint=$SEARCH_ENDPOINT \
  --from-literal=search-key=$SEARCH_KEY
```

### Step 4: Deploy to AKS

```bash
# Apply manifests
kubectl apply -f k8s/deployment.yaml

# Check deployment status
kubectl get pods
kubectl get services
kubectl get hpa

# View logs
kubectl logs -f deployment/azure-ai-platform
```

---

## Deployment Pipeline (GitHub Actions)

### Workflow Configuration

```yaml
# .github/workflows/deploy.yml
name: Deploy to Azure Container Apps

on:
  push:
    branches:
      - main

env:
  AZURE_CONTAINER_REGISTRY: aiplatformacr.azurecr.io
  IMAGE_NAME: azure-ai-platform
  CONTAINER_APP: azure-ai-platform
  RESOURCE_GROUP: rg-azure-ai-platform

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Run tests
      run: |
        pytest tests/unit/ -v
    
    - name: Build Docker image
      run: |
        docker build -t $IMAGE_NAME:${{ github.sha }} .
        docker tag $IMAGE_NAME:${{ github.sha }} $IMAGE_NAME:latest
    
    - name: Login to Azure Container Registry
      uses: azure/docker-login@v1
      with:
        login-server: ${{ env.AZURE_CONTAINER_REGISTRY }}
        username: ${{ secrets.ACR_USERNAME }}
        password: ${{ secrets.ACR_PASSWORD }}
    
    - name: Push to Container Registry
      run: |
        docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/$IMAGE_NAME:${{ github.sha }}
        docker push ${{ env.AZURE_CONTAINER_REGISTRY }}/$IMAGE_NAME:latest
    
    - name: Login to Azure
      uses: azure/login@v1
      with:
        creds: ${{ secrets.AZURE_CREDENTIALS }}
    
    - name: Deploy to Container Apps
      run: |
        az containerapp update \
          --name ${{ env.CONTAINER_APP }} \
          --resource-group ${{ env.RESOURCE_GROUP }} \
          --image ${{ env.AZURE_CONTAINER_REGISTRY }}/$IMAGE_NAME:${{ github.sha }}
```

### Setting Up GitHub Secrets

```bash
# Get Azure credentials
az ad sp create-for-rbac \
  --name github-actions-deployer \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/rg-azure-ai-platform \
  --json-auth

# Get ACR credentials
ACR_USERNAME=$(az acr credential show \
  --name aiplatformacr \
  --resource-group rg-azure-ai-platform \
  --query username -o tsv)

ACR_PASSWORD=$(az acr credential show \
  --name aiplatformacr \
  --resource-group rg-azure-ai-platform \
  --query passwords[0].value -o tsv)

# Add secrets to GitHub repository
# Repository > Settings > Secrets > Actions > New repository secret
# - AZURE_CREDENTIALS: (output from az ad sp create-for-rbac)
# - ACR_USERNAME: (output from az acr credential show)
# - ACR_PASSWORD: (output from az acr credential show)
```

---

## Verification Steps

### After Deployment

```bash
# Check application health
curl https://your-app-url.health

# Test chat endpoint
curl -X POST https://your-app-url.chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, world!"}'

# Check metrics
curl https://your-app-url.observability/metrics

# View logs
az containerapp logs show \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --follow
```

### Monitor Application

```bash
# View metrics in Grafana
# Navigate to http://your-grafana-url:3000
# Login with admin/admin
# Import pre-configured dashboards from ./grafana/dashboards/

# View logs in Log Analytics
az monitor log-analytics query \
  --workspace azure-ai-logs \
  --analytics-query "AzureDiagnostics | take 10"
```

---

## Troubleshooting

### Common Issues

1. **Application not starting**
   ```bash
   # Check logs
   az containerapp logs show --name azure-ai-platform --resource-group rg-azure-ai-platform --follow
   
   # Check environment variables
   az containerapp revision show --name azure-ai-platform --resource-group rg-azure-ai-platform
   ```

2. **Azure OpenAI connection failed**
   ```bash
   # Verify API key and endpoint
   az cognitiveservices account keys list --name ai-platform-openai --resource-group rg-azure-ai-platform
   ```

3. **Cognitive Search not indexing**
   ```bash
   # Check search service status
   az search service show --name ai-platform-search --resource-group rg-azure-ai-platform
   ```

---

## Cost Optimization

### Estimated Monthly Costs (Production)

| Service | Tier | Cost |
|---------|------|------|
| Azure Container Apps | Standard | $30-100 |
| Azure OpenAI (GPT-4) | S0 | $50-500+ |
| Cognitive Search | Basic | $25-150 |
| Storage Account | Standard LRS | $5-20 |
| Key Vault | Standard | $5 |
| Log Analytics | Per GB | $2-10 |
| Application Insights | Standard | $2-10 |

**Total Estimated: $120-795/month**

### Cost Reduction Strategies

1. **Use GPT-3.5 instead of GPT-4** for non-critical queries (10x cheaper)
2. **Enable auto-scaling** to scale down during off-peak hours
3. **Use caching** to reduce Azure OpenAI API calls
4. **Monitor token usage** and optimize prompts
5. **Use Cognitive Search Free Tier** for development/testing

---

## Next Steps

1. **Configure monitoring alerts** in Azure Monitor
2. **Set up CI/CD pipeline** for automated deployments
3. **Implement A/B testing** for prompt optimization
4. **Add custom domains** with SSL certificates
5. **Configure custom DNS** and CDN for better performance
6. **Implement multi-region deployment** for high availability