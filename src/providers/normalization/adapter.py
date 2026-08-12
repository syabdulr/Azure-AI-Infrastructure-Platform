"""Response normalizer base adapter."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import (
    LogProb,
    NormalizationError,
    NormalizationResult,
    NormalizedResponse,
    ToolCall,
    UsageStatistics,
)


class ResponseAdapter(ABC):
    """Base adapter for normalizing provider responses."""

    def __init__(self, provider_name: str):
        """Initialize adapter with provider name."""
        self.provider_name = provider_name
        self.supports_tool_calls = False
        self.supports_logprobs = False
        self.supports_streaming = False

    @abstractmethod
    def normalize(
        self,
        raw_response: Dict[str, Any],
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_per_1k: float,
    ) -> NormalizationResult:
        """
        Normalize a provider's raw response into a unified format.

        Args:
            raw_response: The raw response from the provider API
            model_name: Name of the model that generated the response
            prompt_tokens: Tokens in the prompt
            completion_tokens: Tokens in the completion
            cost_per_1k: Cost per 1k tokens

        Returns:
            NormalizationResult with normalized response or errors
        """
        pass

    def calculate_cost(
        self, prompt_tokens: int, completion_tokens: int, cost_per_1k: float
    ) -> tuple[float, float, float]:
        """
        Calculate cost breakdown.

        Args:
            prompt_tokens: Tokens in the prompt
            completion_tokens: Tokens in the completion
            cost_per_1k: Cost per 1k tokens

        Returns:
            Tuple of (prompt_cost, completion_cost, total_cost)
        """
        prompt_cost = (prompt_tokens / 1000.0) * cost_per_1k
        completion_cost = (completion_tokens / 1000.0) * cost_per_1k
        total_cost = prompt_cost + completion_cost
        return prompt_cost, completion_cost, total_cost

    def extract_content(self, raw_response: Dict[str, Any]) -> tuple[str, List[str]]:
        """
        Extract content from raw response.

        Args:
            raw_response: Raw provider response

        Returns:
            Tuple of (content, warnings)
        """
        warnings: List[str] = []

        # Default: try to find 'choices[0].message.content'
        try:
            content = raw_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            if not content:
                warnings.append(
                    f"{NormalizationError.EMPTY_RESPONSE.value}: No content in response"
                )
                return "", warnings
            return content, warnings
        except (KeyError, IndexError, AttributeError) as e:
            warnings.append(f"{NormalizationError.MISSING_REQUIRED_FIELD.value}: {str(e)}")
            return "", warnings

    def extract_finish_reason(self, raw_response: Dict[str, Any]) -> Optional[str]:
        """
        Extract finish reason from raw response.

        Args:
            raw_response: Raw provider response

        Returns:
            Finish reason or None
        """
        try:
            finish_reason = raw_response.get("choices", [{}])[0].get("finish_reason")
            return str(finish_reason) if finish_reason is not None else None
        except (KeyError, IndexError):
            return None

    def extract_tool_calls(self, raw_response: Dict[str, Any]) -> tuple[List[ToolCall], List[str]]:
        """
        Extract tool calls from raw response.

        Args:
            raw_response: Raw provider response

        Returns:
            Tuple of (tool_calls, warnings)
        """
        warnings: List[str] = []

        if not self.supports_tool_calls:
            return [], warnings

        try:
            raw_tool_calls = (
                raw_response.get("choices", [{}])[0].get("message", {}).get("tool_calls", [])
            )

            tool_calls = []
            for i, raw_call in enumerate(raw_tool_calls):
                try:
                    call_id = raw_call.get("id", f"call_{i}")
                    name = raw_call.get("function", {}).get("name", "")
                    arguments = raw_call.get("function", {}).get("arguments", "{}")

                    if not name:
                        warnings.append(f"Tool call {i} missing function name")
                        continue

                    tool_calls.append(
                        ToolCall(
                            id=call_id,
                            name=name,
                            arguments=arguments,
                            type=raw_call.get("type", "function"),
                        )
                    )
                except Exception as e:
                    warnings.append(f"Failed to parse tool call {i}: {str(e)}")

            return tool_calls, warnings
        except (KeyError, IndexError) as e:
            warnings.append(f"{NormalizationError.TOOL_CALL_FORMAT_ERROR.value}: {str(e)}")
            return [], warnings

    def extract_logprobs(
        self, raw_response: Dict[str, Any]
    ) -> tuple[Optional[List[LogProb]], List[str]]:
        """
        Extract log probabilities from raw response.

        Args:
            raw_response: Raw provider response

        Returns:
            Tuple of (logprobs, warnings)
        """
        warnings: List[str] = []

        if not self.supports_logprobs:
            return None, warnings

        try:
            raw_logprobs = (
                raw_response.get("choices", [{}])[0].get("logprobs", {}).get("content", [])
            )

            if not raw_logprobs:
                return None, warnings

            logprobs = []
            for lp in raw_logprobs:
                try:
                    token = lp.get("token", "")
                    logprob = lp.get("logprob", 0.0)

                    # Extract top logprobs if available
                    top_logprobs = []
                    if "top_logprobs" in lp:
                        top_logprobs = [
                            {tlp.get("token", ""): tlp.get("logprob", 0.0)}
                            for tlp in lp.get("top_logprobs", [])
                        ]

                    logprobs.append(
                        LogProb(token=token, logprob=logprob, top_logprobs=top_logprobs)
                    )
                except Exception as e:
                    warnings.append(f"Failed to parse logprob: {str(e)}")

            return logprobs, warnings
        except (KeyError, IndexError) as e:
            warnings.append(f"Failed to extract logprobs: {str(e)}")
            return None, warnings

    def create_normalized_response(
        self,
        content: str,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
        cost_per_1k: float,
        latency_ms: float,
        finish_reason: Optional[str] = None,
        tool_calls: Optional[List[ToolCall]] = None,
        logprobs: Optional[List[LogProb]] = None,
        raw_response: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None,
        cached: bool = False,
    ) -> NormalizedResponse:
        """
        Create a normalized response.

        Args:
            content: Generated content
            model_name: Model name
            prompt_tokens: Tokens in prompt
            completion_tokens: Tokens in completion
            cost_per_1k: Cost per 1k tokens
            latency_ms: Request latency
            finish_reason: Finish reason
            tool_calls: Tool calls
            logprobs: Log probabilities
            raw_response: Raw provider response
            request_id: Request ID
            cached: Whether cached

        Returns:
            NormalizedResponse
        """
        prompt_cost, completion_cost, total_cost = self.calculate_cost(
            prompt_tokens, completion_tokens, cost_per_1k
        )

        usage = UsageStatistics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            prompt_cost=prompt_cost,
            completion_cost=completion_cost,
            total_cost=total_cost,
        )

        return NormalizedResponse(
            content=content,
            model=model_name,
            provider=self.provider_name,
            usage=usage,
            latency_ms=latency_ms,
            timestamp=datetime.now(),
            finish_reason=finish_reason,
            quality_score=0.0,
            tool_calls=tool_calls or [],
            logprobs=logprobs,
            error=None,
            raw_response=raw_response or {},
            request_id=request_id,
            cached=cached,
        )

    def create_result(
        self,
        success: bool,
        response: Optional[NormalizedResponse],
        warnings: List[str],
        errors: List[str],
        normalization_duration_ms: float,
    ) -> NormalizationResult:
        """
        Create a normalization result.

        Args:
            success: Whether normalization succeeded
            response: Normalized response (if successful)
            warnings: Warnings
            errors: Errors
            normalization_duration_ms: Duration of normalization

        Returns:
            NormalizationResult
        """
        return NormalizationResult(
            success=success,
            response=response,
            warnings=warnings,
            errors=errors,
            original_provider=self.provider_name,
            normalization_duration_ms=normalization_duration_ms,
        )
