"""
RAG routes for Azure AI Infrastructure Platform
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime
import logging
import uuid

from src.api.schemas import RAGRequest, RAGResponse, SourceDocument, ErrorCode, ErrorResponse
from src.config.settings import get_settings
from src.api.routes.monitoring import record_request_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGResponse)
async def rag_query(request: RAGRequest) -> RAGResponse:
    """
    RAG query endpoint using Azure Cognitive Search and Azure OpenAI

    Complete RAG pipeline:
    1. Retrieve documents using hybrid search
    2. Build context from retrieved documents
    3. Generate answer using Azure OpenAI
    4. Generate citations

    Args:
        request: RAGRequest with query, top_k, include_citations, min_score

    Returns:
        RAGResponse with answer, sources, query, total_sources, latency

    Raises:
        HTTPException: If query fails
    """
    start_time = datetime.utcnow()
    settings = get_settings()
    query_id = str(uuid.uuid4())
    
    try:
        # Step 1: Retrieve documents using hybrid search
        from src.rag.cognitive_search import CognitiveSearchClient
        search_client = CognitiveSearchClient()
        
        search_results = await search_client.hybrid_search(
            query=request.query,
            top_k=request.top_k,
            min_score=request.min_score
        )
        
        if not search_results:
            # Return response indicating no sources found
            latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            record_request_metrics(
                tokens=0,
                cost=0.0,
                latency_ms=latency_ms,
                error=False
            )
            
            return RAGResponse(
                answer="I couldn't find any relevant information in the knowledge base to answer your query.",
                sources=[],
                query=request.query,
                total_sources=0,
                answer_source="azure_openai",
                latency_ms=latency_ms,
                timestamp=datetime.utcnow()
            )
        
        # Step 2: Build context from retrieved documents
        context = _build_context(search_results, request.context_window)
        
        # Step 3: Generate answer using Azure OpenAI
        from src.llm.azure_openai_client import AzureOpenAIClient
        openai_client = AzureOpenAIClient()
        
        system_prompt = _get_system_prompt()
        user_prompt = _get_user_prompt(request.query, context)
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        result = await openai_client.chat_completion(
            messages=messages,
            max_tokens=2000,
            temperature=0.7
        )
        
        answer = result["response"]
        tokens_used = result["tokens_used"]
        cost = result["cost"]
        
        # Step 4: Generate citations if requested
        sources = []
        if request.include_citations:
            sources = _generate_citations(search_results)
        else:
            sources = [
                SourceDocument(
                    id=doc.get("id", ""),
                    title=doc.get("title", ""),
                    content=doc.get("content", ""),
                    source=doc.get("source", ""),
                    score=doc.get("score", 0),
                    citation_id="",
                    metadata=doc.get("metadata", {})
                )
                for doc in search_results
            ]
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record metrics
        record_request_metrics(
            tokens=tokens_used,
            cost=cost,
            latency_ms=latency_ms,
            error=False
        )
        
        return RAGResponse(
            answer=answer,
            sources=sources,
            query=request.query,
            total_sources=len(sources),
            answer_source="azure_openai",
            latency_ms=latency_ms,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Record error metrics
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.AZURE_ERROR,
                message=f"RAG query failed: {str(e)}",
                details={"query": request.query},
                timestamp=datetime.utcnow()
            )
        )


@router.post("/index")
async def index_document(
    document: dict
) -> dict:
    """
    Index a document with embeddings

    Args:
        document: Document data with 'title', 'content', 'source', 'metadata'

    Returns:
        Dictionary with document_id, status, chunks_indexed, embedding_cost, latency

    Raises:
        HTTPException: If indexing fails
    """
    start_time = datetime.utcnow()
    settings = get_settings()
    
    try:
        # Validate document structure
        if not document.get("content"):
            raise HTTPException(
                status_code=400,
                detail="Document must have 'content' field"
            )
        
        # Index document
        from src.rag.cognitive_search import CognitiveSearchClient
        search_client = CognitiveSearchClient()
        
        document_id = await search_client.index_document(document)
        
        # Calculate embedding cost (approximate)
        content_length = len(document.get("content", ""))
        embedding_cost = (content_length / 1000) * 0.0001  # $0.0001 per 1K tokens
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "document_id": document_id,
            "status": "indexed",
            "chunks_indexed": 1,
            "embedding_cost": embedding_cost,
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Document indexing failed",
                "message": str(e)
            }
        )


@router.post("/index/batch")
async def batch_index_documents(
    documents: list,
    batch_size: int = 100
) -> dict:
    """
    Index multiple documents in batches

    Args:
        documents: List of documents to index
        batch_size: Batch size for processing (default: 100)

    Returns:
        Dictionary with total_documents, successful, failed, total_chunks_indexed,
                total_embedding_cost, latency

    Raises:
        HTTPException: If batch indexing fails
    """
    start_time = datetime.utcnow()
    settings = get_settings()
    
    try:
        # Validate documents
        if not documents:
            raise HTTPException(
                status_code=400,
                detail="Documents list cannot be empty"
            )
        
        # Index documents in batch
        from src.rag.cognitive_search import CognitiveSearchClient
        search_client = CognitiveSearchClient()
        
        stats = await search_client.batch_index_documents(
            documents=documents,
            batch_size=batch_size
        )
        
        # Calculate total embedding cost (approximate)
        total_content_length = sum(
            len(doc.get("content", "")) for doc in documents
        )
        total_embedding_cost = (total_content_length / 1000) * 0.0001
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        return {
            "total_documents": stats["total_documents"],
            "successful": stats["successful"],
            "failed": stats["failed"],
            "total_chunks_indexed": stats["total_chunks_indexed"],
            "total_embedding_cost": total_embedding_cost,
            "errors": stats["errors"],
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Batch indexing failed: {e}")
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Batch indexing failed",
                "message": str(e)
            }
        )


def _build_context(
    search_results: List[Dict[str, Any]],
    context_window: int = 4000
) -> str:
    """
    Build context string from search results

    Args:
        search_results: List of search results
        context_window: Maximum context length in tokens

    Returns:
        Formatted context string
    """
    context_parts = []
    current_length = 0
    
    for i, result in enumerate(search_results):
        title = result.get("title", "")
        content = result.get("content", "")
        
        # Format source with citation marker
        source = f"[Source {i+1}: {title}]\n{content}\n"
        
        # Check if adding this source exceeds context window
        if current_length + len(source) > context_window:
            break
        
        context_parts.append(source)
        current_length += len(source)
    
    return "\n".join(context_parts)


def _get_system_prompt() -> str:
    """
    Get system prompt for RAG

    Returns:
        System prompt string
    """
    return """You are a helpful AI assistant that answers questions based on the provided context.

Your task:
1. Carefully read the provided context from the knowledge base
2. Answer the user's question based ONLY on the provided context
3. If the context doesn't contain enough information to answer the question, say so
4. Provide clear, concise answers
5. When relevant, reference the sources you used in your answer (e.g., "According to Source 1...")
6. Do not make up information or use outside knowledge beyond the provided context

Remember:
- Accuracy is more important than completeness
- It's okay to say "I don't have enough information to answer this question"
- Always ground your answers in the provided sources"""


def _get_user_prompt(query: str, context: str) -> str:
    """
    Get user prompt for RAG

    Args:
        query: User's query
        context: Retrieved context

    Returns:
        User prompt string
    """
    return f"""Context from the knowledge base:
{context}

Question: {query}

Based on the provided context, answer the question. If the context doesn't contain enough information, say so."""


def _generate_citations(search_results: List[Dict[str, Any]]) -> List[SourceDocument]:
    """
    Generate citations from search results

    Args:
        search_results: List of search results

    Returns:
        List of SourceDocument objects with citation IDs
    """
    sources = []
    
    for i, result in enumerate(search_results):
        sources.append(SourceDocument(
            id=result.get("id", ""),
            title=result.get("title", ""),
            content=result.get("content", ""),
            source=result.get("source", ""),
            score=result.get("score", 0),
            citation_id=f"[{i+1}]",
            metadata=result.get("metadata", {})
        ))
    
    return sources