"""Pytest configuration and fixtures for Azure AI Infrastructure Platform"""

import pytest
from datetime import datetime
from typing import Dict, Any
from unittest.mock import Mock, AsyncMock, MagicMock


# ============================================================================
# Pytest Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow running tests"
    )
    config.addinivalue_line(
        "markers", "azure: Tests requiring Azure services"
    )
    config.addinivalue_line(
        "markers", "mock: Tests using mocks"
    )


# ============================================================================
# Fixtures - Configuration
# ============================================================================

@pytest.fixture
def app_config() -> Dict[str, Any]:
    """Application configuration for testing"""
    return {
        "app_name": "Azure AI Infrastructure Platform",
        "app_version": "1.0.0",
        "debug": True,
        "host": "127.0.0.1",
        "port": 8000,
        "log_level": "INFO",
        "reload": False
    }


@pytest.fixture
def azure_config() -> Dict[str, Any]:
    """Azure configuration for testing"""
    return {
        "subscription_id": "test-subscription-id",
        "resource_group": "test-rg",
        "location": "eastus",
        "openai": {
            "endpoint": "https://test.openai.azure.com",
            "api_version": "2024-02-01",
            "deployment_name": "gpt-4",
            "model_name": "gpt-4"
        },
        "cognitive_search": {
            "endpoint": "https://test.search.windows.net",
            "index_name": "test-index",
            "api_version": "2023-11-01"
        }
    }


# ============================================================================
# Fixtures - Mock Azure Services
# ============================================================================

@pytest.fixture
def mock_azure_openai_client():
    """Mock Azure OpenAI client"""
    client = MagicMock()
    
    # Mock chat completion
    client.chat.completions.create.return_value = MagicMock(
        id="test-chat-id",
        created=int(datetime.utcnow().timestamp()),
        model="gpt-4",
        choices=[MagicMock(
            message=MagicMock(
                role="assistant",
                content="Test response"
            ),
            finish_reason="stop",
            index=0
        )],
        usage=MagicMock(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
    )
    
    # Mock embedding
    client.embeddings.create.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5] * 3072)]
    )
    
    return client


@pytest.fixture
def mock_cognitive_search_client():
    """Mock Azure Cognitive Search client"""
    client = MagicMock()
    
    # Mock search results
    client.search.return_value = [
        MagicMock(
            id="doc-1",
            title="Test Document",
            content="Test content for searching",
            score=0.95
        ),
        MagicMock(
            id="doc-2",
            title="Another Document",
            content="More test content",
            score=0.85
        )
    ]
    
    return client


# ============================================================================
# Fixtures - Sample Data
# ============================================================================

@pytest.fixture
def sample_chat_request() -> Dict[str, Any]:
    """Sample chat request"""
    return {
        "message": "Hello, how are you?",
        "model": "gpt-4",
        "temperature": 0.7,
        "max_tokens": 1000,
        "stream": False
    }


@pytest.fixture
def sample_rag_request() -> Dict[str, Any]:
    """Sample RAG request"""
    return {
        "query": "What is Azure AI?",
        "top_k": 5,
        "include_citations": True,
        "min_score": 0.5,
        "context_window": 4000
    }


@pytest.fixture
def sample_document() -> Dict[str, Any]:
    """Sample document for indexing"""
    return {
        "title": "Azure AI Overview",
        "content": "Azure AI is a comprehensive platform for building intelligent applications...",
        "source": "/docs/azure-ai.md",
        "metadata": {
            "author": "Abdul Syed",
            "category": "documentation"
        }
    }


@pytest.fixture
def sample_documents() -> list:
    """Sample documents for batch indexing"""
    return [
        {
            "title": "Document 1",
            "content": "Content for document 1",
            "source": "/docs/doc1.md"
        },
        {
            "title": "Document 2",
            "content": "Content for document 2",
            "source": "/docs/doc2.md"
        },
        {
            "title": "Document 3",
            "content": "Content for document 3",
            "source": "/docs/doc3.md"
        }
    ]


# ============================================================================
# Fixtures - Test Utilities
# ============================================================================

@pytest.fixture
def mock_settings():
    """Mock application settings"""
    settings = MagicMock()
    settings.app_name = "Azure AI Infrastructure Platform"
    settings.app_version = "1.0.0"
    settings.debug = True
    settings.host = "127.0.0.1"
    settings.port = 8000
    settings.log_level = "INFO"
    settings.reload = False
    return settings


@pytest.fixture
def async_mock():
    """Create async mock function"""
    return AsyncMock()


# ============================================================================
# Fixtures - Metrics
# ============================================================================

@pytest.fixture
def sample_metrics() -> Dict[str, Any]:
    """Sample metrics for testing"""
    return {
        "counters": {
            "api_requests_total": {"value": 1000},
            "ai_requests_total": {"value": 500}
        },
        "gauges": {
            "active_connections": {"value": 50},
            "ai_error_rate": {"value": 0.05}
        },
        "histograms": {
            "api_request_duration_ms": {
                "count": 1000,
                "sum": 50000,
                "buckets": {
                    "5ms": 100,
                    "10ms": 300,
                    "50ms": 800,
                    "100ms": 950,
                    "500ms": 990,
                    "1000ms": 1000
                }
            }
        },
        "summaries": {
            "api_response_time_ms": {
                "count": 1000,
                "sum": 50000,
                "quantiles": {
                    "0.5": 45,
                    "0.9": 95,
                    "0.95": 120,
                    "0.99": 200
                }
            }
        }
    }


# ============================================================================
# Fixtures - Alerts
# ============================================================================

@pytest.fixture
def sample_alert() -> Dict[str, Any]:
    """Sample alert for testing"""
    return {
        "id": "alert-123",
        "rule_name": "high_error_rate",
        "value": 0.95,
        "threshold": 0.90,
        "message": "Error rate exceeded 90%",
        "severity": "critical",
        "context": {
            "metric": "ai_error_rate",
            "condition": "gt"
        },
        "triggered_at": "2026-07-25T12:00:00Z",
        "active": True
    }


# ============================================================================
# Fixtures - Logs
# ============================================================================

@pytest.fixture
def sample_logs() -> list:
    """Sample logs for testing"""
    return [
        {
            "timestamp": "2026-07-25T12:00:00Z",
            "level": "INFO",
            "message": "API request received",
            "source": "api",
            "context": {
                "endpoint": "/chat",
                "user_id": "user-123"
            }
        },
        {
            "timestamp": "2026-07-25T12:01:00Z",
            "level": "WARNING",
            "message": "Rate limit approaching",
            "source": "guardrails",
            "context": {
                "user_id": "user-123",
                "remaining": 5
            }
        },
        {
            "timestamp": "2026-07-25T12:02:00Z",
            "level": "ERROR",
            "message": "AI request failed",
            "source": "llm",
            "context": {
                "error": "Connection timeout",
                "retry_count": 3
            }
        }
    ]


# ============================================================================
# Helpers
# ============================================================================

def create_mock_response(
    status_code: int = 200,
    json_data: Dict[str, Any] = None
) -> MagicMock:
    """Create mock HTTP response
    
    Args:
        status_code: HTTP status code
        json_data: Response JSON data
        
    Returns:
        Mock response object
    """
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.text = str(json_data or "")
    return response


def create_test_user(
    user_id: str = "test-user-123",
    email: str = "test@example.com"
) -> Dict[str, Any]:
    """Create test user data
    
    Args:
        user_id: User ID
        email: User email
        
    Returns:
        User data dictionary
    """
    return {
        "id": user_id,
        "email": email,
        "name": "Test User",
        "created_at": datetime.utcnow().isoformat()
    }