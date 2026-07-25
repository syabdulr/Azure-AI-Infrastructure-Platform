# Architecture Diagram

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT APPLICATIONS                       │
│  Web UI • Mobile Apps • Partners • Internal Services             │
└────────────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     AZURE LOAD BALANCER                          │
│                (SSL Termination + Routing)                       │
└────────────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │
│  │  Chat    │ │   RAG    │ │Guardrails│ │ Monitoring│          │
│  │  Routes  │ │  Routes  │ │  Routes  │ │  Routes   │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘           │
└────────────────────────────────────┬────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AZURE SERVICES                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │Azure OpenAI  │  │Cognitive     │  │Azure Storage │          │
│  │  GPT-4       │  │Search        │  │Documents     │          │
│  │  Embeddings  │  │Vector Search │  │  Cache       │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│  ┌──────────────┐                                                  │
│  │Azure Key Vault│ - Secrets, Certs, Keys                       │
│  └──────────────┘                                                  │
└─────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        OBSERVABILITY STACK                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │Prometheus│  │ Grafana  │  │App Insights│ │Logs      │       │
│  │  (9090)  │  │ (3000)   │  │          │  │(JSON)    │       │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow: Chat Completion

```
Client Request
    │
    ▼
API Gateway (FastAPI)
    ├─> Rate Limiting Check
    ├─> Input Validation
    └─> Guardrails Check (PII Detection)
    │
    ▼
Azure OpenAI (GPT-4)
    ├─> Load Prompt Template
    ├─> Generate Response
    └─> Response Evaluation
    │
    ▼
Output Filtering
    ├─> PII Redaction
    ├─> Content Safety
    └─> Quality Metrics
    │
    ▼
Return to Client
    ├─> Response Data
    ├─> Metrics (tokens, latency, cost)
    └─> Telemetry Logging
```

**Full Architecture Documentation:** See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed system design, security architecture, and scalability strategies.

**Deployment Strategies:** See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Azure deployment guides (Container Apps, App Service, AKS).

**Quick Start:** See [docs/QUICK_START.md](docs/QUICK_START.md) for fast deployment and troubleshooting.