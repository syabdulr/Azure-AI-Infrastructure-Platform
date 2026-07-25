"""Integration tests for chat API"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock


# ============================================================================
# Chat Completion Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestChatCompletion:
    """Test chat completion endpoint"""
    
    async def test_chat_completion_success(self, mock_azure_openai_client):
        """Test successful chat completion"""
        from src.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.llm.azure_openai_client.AzureOpenAIClient") as mock_client_class:
                # Setup mock
                mock_instance = MagicMock()
                mock_instance.chat_completion.return_value = {
                    "content": "Test response",
                    "finish_reason": "stop",
                    "usage": {
                        "prompt_tokens": 10,
                        "completion_tokens": 20,
                        "total_tokens": 30
                    },
                    "cost": 0.0006
                }
                mock_client_class.return_value = mock_instance
                
                # Make request
                response = await client.post(
                    "/chat",
                    json={
                        "message": "Hello",
                        "model": "gpt-4",
                        "temperature": 0.7,
                        "max_tokens": 1000
                    }
                )
                
                # Assert response
                assert response.status_code == 200
                data = response.json()
                assert data["content"] == "Test response"
                assert data["model"] == "gpt-4"
                assert "usage" in data
                assert "latency_ms" in data
    
    async def test_chat_completion_invalid_request(self):
        """Test chat completion with invalid request"""
        from src.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make invalid request (missing message)
            response = await client.post(
                "/chat",
                json={
                    "model": "gpt-4",
                    "temperature": 0.7
                }
            )
            
            # Assert error response
            assert response.status_code == 422
    
    async def test_chat_completion_ai_error(self, mock_azure_openai_client):
        """Test chat completion with AI service error"""
        from src.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.llm.azure_openai_client.AzureOpenAIClient") as mock_client_class:
                # Setup mock to raise error
                mock_instance = MagicMock()
                mock_instance.chat_completion.side_effect = Exception("AI service error")
                mock_client_class.return_value = mock_instance
                
                # Make request
                response = await client.post(
                    "/chat",
                    json={
                        "message": "Hello",
                        "model": "gpt-4"
                    }
                )
                
                # Assert error response
                assert response.status_code == 500


# ============================================================================
# Streaming Tests
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
class TestChatStreaming:
    """Test chat streaming endpoint"""
    
    async def test_chat_streaming_success(self, mock_azure_openai_client):
        """Test successful streaming chat"""
        from src.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.llm.azure_openai_client.AzureOpenAIClient") as mock_client_class:
                # Setup mock
                mock_instance = MagicMock()
                mock_instance.chat_completion_stream.return_value = [
                    {"content": "Hello ", "finish_reason": None},
                    {"content": "world!", "finish_reason": "stop"}
                ]
                mock_client_class.return_value = mock_instance
                
                # Make streaming request
                response = await client.post(
                    "/chat/stream",
                    json={
                        "message": "Hello",
                        "model": "gpt-4",
                        "stream": True
                    }
                )
                
                # Assert response
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream"
                
                # Read stream
                content = response.text
                assert "Hello" in content
                assert "world!" in content
    
    async def test_chat_streaming_error(self, mock_azure_openai_client):
        """Test streaming with error"""
        from src.main import app
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            with patch("src.llm.azure_openai_client.AzureOpenAIClient") as mock_client_class:
                # Setup mock to raise error
                mock_instance = MagicMock()
                mock_instance.chat_completion_stream.side_effect = Exception("Streaming error")
                mock_client_class.return_value = mock_instance
                
                # Make streaming request
                response = await client.post(
                    "/chat/stream",
                    json={
                        "message": "Hello",
                        "model": "gpt-4",
                        "stream": True
                    }
                )
                
                # Assert error response
                assert response.status_code == 500