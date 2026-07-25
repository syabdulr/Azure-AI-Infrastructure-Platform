# Quick Reference: Deployment Flowchart

## Development to Production Deployment

```
LOCAL DEVELOPMENT
    │
    ├─> 1. Clone repository
    │   └─> git clone https://github.com/syabdulr/Azure-AI-Infrastructure-Platform.git
    │
    ├─> 2. Setup environment
    │   ├─> python3 -m venv .venv
    │   ├─> source .venv/bin/activate
    │   ├─> pip install -r requirements.txt
    │   └─> cp .env.example .env
    │
    ├─> 3. Run locally
    │   ├─> uvicorn src.main:app --reload
    │   └─> Access: http://localhost:8000
    │
    ├─> 4. Test & verify
    │   ├─> pytest tests/unit/ -v
    │   └─> curl http://localhost:8000/health
    │
    └─> 5. Push to GitHub
        └─> git push origin main

GIT PUSH TRIGGERS CI/CD
    │
    ├─> GitHub Actions Workflow Runs:
    │   ├─> ✅ Linting (flake8, black)
    │   ├─> ✅ Unit Tests (pytest)
    │   ├─> ✅ Coverage Check (27%+)
    │   ├─> ✅ Docker Build
    │   └─> ✅ Push to ACR
    │
    └─> Auto-deployment to Azure (if configured)

PRODUCTION DEPLOYMENT
    │
    ├─> OPTION 1: Azure Container Apps (Recommended)
    │   ├─> Create resource group
    │   ├─> Create Azure OpenAI, Cognitive Search, Storage
    │   ├─> Configure environment variables
    │   ├─> Deploy container app
    │   └─> Configure monitoring
    │
    ├─> OPTION 2: Azure App Service (Simplified)
    │   ├─> Create app service plan
    │   ├─> Create web app
    │   ├─> Configure startup command
    │   ├─> Deploy code (Git/ZIP)
    │   └─> Set environment variables
    │
    ├─> OPTION 3: Docker Compose (Local/Dev)
    │   ├─> Create .env with Azure credentials
    │   ├─> Run: docker-compose up -d
    │   └─> Access: http://localhost:8000
    │
    └─> OPTION 4: AKS (Enterprise)
        ├─> Create AKS cluster
        ├─> Create Kubernetes manifests
        ├─> Create secrets
        ├─> Apply manifests (kubectl)
        └─> Configure auto-scaling

POST-DEPLOYMENT
    │
    ├─> Health Checks
    │   ├─> curl https://your-app.health
    │   ├─> Check Azure Portal logs
    │   └─> Verify all services healthy
    │
    ├─> Monitoring Setup
    │   ├─> Configure Prometheus scrapers
    │   ├─> Import Grafana dashboards
    │   ├─> Set up alert rules
    │   └─> Configure Application Insights
    │
    ├─> Performance Tuning
    │   ├─> Monitor CPU/memory usage
    │   ├─> Adjust replica count
    │   ├─> Optimize Azure OpenAI prompts
    │   └─> Enable caching
    │
    └─> Security Hardening
        ├─> Configure Azure Firewall
        ├─> Set up WAF rules
        ├─> Enable Azure AD authentication
        └─> Rotate secrets regularly

ONGOING OPERATIONS
    │
    ├─> Daily Monitoring
    │   ├─> Check Grafana dashboards
    │   ├─> Review application logs
    │   └─> Verify API health
    │
    ├─> Weekly Maintenance
    │   ├─> Review costs
    │   ├─> Check for security vulnerabilities
    │   └─> Update dependencies
    │
    ├─> Monthly Reviews
    │   ├─> Performance analysis
    │   ├─> Capacity planning
    │   ├─> Audit logs
    │   └─> Optimize resource usage
    │
    └─> Continuous Improvement
        ├─> Monitor token usage
        ├─> A/B test prompts
        ├─> Optimize RAG retrieval
        └─> Improve guardrails
```

## Quick Start Deployment

### For Demo/Recruiter (No Azure Required)

```bash
# 1. Clone and setup
git clone https://github.com/syabdulr/Azure-AI-Infrastructure-Platform.git
cd Azure-AI-Infrastructure-Platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Run in demo mode
export DEMO_MODE=true
uvicorn src.main:app --reload

# 3. Access
# Swagger UI: http://localhost:8000/docs
# Health Check: http://localhost:8000/health
# Metrics: http://localhost:8000/observability/metrics
```

### For Production (Azure Required)

```bash
# 1. Prerequisites
az login
az extension add --name containerapp --upgrade

# 2. Create resources
az group create --name rg-azure-ai-platform --location eastus
az cognitiveservices account create --name ai-platform-openai --resource-group rg-azure-ai-platform --kind OpenAI --sku S0
az search service create --name ai-platform-search --resource-group rg-azure-ai-platform --sku Basic
az storage account create --name aiplatformstorage --resource-group rg-azure-ai-platform --sku Standard_LRS

# 3. Deploy
docker build -t azure-ai-platform:latest .
az containerapp create \
  --name azure-ai-platform \
  --resource-group rg-azure-ai-platform \
  --image azure-ai-platform:latest \
  --ingress external \
  --env-vars AZURE_OPENAI_ENDPOINT=... AZURE_OPENAI_API_KEY=...

# 4. Access
# Application: https://your-app-url.azurecontainerapps.io
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| App won't start | Check logs: `az containerapp logs show --follow` |
| Azure OpenAI error | Verify API key: `az cognitiveservices account keys list` |
| Search not working | Check search status: `az search service show` |
| High latency | Scale up replicas: `az containerapp update --min-replicas 5` |
| Cost too high | Use GPT-3.5 or enable caching |

## Cost Monitoring

```bash
# View current costs
az consumption usage list --resource-group rg-azure-ai-platform --output table

# Set budget alert
az consumption budget create \
  --account-name rg-azure-ai-platform \
  --amount 100 \
  --name monthly-budget
```

## Security Checklist

- [ ] Secrets stored in Azure Key Vault
- [ ] Azure Firewall configured
- [ ] WAF rules enabled
- [ ] HTTPS/TLS enforced
- [ ] RBAC configured
- [ ] Audit logging enabled
- [ ] Regular secret rotation
- [ ] DDoS protection enabled