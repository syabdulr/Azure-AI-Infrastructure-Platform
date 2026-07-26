"""Integration tests for RAG API"""

from unittest.mock import MagicMock, patch

import pytest
from httpx import AsyncClient

# ============================================================================
# RAG Query Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestRAGQuery:
    """Test RAG query endpoint"""

    async def test_rag_query_success(self, sample_rag_request, mock_cognitive_search_client):
        """Test successful RAG query"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.rag.cognitive_search.CognitiveSearchClient") as mock_search_class:
                # Setup mock
                mock_instance = MagicMock()
                mock_instance.hybrid_search.return_value = [
                    {
                        "id": "doc-1",
                        "title": "Test Document",
                        "content": "Test content",
                        "score": 0.95,
                        "source": "/docs/test.md",
                    }
                ]
                mock_search_class.return_value = mock_instance

                # Make request
                response = await client.post("/rag/query", json=sample_rag_request)

                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                assert "sources" in data
                assert "query" in data
                assert data["query"] == "What is Azure AI?"

    async def test_rag_query_no_results(self):
        """Test RAG query with no results"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.rag.cognitive_search.CognitiveSearchClient") as mock_search_class:
                # Setup mock to return empty results
                mock_instance = MagicMock()
                mock_instance.hybrid_search.return_value = []
                mock_search_class.return_value = mock_instance

                # Make request
                response = await client.post(
                    "/rag/query", json={"query": "Unknown topic", "top_k": 5}
                )

                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert "answer" in data
                # Should still generate an answer even with no sources

    async def test_rag_query_invalid_request(self):
        """Test RAG query with invalid request"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make invalid request (missing query)
            response = await client.post("/rag/query", json={"top_k": 5, "include_citations": True})

            # Assert error response
            assert response.status_code == 422


# ============================================================================
# Document Indexing Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentIndexing:
    """Test document indexing endpoint"""

    async def test_index_document_success(self, sample_document, mock_cognitive_search_client):
        """Test successful document indexing"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.rag.cognitive_search.CognitiveSearchClient") as mock_search_class:
                # Setup mock
                mock_instance = MagicMock()
                mock_instance.index_document.return_value = {
                    "document_id": "doc-123",
                    "status": "indexed",
                    "chunks_indexed": 1,
                    "embedding_cost": 0.0005,
                }
                mock_search_class.return_value = mock_instance

                # Make request
                response = await client.post("/rag/index", json=sample_document)

                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "indexed"
                assert "document_id" in data

    async def test_batch_index_documents_success(
        self, sample_documents, mock_cognitive_search_client
    ):
        """Test batch document indexing"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.rag.cognitive_search.CognitiveSearchClient") as mock_search_class:
                # Setup mock
                mock_instance = MagicMock()
                mock_instance.batch_index_documents.return_value = {
                    "total_documents": 3,
                    "successful": 3,
                    "failed": 0,
                    "total_chunks_indexed": 3,
                    "total_embedding_cost": 0.0015,
                    "errors": [],
                }
                mock_search_class.return_value = mock_instance

                # Make request
                response = await client.post(
                    "/rag/index/batch", json={"documents": sample_documents, "batch_size": 100}
                )

                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert data["successful"] == 3
                assert data["failed"] == 0
