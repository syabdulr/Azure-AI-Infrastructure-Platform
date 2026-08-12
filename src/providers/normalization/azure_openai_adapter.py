"""Azure OpenAI response adapter."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .adapter import ResponseAdapter
from .models import LogProb, NormalizationResult, NormalizedResponse, ToolCall, UsageStatistics


class AzureOpenAIAdapter(ResponseAdapter):
    """Adapter for normalizing Azure OpenAI API responses."""

    def __init__(self) -> None:
        """Initialize Azure OpenAI adapter."""
        super().__init__("azure_openai")
        self.supports_tool_calls = True
        self.supports_logprobs = True
        self.supports_streaming = True

    def normalize(
        self,
        raw_response: Dict[str, Any],
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_per_1k: float,
    ) -> NormalizationResult:
        """
        Normalize Azure OpenAI response.

        Args:
            raw_response: Raw Azure OpenAI API response
            model_name: Model name
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            cost_per_1k: Cost per 1k tokens

        Returns:
            NormalizationResult
        """
        import time

        start_time = time.time()

        warnings: List[str] = []
        errors: List[str] = []

        # Check if response is an error
        if "error" in raw_response:
            error_msg = raw_response["error"].get("message", "Unknown error")
            errors.append(f"Azure OpenAI error: {error_msg}")

            response = NormalizedResponse(
                content="",
                model=model_name,
                provider=self.provider_name,
                usage=self._create_usage(0, 0, cost_per_1k),
                latency_ms=0.0,
                finish_reason=None,
                request_id=None,
                error=error_msg,
                raw_response=raw_response,
                quality_score=0.0,
                logprobs=None,
                cached=False,
            )

            return self.create_result(
                success=False,
                response=response,
                warnings=warnings,
                errors=errors,
                normalization_duration_ms=(time.time() - start_time) * 1000,
            )

        # Extract content
        content, content_warnings = self.extract_content(raw_response)
        warnings.extend(content_warnings)

        if not content and not errors:
            errors.append("No content in Azure OpenAI response")

        # Extract finish reason
        finish_reason = self.extract_finish_reason(raw_response)

        # Extract tool calls
        tool_calls, tool_warnings = self.extract_tool_calls(raw_response)
        warnings.extend(tool_warnings)

        # Extract logprobs
        logprobs, logprob_warnings = self.extract_logprobs(raw_response)
        warnings.extend(logprob_warnings)

        # Create normalized response
        try:
            response = NormalizedResponse(
                content=content,
                model=model_name,
                provider=self.provider_name,
                usage=self._create_usage(prompt_tokens, completion_tokens, cost_per_1k),
                latency_ms=0.0,
                timestamp=datetime.now(),
                finish_reason=finish_reason,
                quality_score=0.0,
                tool_calls=tool_calls,
                logprobs=logprobs,
                error=None,
                raw_response=raw_response,
                request_id=None,
                cached=False,
            )

            return self.create_result(
                success=True,
                response=response,
                warnings=warnings,
                errors=errors,
                normalization_duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            errors.append(f"Failed to create normalized response: {str(e)}")

            response = NormalizedResponse(
                content=content or "",
                model=model_name,
                provider=self.provider_name,
                usage=self._create_usage(prompt_tokens, completion_tokens, cost_per_1k),
                latency_ms=0.0,
                timestamp=datetime.now(),
                finish_reason=None,
                quality_score=0.0,
                tool_calls=[],
                logprobs=None,
                raw_response=raw_response,
                request_id=None,
                cached=False,
                error=str(e),
            )

            return self.create_result(
                success=False,
                response=response,
                warnings=warnings,
                errors=errors,
                normalization_duration_ms=(time.time() - start_time) * 1000,
            )

    def _create_usage(
        self, prompt_tokens: int, completion_tokens: int, cost_per_1k: float
    ) -> UsageStatistics:
        """Create usage statistics."""
        from .models import UsageStatistics

        prompt_cost = (prompt_tokens / 1000.0) * cost_per_1k
        completion_cost = (completion_tokens / 1000.0) * cost_per_1k
        return UsageStatistics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=prompt_cost + completion_cost,
        )
