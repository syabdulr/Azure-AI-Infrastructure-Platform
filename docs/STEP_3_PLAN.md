# Step 3: AI Service Application - Build Plan

## 🎯 Step Overview

**Commit:** `feat: Build FastAPI AI service with Azure OpenAI integration`  
**Estimated Time:** 4 hours  
**Goal:** Create production-ready FastAPI application with Azure OpenAI, Azure Cognitive Search, and monitoring integration

---

## 🏗️ Application Architecture

```
src/
├── main.py                    # FastAPI application entry point
├── api/
│   ├── __init__.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py            # Chat completion endpoint
│   │   ├── rag.py             # RAG query endpoint
│   │   ├── health.py          # Health check endpoint
│   │   └── monitoring.py      # Metrics and status endpoint
│   └── schemas.py             # Pydantic models (request/response)
├── llm/
│   ├── __init__.py
│   ├── azure_openai_client.py # Azure OpenAI client wrapper
│   ├── prompt_manager.py      # Prompt template management
│   └── response_evaluator.py  # Response quality evaluation
├── rag/
│   ├── __init__.py
│   ├── cognitive_search.py    # Azure Cognitive Search client
│   ├── document_processor.py  # Document processing utilities
│   └── retrieval.py           # Retrieval strategies
├── monitoring/
│   ├── __init__.py
│   ├── metrics.py             # Metrics collection
│   ├── logging.py             # Structured logging
│   └── telemetry.py           # Azure Monitor integration
└── config/
    ├── __init__.py
    └── settings.py            # Configuration management
```

---

## 📋 Files to Create (21 files)

### 1. Application Entry Point
- `src/main.py` (150 lines)
  - FastAPI app initialization
  - Middleware configuration
  - Route registration
  - CORS configuration
  - Health checks
  - OpenAPI/Swagger configuration
  - Error handlers

### 2. API Routes (5 files)
- `src/api/__init__.py` (5 lines)
- `src/api/routes/__init__.py` (5 lines)
- `src/api/routes/chat.py` (180 lines)
  - POST /chat endpoint
  - Streaming support
  - Context management
  - Rate limiting
- `src/api/routes/rag.py` (200 lines)
  - POST /rag/query endpoint
  - Hybrid search (vector + keyword)
  - Semantic reranking
  - Citation generation
- `src/api/routes/health.py` (100 lines)
  - GET /health endpoint
  - Dependency health checks
  - Response time metrics
- `src/api/routes/monitoring.py` (120 lines)
  - GET /monitoring/metrics
  - GET /monitoring/status
  - Cost tracking

### 3. API Schemas
- `src/api/schemas.py` (250 lines)
  - ChatRequest, ChatResponse
  - RAGRequest, RAGResponse
  - HealthResponse, MetricsResponse
  - ErrorResponse

### 4. LLM Module (3 files)
- `src/llm/__init__.py` (5 lines)
- `src/llm/azure_openai_client.py` (280 lines)
  - Azure OpenAI client wrapper
  - Managed identity authentication
  - Retry logic with exponential backoff
  - Rate limiting
  - Cost tracking per request
  - Streaming support
  - Token counting
- `src/llm/prompt_manager.py` (150 lines)
  - Template management
  - Version control
  - Prompt validation
- `src/llm/response_evaluator.py` (120 lines)
  - Response quality metrics
  - Relevance scoring

### 5. RAG Module (4 files)
- `src/rag/__init__.py` (5 lines)
- `src/rag/cognitive_search.py` (200 lines)
  - Azure Cognitive Search client
  - Hybrid search implementation
  - Semantic reranking
  - Vector search
- `src/rag/document_processor.py` (120 lines)
  - Document ingestion
  - Chunking strategies
  - Metadata extraction
- `src/rag/retrieval.py` (150 lines)
  - Retrieval strategies
  - Relevance scoring
  - Citation generation

### 6. Monitoring Module (4 files)
- `src/monitoring/__init__.py` (5 lines)
- `src/monitoring/metrics.py` (180 lines)
  - Metrics collection
  - Request latency
  - Token usage
  - Cost tracking
- `src/monitoring/logging.py` (120 lines)
  - Structured logging
  - JSON format
  - Correlation IDs
- `src/monitoring/telemetry.py` (150 lines)
  - Azure Monitor integration
  - Application Insights
  - Distributed tracing

### 7. Configuration (2 files)
- `src/config/__init__.py` (5 lines)
- `src/config/settings.py` (200 lines)
  - Configuration management
  - Environment variables
  - Validation
  - Azure resource configuration

---

## 🎯 Key Features to Implement

### 1. Azure OpenAI Integration
- ✅ Managed identity authentication (no hardcoded keys)
- ✅ GPT-4 chat completions
- ✅ Text-embedding-ada-002 for embeddings
- ✅ Retry logic with exponential backoff
- ✅ Rate limiting
- ✅ Cost tracking per request
- ✅ Streaming responses
- ✅ Token counting

### 2. Azure Cognitive Search Integration
- ✅ Hybrid search (vector + keyword)
- ✅ Semantic reranking
- ✅ Vector search with HNSW
- ✅ Citation generation
- ✅ Relevance scoring
- ✅ Top-k selection

### 3. Production-Ready API
- ✅ FastAPI with async support
- ✅ Pydantic validation
- ✅ OpenAPI/Swagger documentation
- ✅ CORS configuration
- ✅ Error handlers
- ✅ Rate limiting
- ✅ Health checks

### 4. Monitoring & Observability
- ✅ Request metrics (latency, tokens, cost)
- ✅ Structured logging (JSON format)
- ✅ Azure Monitor integration
- ✅ Application Insights telemetry
- ✅ Distributed tracing
- ✅ Custom dashboards support

### 5. Configuration Management
- ✅ Environment variable support
- ✅ Azure Key Vault integration
- ✅ Configuration validation
- ✅ Default values
- ✅ Azure resource configuration

---

## 🔒 Security Features

1. **Managed Identity Authentication**
   - No hardcoded API keys
   - Azure Active Directory integration
   - Automatic token refresh

2. **Environment Variable Security**
   - Sensitive data from Azure Key Vault
   - No secrets in code
   - Secure credential flow

3. **Input Validation**
   - Pydantic schemas
   - Type checking
   - Length limits
   - Sanitization

4. **Rate Limiting**
   - Per-user rate limiting
   - Token-based rate limits
   - Sliding window algorithm

---

## 💰 Cost Optimization Features

1. **Token Tracking**
   - Count input/output tokens
   - Calculate cost per request
   - Aggregate cost metrics

2. **Caching Strategy**
   - Embedding caching (in Step 4)
   - Response caching (future)
   - Cost-aware routing

3. **Efficient Queries**
   - Hybrid search optimization
   - Top-k selection
   - Relevance thresholds

---

## 📊 API Endpoints

### 1. POST /chat
**Purpose:** Chat completion with GPT-4

**Request:**
```json
{
  "message": "What is the status of the AI platform?",
  "conversation_id": "optional-conversation-id",
  "max_tokens": 1000,
  "temperature": 0.7
}
```

**Response:**
```json
{
  "response": "The AI platform is running optimally...",
  "model": "gpt-4",
  "tokens_used": 150,
  "cost": 0.003,
  "latency_ms": 234
}
```

### 2. POST /rag/query
**Purpose:** RAG query with Azure Cognitive Search

**Request:**
```json
{
  "query": "How do I deploy the AI platform?",
  "top_k": 5,
  "include_citations": true
}
```

**Response:**
```json
{
  "answer": "To deploy the AI platform, follow these steps...",
  "sources": [
    {
      "title": "Deployment Guide",
      "content": "...",
      "score": 0.92,
      "citation_id": "source-1"
    }
  ],
  "latency_ms": 312
}
```

### 3. GET /health
**Purpose:** Health check endpoint

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-25T12:00:00Z",
  "dependencies": {
    "azure_openai": "healthy",
    "cognitive_search": "healthy",
    "key_vault": "healthy"
  },
  "version": "1.0.0"
}
```

### 4. GET /monitoring/metrics
**Purpose:** Application metrics

**Response:**
```json
{
  "request_count": 1250,
  "total_tokens": 150000,
  "total_cost": 4.50,
  "avg_latency_ms": 245,
  "error_rate": 0.02
}
```

---

## 🧪 Testing Strategy

### Unit Tests (Mocking)
- `tests/unit/test_azure_openai_client.py`
- `tests/unit/test_cognitive_search.py`
- `tests/unit/test_prompt_manager.py`

### Integration Tests (Real Azure services)
- `tests/integration/test_azure_integration.py`
- `tests/integration/test_rag_pipeline.py`

### E2E Tests (Full pipeline)
- `tests/e2e/test_full_chat_pipeline.py`
- `tests/e2e/test_full_rag_pipeline.py`

---

## 📝 Success Criteria

✅ All 21 files created (2,500+ lines)  
✅ FastAPI app starts without errors  
✅ Azure OpenAI client authenticates with managed identity  
✅ Cognitive Search client connects to Azure Search  
✅ Health check endpoint returns 200  
✅ Chat endpoint responds with GPT-4 completions  
✅ RAG endpoint returns hybrid search results  
✅ Monitoring endpoint returns metrics  
✅ Structured logging works (JSON format)  
✅ Azure Monitor integration works  
✅ Configuration loads from environment variables  
✅ CI/CD pipeline passes (Python tests)

---

## 🚀 What This Will Fix

**CI/CD Pipeline:**
- ✅ Python code exists → tests will pass
- ✅ Application can be tested
- ✅ Green checks on GitHub Actions

**Repository:**
- ✅ Fully functional application
- ✅ Production-ready API
- ✅ Demonstrates Azure OpenAI integration
- ✅ Shows monitoring and observability

---

## 📊 Progress After Step 3

- **Files Created:** 21 files (~2,500 lines)
- **Commits:** 3 total
- **Steps Complete:** 3/13 (23.1%)
- **CI/CD:** ✅ Passing (green checks)

---

## ⏭️ Ready to Build?

**All code is already committed to GitHub** (2 commits, up to date).

**Next Action:** Create 21 files for the AI Service Application

**Estimated Time:** 4 hours

**Type "yes" to start building Step 3!** 🚀