# Azure AI Infrastructure Platform

## 🎯 Overview

A production-ready Azure AI infrastructure platform that integrates Azure OpenAI, Azure Cognitive Search, and Azure Storage into a unified RESTful API. Built with FastAPI, featuring advanced monitoring, observability, and enterprise-grade guardrails.

## 🚀 Features

### AI & LLM
- **Azure OpenAI Integration**: Production-ready chat completions with GPT-4
- **Streaming Responses**: Real-time streaming for conversational AI
- **Prompt Management**: Version-controlled prompt templates with evaluation metrics
- **Response Evaluation**: Automated quality assessment of AI responses

### RAG (Retrieval-Augmented Generation)
- **Azure Cognitive Search**: Enterprise-grade semantic search
- **Document Processing**: Automatic chunking, embedding, and indexing
- **Batch Indexing**: Efficient bulk document processing
- **Semantic Retrieval**: Vector-based search with relevance scoring

### Guardrails & Safety
- **Input Filtering**: PII detection and redaction (emails, phones, SSNs)
- **Content Filtering**: Output safety checks
- **Rate Limiting**: User-level request throttling
- **Violation Tracking**: Comprehensive audit logging

### Monitoring & Observability
- **Prometheus Metrics**: Real-time metrics collection and export
- **Structured Logging**: JSON-formatted logs with correlation IDs
- **Health Checks**: Multi-tier health monitoring (application, dependencies, system)
- **Alert Management**: Configurable alerting with rules and thresholds

### Enterprise Features
- **Docker Support**: Containerized deployment with Docker Compose
- **CI/CD Pipeline**: GitHub Actions for automated testing and deployment
- **Comprehensive Testing**: 112+ unit tests with 27%+ code coverage
- **API Documentation**: Interactive Swagger UI with all endpoints documented

## 📊 API Endpoints

### Health & Monitoring
- `GET /health` - Health check with dependency status
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness probe
- `GET /monitoring/metrics` - Application metrics
- `GET /observability/metrics` - Extended metrics (Prometheus format)
- `GET /observability/health` - Health status with system metrics

### Chat & AI
- `POST /chat` - Chat completion with Azure OpenAI
- `POST /chat/stream` - Streaming chat completion
- `POST /prompts/evaluate` - Evaluate prompt responses
- `GET /prompts/templates` - List prompt templates
- `POST /prompts/templates/{name}/versions` - Create prompt version

### RAG
- `POST /rag/query` - Query documents with semantic search
- `POST /rag/index` - Index a document
- `POST /rag/index/batch` - Batch index documents

### Guardrails
- `POST /guardrails/check-input` - Check input for PII and safety
- `POST /guardrails/check-output` - Check output for safety
- `GET /guardrails/limits/{user_id}` - Get rate limit status
- `GET /guardrails/violations` - List all violations

## 🛠️ Installation

### Prerequisites
- Python 3.11+
- Azure account with:
  - Azure OpenAI Service
  - Azure Cognitive Search
  - Azure Storage Account

### Quick Start

1. **Clone the repository**
```bash
git clone https://github.com/syabdulr/Azure-AI-Infrastructure-Platform.git
cd Azure-AI-Infrastructure-Platform
```

2. **Create virtual environment**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

5. **Run the application**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

6. **Access the API**
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Metrics: http://localhost:8000/observability/metrics

## 🐳 Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

This will start:
- FastAPI application (port 8000)
- Prometheus (port 9090)
- Grafana (port 3000)

### Access Services
- Application: http://localhost:8000
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

## 📈 Monitoring

### Prometheus Metrics
Metrics are available at `/observability/metrics/prometheus` for Prometheus scraping.

Key metrics include:
- API request rate and latency
- AI request count and token usage
- RAG query performance
- Guardrails violations
- System resource usage

### Grafana Dashboards
Pre-configured dashboards are available:
- API Performance Dashboard
- AI Usage Dashboard
- System Health Dashboard

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/unit/ -v
```

### Run with Coverage
```bash
pytest tests/unit/ --cov=src --cov-report=html
```

### Test Results
- **Tests**: 112/112 passing ✅
- **Coverage**: 27.21% (unit tests only)
- **CI/CD**: GitHub Actions automated testing

## 🔒 Security Features

- **PII Detection**: Automatic detection and redaction of sensitive data
- **Rate Limiting**: Prevents abuse with configurable per-user limits
- **Content Filtering**: Input/output safety checks
- **Audit Logging**: Comprehensive tracking of all AI interactions
- **Secret Management**: Support for Azure Key Vault integration

## 📁 Project Structure

```
azure-ai-infra-platform/
├── src/
│   ├── api/              # API routes and schemas
│   ├── llm/              # LLM integration (OpenAI, prompts)
│   ├── rag/              # RAG implementation (Cognitive Search)
│   ├── guardrails/       # Safety and rate limiting
│   ├── monitoring/       # Metrics, logging, alerts
│   ├── config/           # Configuration management
│   └── main.py           # FastAPI application
├── tests/                # Unit and integration tests
├── docs/                 # Documentation
├── docker/               # Docker configurations
├── .github/workflows/    # CI/CD pipelines
└── requirements.txt      # Python dependencies
```

## 🎨 Screenshots

### Swagger UI - Complete API Documentation
![Swagger UI](docs/screenshots/swagger-ui.png)

Interactive Swagger UI showing all 30+ API endpoints organized by module:
- **Health & Monitoring** (5 endpoints)
- **Chat & AI** (2 endpoints)
- **RAG** (3 endpoints)
- **Guardrails** (8 endpoints)
- **Prompt Management** (8 endpoints)
- **Observability** (12 endpoints)

### Metrics Dashboard - Real-Time Monitoring
![Metrics Dashboard](docs/screenshots/metrics-dashboard.png)

Structured JSON metrics showing:
- API request counters and latency
- AI request tracking (tokens, cost, latency)
- RAG query performance metrics
- Guardrails violation tracking
- System resource usage

### Health Check - Dependency Status
![Health Check](docs/screenshots/health-check.png)

Multi-tier health monitoring:
- Application status
- Azure OpenAI service health
- Cognitive Search connectivity
- Key Vault integration status
- Response time metrics

**All screenshots available in** [docs/screenshots/](docs/screenshots/)

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Abdul Syed**
- GitHub: [syabdulr](https://github.com/syabdulr)
- Email: syabdulr6@gmail.com
- Role: AI Platform Engineer

## 🙏 Acknowledgments

- Azure OpenAI Service
- Azure Cognitive Search
- FastAPI framework
- Prometheus ecosystem

---

**Built with ❤️ for production AI workloads on Azure**