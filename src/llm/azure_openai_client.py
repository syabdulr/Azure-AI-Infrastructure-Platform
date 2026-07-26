"""
Azure OpenAI client wrapper for Azure AI Infrastructure Platform

This module provides a production-ready Azure OpenAI client with:
- Managed identity authentication
- Retry logic with exponential backoff
- Rate limiting
- Cost tracking per request
- Streaming support
- Token counting
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import APIConnectionError, APIError, APITimeoutError, AsyncAzureOpenAI, RateLimitError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class AzureOpenAIClient:
    """Production-ready Azure OpenAI client with comprehensive features"""

    def __init__(self):
        """Initialize Azure OpenAI client with managed identity authentication"""
        self.settings = get_settings()
        self.client: Optional[AsyncAzureOpenAI] = None
        self._initialize_client()
        self._rate_limiter = RateLimiter(
            max_requests_per_minute=self.settings.rate_limit_requests_per_minute,
            burst=self.settings.rate_limit_burst,
        )
        self._cost_tracker = CostTracker(
            gpt4_input_cost=self.settings.gpt4_input_cost_per_1k,
            gpt4_output_cost=self.settings.gpt4_output_cost_per_1k,
            embedding_cost=self.settings.embedding_cost_per_1k,
        )

    def _initialize_client(self):
        """Initialize Azure OpenAI client"""
        try:
            if self.settings.azure_client_id:
                # Use managed identity authentication
                from azure.identity import DefaultAzureCredential, get_bearer_token_provider

                credential = DefaultAzureCredential()
                token_provider = get_bearer_token_provider(
                    credential, "https://cognitiveservices.azure.com/.default"
                )
                self.client = AsyncAzureOpenAI(
                    api_version=self.settings.azure_openai_api_version,
                    azure_ad_token_provider=token_provider,
                    azure_endpoint=self.settings.azure_openai_endpoint,
                )
            elif self.settings.azure_openai_api_key:
                # Use API key authentication
                self.client = AsyncAzureOpenAI(
                    api_version=self.settings.azure_openai_api_version,
                    api_key=self.settings.azure_openai_api_key,
                    azure_endpoint=self.settings.azure_openai_endpoint,
                )
            else:
                raise ValueError(
                    "Either azure_client_id or azure_openai_api_key must be configured"
                )

            logger.info("Azure OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Azure OpenAI client: {e}")
            raise

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((APITimeoutError, APIError)),
    )
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Get chat completion from GPT-4

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens in response (default from settings)
            temperature: Sampling temperature (default from settings)
            stream: Enable streaming response

        Returns:
            Dictionary with response, tokens used, cost, and latency
        """
        # Rate limiting
        await self._rate_limiter.acquire()

        start_time = time.time()

        try:
            max_tokens = max_tokens or self.settings.chat_max_tokens_default
            temperature = temperature or self.settings.chat_temperature_default

            response = await self.client.chat.completions.create(
                model=self.settings.azure_openai_chat_deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=stream,
            )

            if stream:
                # Handle streaming response
                return {
                    "response": response,  # Will be an async generator
                    "stream": True,
                    "model": self.settings.azure_openai_chat_deployment,
                }
            else:
                # Handle non-streaming response
                result = response.choices[0].message.content
                prompt_tokens = response.usage.prompt_tokens
                completion_tokens = response.usage.completion_tokens
                total_tokens = response.usage.total_tokens

                # Calculate cost
                cost = self._cost_tracker.calculate_cost(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    model=self.settings.azure_openai_chat_deployment,
                )

                latency_ms = (time.time() - start_time) * 1000

                logger.info(
                    f"Chat completion completed - "
                    f"tokens: {total_tokens}, cost: ${cost:.4f}, latency: {latency_ms:.2f}ms"
                )

                return {
                    "response": result,
                    "model": self.settings.azure_openai_chat_deployment,
                    "tokens_used": total_tokens,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": cost,
                    "latency_ms": latency_ms,
                }

        except RateLimitError as e:
            logger.warning(f"Rate limit exceeded: {e}")
            raise
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            raise

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Get streaming chat completion from GPT-4

        Args:
            messages: List of message dictionaries with 'role' and 'content'
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Yields:
            Text chunks from the streaming response
        """
        # Rate limiting
        await self._rate_limiter.acquire()

        max_tokens = max_tokens or self.settings.chat_max_tokens_default
        temperature = temperature or self.settings.chat_temperature_default

        try:
            stream = await self.client.chat.completions.create(
                model=self.settings.azure_openai_chat_deployment,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Streaming chat completion failed: {e}")
            raise

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for a list of texts

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        # Rate limiting
        await self._rate_limiter.acquire()

        start_time = time.time()

        try:
            response = await self.client.embeddings.create(
                model=self.settings.azure_openai_embedding_deployment, input=texts
            )

            embeddings = [item.embedding for item in response.data]
            total_tokens = response.usage.total_tokens

            # Calculate cost
            cost = self._cost_tracker.calculate_cost(
                prompt_tokens=total_tokens,
                completion_tokens=0,
                model=self.settings.azure_openai_embedding_deployment,
            )

            latency_ms = (time.time() - start_time) * 1000

            logger.info(
                f"Embeddings generated - "
                f"texts: {len(texts)}, tokens: {total_tokens}, cost: ${cost:.4f}, latency: {latency_ms:.2f}ms"
            )

            return embeddings

        except Exception as e:
            logger.error(f"Embeddings generation failed: {e}")
            raise

    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of Azure OpenAI service

        Returns:
            Dictionary with health status and response time
        """
        start_time = time.time()

        try:
            # Simple health check with minimal request
            await self.client.chat.completions.create(
                model=self.settings.azure_openai_chat_deployment,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=1,
            )

            response_time_ms = (time.time() - start_time) * 1000

            return {"status": "healthy", "response_time_ms": response_time_ms}

        except Exception as e:
            logger.error(f"Azure OpenAI health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def get_total_cost(self) -> float:
        """Get total cost accumulated by this client"""
        return self._cost_tracker.total_cost

    def get_request_count(self) -> int:
        """Get total number of requests made by this client"""
        return self._cost_tracker.request_count


class RateLimiter:
    """Token bucket rate limiter"""

    def __init__(self, max_requests_per_minute: int, burst: int):
        self.max_requests_per_minute = max_requests_per_minute
        self.burst = burst
        self.tokens = burst
        self.last_update = time.time()
        self.lock = asyncio.Lock()

    async def acquire(self):
        """Acquire a token from the rate limiter"""
        async with self.lock:
            now = time.time()
            elapsed = now - self.last_update

            # Refill tokens based on elapsed time
            tokens_to_add = elapsed * (self.max_requests_per_minute / 60.0)
            self.tokens = min(self.burst, self.tokens + tokens_to_add)
            self.last_update = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) * (60.0 / self.max_requests_per_minute)
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class CostTracker:
    """Track API costs per request"""

    def __init__(self, gpt4_input_cost: float, gpt4_output_cost: float, embedding_cost: float):
        self.gpt4_input_cost = gpt4_input_cost
        self.gpt4_output_cost = gpt4_output_cost
        self.embedding_cost = embedding_cost
        self.total_cost = 0.0
        self.request_count = 0

    def calculate_cost(self, prompt_tokens: int, completion_tokens: int, model: str) -> float:
        """Calculate cost for a request"""
        if model == "gpt-4":
            cost = (prompt_tokens / 1000.0) * self.gpt4_input_cost + (
                completion_tokens / 1000.0
            ) * self.gpt4_output_cost
        elif "embedding" in model:
            cost = (prompt_tokens / 1000.0) * self.embedding_cost
        else:
            cost = 0.0

        self.total_cost += cost
        self.request_count += 1

        return cost
