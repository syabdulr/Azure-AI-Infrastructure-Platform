# Step 4: RAG Pipeline with Azure Cognitive Search - Build Plan

## 🎯 Step Overview

**Commit:** `feat: Implement complete RAG pipeline with Azure Cognitive Search`  
**Estimated Time:** 3 hours  
**Goal:** Build production-ready RAG pipeline with Azure Cognitive Search integration

---

## 🏗️ RAG Pipeline Architecture

```
┌─────────────┐
│   User      │
│  Query      │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Azure Cognitive│
│    Search       │
│                 │
│  • Vector Search│
│  • Hybrid Search│
│  • Semantic     │
│    Reranking    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Azure OpenAI   │
│  (GPT-4)        │
│                 │
│  • Context      │
│  • Prompt       │
│  • Generation   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Response +     │
│  Citations      │
└─────────────────┘
```

---

## 📋 Files to Update (3 files, ~1,500 lines)

### 1. Complete Azure Cognitive Search Client
- `src/rag/cognitive_search.py` (Update: +400 lines)
  - Hybrid search implementation
  - Vector search with HNSW
  - Semantic search
  - Batch operations

### 2. Complete RAG Endpoint
- `src/api/routes/rag.py` (Update: +500 lines)
  - Full RAG pipeline
  - Context building
  - Citation generation
  - Answer generation

### 3. Add Tests
- `tests/unit/test_cognitive_search.py` (New: 300 lines)
- `tests/integration/test_rag_pipeline.py` (New: 300 lines)

---

## 🎯 Key Features to Implement

### 1. Hybrid Search
```python
async def hybrid_search(
    query: str,
    top_k: int = 5,
    min_score: float = 0.5
) -> List[Dict[str, Any]]:
    """
    Perform hybrid search (vector + keyword + semantic)
    
    Steps:
    1. Generate query embedding
    2. Perform vector search (HNSW)
    3. Perform keyword search (BM25)
    4. Combine results (RRF - Reciprocal Rank Fusion)
    5. Apply semantic reranking
    6. Filter by min_score
    7. Return top_k results
    """
```

### 2. Vector Search
```python
async def vector_search(
    vector: List[float],
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform vector search with HNSW algorithm
    
    Features:
    - HNSW index for fast nearest neighbor search
    - Cosine similarity metric
    - Configurable ef_search parameter
    - Top-k selection
    """
```

### 3. Semantic Search
```python
async def semantic_search(
    query: str,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Perform semantic search with ranking
    
    Features:
    - Semantic understanding of query
    - Prioritized fields (content > title > metadata)
    - Captions for enhanced relevance
    """
```

### 4. Document Indexing
```python
async def index_document(
    document: Dict[str, Any]
) -> str:
    """
    Index a document with embeddings
    
    Steps:
    1. Process document (chunk if needed)
    2. Generate embeddings for chunks
    3. Create index entries with vectors
    4. Upload to Azure Cognitive Search
    5. Return document ID
    """
```

### 5. Batch Indexing
```python
async def batch_index_documents(
    documents: List[Dict[str, Any]],
    batch_size: int = 100
) -> List[str]:
    """
    Index multiple documents in batches
    
    Features:
    - Batch processing for efficiency
    - Progress tracking
    - Error handling per document
    - Bulk upload operations
    """
```

---

## 📊 RAG Pipeline Implementation

### Complete RAG Query Flow

```python
async def rag_query(query: str, top_k: int = 5) -> RAGResponse:
    """
    Complete RAG pipeline
    
    1. Retrieve documents (hybrid search)
    2. Build context from documents
    3. Generate answer with Azure OpenAI
    4. Generate citations
    5. Return response with sources
    """
    
    # Step 1: Retrieve documents
    search_results = await cognitive_search.hybrid_search(
        query=query,
        top_k=top_k
    )
    
    # Step 2: Build context
    context = build_context(search_results)
    
    # Step 3: Generate answer
    system_prompt = prompt_manager.render_template("rag_system")
    user_prompt = prompt_manager.render_template(
        "rag_user",
        context=context,
        question=query
    )
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    result = await openai_client.chat_completion(messages)
    
    # Step 4: Generate citations
    citations = generate_citations(search_results)
    
    # Step 5: Return response
    return RAGResponse(
        answer=result["response"],
        sources=search_results,
        query=query,
        total_sources=len(search_results),
        answer_source="azure_openai",
        latency_ms=result["latency_ms"]
    )
```

---

## 🔒 Security Features

1. **Secure Access**
   - Managed identity for Cognitive Search
   - Role-based access control
   - No hardcoded API keys

2. **Input Validation**
   - Query length limits
   - Top-k bounds checking
   - Score validation

3. **Content Safety**
   - Sanitization of retrieved content
   - PII detection
   - Sensitive content filtering

---

## 💰 Cost Optimization Features

1. **Embedding Caching**
   - Cache query embeddings
   - TTL-based invalidation
   - Redis support (future)

2. **Efficient Retrieval**
   - Hybrid search reduces API calls
   - Top-k selection limits context size
   - Semantic reranking improves accuracy

3. **Batch Operations**
   - Bulk document indexing
   - Reduced API overhead
   - Parallel processing

---

## 📊 API Enhancements

### Enhanced RAG Endpoint

```python
POST /rag/query
Content-Type: application/json

{
  "query": "How do I deploy the AI platform?",
  "top_k": 5,
  "min_score": 0.5,
  "include_citations": true,
  "use_semantic_search": true,
  "context_window": 4000
}

Response:
{
  "answer": "To deploy the AI platform to Azure, follow these steps...",
  "sources": [
    {
      "id": "doc-123",
      "title": "Deployment Guide",
      "content": "...",
      "source": "/docs/deployment.md",
      "score": 0.92,
      "citation_id": "[1]"
    }
  ],
  "query": "How do I deploy the AI platform?",
  "total_sources": 5,
  "answer_source": "azure_openai",
  "latency_ms": 312,
  "tokens_used": 850,
  "cost": 0.025
}
```

### New Indexing Endpoint

```python
POST /rag/index
Content-Type: application/json

{
  "document": {
    "title": "Deployment Guide",
    "content": "To deploy the AI platform...",
    "source": "/docs/deployment.md",
    "metadata": {
      "author": "Abdul Syed",
      "category": "deployment"
    }
  }
}

Response:
{
  "document_id": "doc-abc123",
  "status": "indexed",
  "chunks_indexed": 5,
  "embedding_cost": 0.0005,
  "latency_ms": 245
}
```

### New Batch Indexing Endpoint

```python
POST /rag/index/batch
Content-Type: application/json

{
  "documents": [
    {
      "title": "Guide 1",
      "content": "...",
      "source": "/docs/guide1.md"
    },
    {
      "title": "Guide 2",
      "content": "...",
      "source": "/docs/guide2.md"
    }
  ],
  "batch_size": 100
}

Response:
{
  "total_documents": 2,
  "successful": 2,
  "failed": 0,
  "total_chunks_indexed": 10,
  "total_embedding_cost": 0.001,
  "latency_ms": 512
}
```

---

## 🧪 Testing Strategy

### Unit Tests
- `test_hybrid_search.py`
  - Test vector search
  - Test keyword search
  - Test result fusion
  - Test semantic reranking

### Integration Tests
- `test_rag_pipeline.py`
  - Test end-to-end RAG
  - Test with real Azure services
  - Test citation generation

### Performance Tests
- Test search latency (< 500ms)
- Test indexing throughput (> 10 docs/sec)
- Test cost tracking accuracy

---

## 📝 Success Criteria

✅ Hybrid search implemented (vector + keyword + semantic)  
✅ Vector search with HNSW algorithm  
✅ Semantic search with prioritized fields  
✅ Document indexing with embeddings  
✅ Batch indexing support  
✅ Complete RAG pipeline (retrieve → generate → cite)  
✅ Citation generation  
✅ Context building  
✅ Enhanced RAG endpoint  
✅ New indexing endpoints  
✅ Unit tests for search functions  
✅ Integration tests for RAG pipeline  
✅ Performance benchmarks met

---

## 🚀 What This Will Add

**New Functionality:**
- ✅ Working RAG pipeline (not just foundation)
- ✅ Real hybrid search with Azure Cognitive Search
- ✅ Document indexing capabilities
- ✅ Citation generation
- ✅ Enhanced API endpoints

**Recruiter Impact:**
- ✅ Demonstrates complete RAG implementation
- ✅ Shows Azure Cognitive Search expertise
- ✅ Production-ready RAG pipeline
- ✅ Addresses Accenture "RAG" requirement directly

---

## 📊 Progress After Step 4

- **Files Updated:** 3 files (+1,200 lines)
- **Tests Added:** 2 files (600 lines)
- **Total New Code:** ~1,800 lines
- **Commits:** 4 total
- **Steps Complete:** 4/13 (30.8%)

---

## ⏭️ Ready to Build?

**Next Action:** Implement complete RAG pipeline

**Estimated Time:** 3 hours

**Type "yes" to start building Step 4!** 🚀