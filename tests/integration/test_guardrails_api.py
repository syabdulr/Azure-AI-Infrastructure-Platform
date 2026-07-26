"""Integration tests for guardrails API"""

import pytest
from httpx import AsyncClient

# ============================================================================
# Input Safety Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestInputSafety:
    """Test input safety checks"""

    async def test_check_input_safe(self):
        """Test checking safe input"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/guardrails/check-input",
                json={"text": "Hello, how are you?", "user_id": "user-123", "endpoint": "/chat"},
            )

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert data["is_safe"] is True
            assert data["blocked"] is False

    async def test_check_input_with_pii(self):
        """Test checking input with PII"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/guardrails/check-input",
                json={
                    "text": "My email is user@example.com",
                    "user_id": "user-123",
                    "endpoint": "/chat",
                },
            )

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert "pii_detected" in data
            assert "email" in data["pii_detected"]

    async def test_check_input_harmful_content(self):
        """Test checking input with harmful content"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/guardrails/check-input",
                json={"text": "I want to make a bomb", "user_id": "user-123", "endpoint": "/chat"},
            )

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert data["is_safe"] is False
            assert data["blocked"] is True


# ============================================================================
# Output Safety Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestOutputSafety:
    """Test output safety checks"""

    async def test_check_output_safe(self):
        """Test checking safe output"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/guardrails/check-output",
                json={
                    "text": "Azure AI is a comprehensive platform",
                    "user_id": "user-123",
                    "query": "What is Azure AI?",
                },
            )

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert data["is_safe"] is True
            assert data["blocked"] is False

    async def test_check_output_with_pii(self):
        """Test checking output with PII"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/guardrails/check-output",
                json={"text": "Contact user@example.com for more info", "user_id": "user-123"},
            )

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert "pii_detected" in data
            assert "email" in data["pii_detected"]


# ============================================================================
# Rate Limiting Tests
# ============================================================================


@pytest.mark.integration
@pytest.mark.asyncio
class TestRateLimiting:
    """Test rate limiting"""

    async def test_get_rate_limit_status(self):
        """Test getting rate limit status"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/guardrails/limits/user-123")

            # Assert response
            assert response.status_code == 200
            data = response.json()
            assert "user_id" in data
            assert "overall" in data
            assert "endpoints" in data

    async def test_rate_limit_exceeded(self):
        """Test rate limit exceeded"""
        from src.main import app

        async with AsyncClient(app=app, base_url="http://test") as client:
            # Make many requests to exceed rate limit
            for _ in range(100):
                await client.post(
                    "/guardrails/check-input",
                    json={
                        "text": "Test message",
                        "user_id": "rate-limited-user",
                        "endpoint": "/chat",
                    },
                )

            # This request should be rate limited
            response = await client.post(
                "/guardrails/check-input",
                json={"text": "Test message", "user_id": "rate-limited-user", "endpoint": "/chat"},
            )

            # Assert response
            data = response.json()
            assert data["blocked"] is True
            assert data["block_reason"] == "rate_limit_exceeded"
