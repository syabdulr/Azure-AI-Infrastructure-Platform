"""
Pydantic schemas for API request and response models

This module contains all data models used for request validation and response serialization.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ErrorCode(str, Enum):
    """Error codes for different types of errors"""
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    INTERNAL_ERROR = "internal_error"
    AZURE_ERROR = "azure_error"


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error_code: ErrorCode = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "validation_error",
                "message": "Invalid request parameters",
                "details": {
                    "field": "max_tokens",
                    "reason": "must be between 1 and 4096"
                },
                "timestamp": "2026-07-25T12:00:00Z"
            }
        }


class HealthCheckStatus(str, Enum):
    """Health check status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class DependencyHealth(BaseModel):
    """Health status of a specific dependency"""
    name: str = Field(..., description="Dependency name")
    status: HealthCheckStatus = Field(..., description="Health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: HealthCheckStatus = Field(..., description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    version: str = Field(..., description="Application version")
    dependencies: List[DependencyHealth] = Field(default_factory=list, description="Dependency health status")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2026-07-25T12:00:00Z",
                "version": "1.0.0",
                "dependencies": [
                    {
                        "name": "azure_openai",
                        "status": "healthy",
                        "response_time_ms": 45.2
                    },
                    {
                        "name": "cognitive_search",
                        "status": "healthy",
                        "response_time_ms": 32.1
                    }
                ]
            }
        }


class ChatRequest(BaseModel):
    """Chat completion request model"""
    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    max_tokens: int = Field(1000, ge=1, le=4096, description="Maximum tokens in response")
    temperature: float = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    stream: bool = Field(False, description="Enable streaming response")

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError("Message cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the status of the AI platform?",
                "conversation_id": "conv-123",
                "max_tokens": 1000,
                "temperature": 0.7,
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """Chat completion response model"""
    response: str = Field(..., description="AI-generated response")
    model: str = Field(..., description="Model used (e.g., gpt-4)")
    conversation_id: str = Field(..., description="Conversation ID")
    tokens_used: int = Field(..., description="Total tokens used (prompt + completion)")
    prompt_tokens: int = Field(..., description="Tokens used in prompt")
    completion_tokens: int = Field(..., description="Tokens used in completion")
    cost: float = Field(..., description="Estimated cost in USD")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "The AI platform is running optimally with all systems healthy...",
                "model": "gpt-4",
                "conversation_id": "conv-123",
                "tokens_used": 150,
                "prompt_tokens": 50,
                "completion_tokens": 100,
                "cost": 0.003,
                "latency_ms": 234.5,
                "timestamp": "2026-07-25T12:00:00Z"
            }
        }


class RAGRequest(BaseModel):
    """RAG query request model"""
    query: str = Field(..., min_length=1, max_length=2000, description="Search query")
    top_k: int = Field(5, ge=1, le=10, description="Number of top results to return")
    include_citations: bool = Field(True, description="Include citation information")
    min_score: float = Field(0.5, ge=0.0, le=1.0, description="Minimum relevance score")
    context_window: int = Field(4000, ge=1000, le=16000, description="Maximum context length in tokens")

    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "query": "How do I deploy the AI platform to Azure?",
                "top_k": 5,
                "include_citations": True,
                "min_score": 0.5
            }
        }


class SourceDocument(BaseModel):
    """Source document model for RAG responses"""
    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    content: str = Field(..., description="Relevant content snippet")
    source: str = Field(..., description="Source (e.g., document path)")
    score: float = Field(..., description="Relevance score (0-1)")
    citation_id: Optional[str] = Field(None, description="Citation ID for referencing")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional document metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "doc-123",
                "title": "Deployment Guide",
                "content": "To deploy the AI platform, follow these steps...",
                "source": "/docs/deployment.md",
                "score": 0.92,
                "citation_id": "source-1",
                "metadata": {
                    "created_at": "2026-07-20",
                    "author": "Abdul Syed"
                }
            }
        }


class RAGResponse(BaseModel):
    """RAG query response model"""
    answer: str = Field(..., description="AI-generated answer based on retrieved documents")
    sources: List[SourceDocument] = Field(..., description="Retrieved source documents")
    query: str = Field(..., description="Original query")
    total_sources: int = Field(..., description="Total number of sources retrieved")
    answer_source: str = Field(..., description="Source of the answer (e.g., 'azure_openai')")
    latency_ms: float = Field(..., description="Response latency in milliseconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "answer": "To deploy the AI platform to Azure, follow these steps...",
                "sources": [
                    {
                        "id": "doc-123",
                        "title": "Deployment Guide",
                        "content": "To deploy the AI platform, follow these steps...",
                        "source": "/docs/deployment.md",
                        "score": 0.92,
                        "citation_id": "source-1"
                    }
                ],
                "query": "How do I deploy the AI platform to Azure?",
                "total_sources": 5,
                "answer_source": "azure_openai",
                "latency_ms": 312.4,
                "timestamp": "2026-07-25T12:00:00Z"
            }
        }


class MetricsResponse(BaseModel):
    """Application metrics response model"""
    request_count: int = Field(..., description="Total number of requests")
    total_tokens: int = Field(..., description="Total tokens used")
    total_cost: float = Field(..., description="Total cost in USD")
    avg_latency_ms: float = Field(..., description="Average request latency in milliseconds")
    error_rate: float = Field(..., description="Error rate (0-1)")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Metrics timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "request_count": 1250,
                "total_tokens": 150000,
                "total_cost": 4.50,
                "avg_latency_ms": 245.3,
                "error_rate": 0.02,
                "uptime_seconds": 86400.0,
                "timestamp": "2026-07-25T12:00:00Z"
            }
        }


class MonitoringStatus(BaseModel):
    """Monitoring status response model"""
    azure_openai_status: HealthCheckStatus = Field(..., description="Azure OpenAI status")
    cognitive_search_status: HealthCheckStatus = Field(..., description="Cognitive Search status")
    storage_status: HealthCheckStatus = Field(..., description="Storage status")
    key_vault_status: HealthCheckStatus = Field(..., description="Key Vault status")
    application_insights_status: HealthCheckStatus = Field(..., description="Application Insights status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Status timestamp")

    class Config:
        json_schema_extra = {
            "example": {
                "azure_openai_status": "healthy",
                "cognitive_search_status": "healthy",
                "storage_status": "healthy",
                "key_vault_status": "healthy",
                "application_insights_status": "healthy",
                "timestamp": "2026-07-25T12:00:00Z"
            }
        }


class StreamChunk(BaseModel):
    """Streaming response chunk model"""
    chunk: str = Field(..., description="Text chunk")
    done: bool = Field(False, description="Whether streaming is complete")
    tokens_generated: Optional[int] = Field(None, description="Total tokens generated so far")

    class Config:
        json_schema_extra = {
            "example": {
                "chunk": "The AI platform",
                "done": False,
                "tokens_generated": 4
            }
        }