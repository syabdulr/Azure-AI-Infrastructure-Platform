"""Metrics collector for observability."""

from datetime import datetime
from typing import Any, Dict, Optional

from .models import GatewayMetrics, HealthSnapshot


class MetricsCollector:
    """Collects and aggregates gateway metrics."""

    def __init__(self) -> None:
        """Initialize metrics collector."""
        self._metrics = GatewayMetrics()

    def record_request(
        self,
        provider: str,
        model: str,
        latency_ms: float,
        cost_usd: float,
        tokens: int,
        success: bool,
    ) -> None:
        """Record a request outcome."""
        self._metrics.record_request(
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            cost_usd=cost_usd,
            tokens=tokens,
            success=success,
        )

    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self._metrics.record_cache_hit()

    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self._metrics.record_cache_miss()

    def get_metrics(self) -> GatewayMetrics:
        """Get the raw metrics object."""
        return self._metrics

    def get_provider_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get per-provider metrics summary."""
        result: Dict[str, Dict[str, Any]] = {}
        for provider in self._metrics._provider_data:
            m = self._metrics.get_provider_metrics(provider)
            if m:
                result[provider] = m
        return result

    def get_health_snapshot(self, provider: str) -> Optional[HealthSnapshot]:
        """Get a health snapshot for a provider."""
        provider_metrics = self._metrics.get_provider_metrics(provider)
        if provider_metrics is None:
            return None

        requests = provider_metrics["requests"]
        errors = provider_metrics["errors"]
        success_rate = (requests - errors) / requests if requests > 0 else 0.0
        error_rate = errors / requests if requests > 0 else 0.0
        avg_latency = provider_metrics["avg_latency_ms"]
        healthy = error_rate < 0.1 and avg_latency < 5000.0

        return HealthSnapshot(
            provider_name=provider,
            healthy=healthy,
            latency_ms=avg_latency,
            success_rate=success_rate,
            error_rate=error_rate,
            last_check=datetime.now(),
        )

    def get_snapshot(self) -> Dict[str, Any]:
        """Get full metrics snapshot."""
        return self._metrics.snapshot()

    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics = GatewayMetrics()
