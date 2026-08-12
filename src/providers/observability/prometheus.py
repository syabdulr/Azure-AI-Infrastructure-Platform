"""Prometheus format exporter for gateway metrics."""

from typing import Dict, List

from .collector import MetricsCollector
from .models import GatewayMetrics


class PrometheusExporter:
    """Exports metrics in Prometheus text exposition format."""

    def __init__(self, collector: MetricsCollector) -> None:
        """Initialize exporter with a metrics collector."""
        self._collector = collector

    def export(self) -> str:
        """
        Export all metrics in Prometheus text format.

        Returns:
            Prometheus-formatted text with HELP, TYPE, and metric lines
        """
        metrics = self._collector.get_metrics()
        lines: List[str] = []

        # Request counter
        lines.append("# HELP gateway_requests_total Total number of requests")
        lines.append("# TYPE gateway_requests_total counter")
        lines.append(f"gateway_requests_total {metrics.total_requests}")

        # Error counter
        lines.append("# HELP gateway_errors_total Total number of errors")
        lines.append("# TYPE gateway_errors_total counter")
        lines.append(f"gateway_errors_total {metrics.total_errors}")

        # Cost gauge
        lines.append("# HELP gateway_cost_total Total cost in USD")
        lines.append("# TYPE gateway_cost_total counter")
        lines.append(f"gateway_cost_total {metrics.total_cost}")

        # Token counter
        lines.append("# HELP gateway_tokens_total Total tokens consumed")
        lines.append("# TYPE gateway_tokens_total counter")
        lines.append(f"gateway_tokens_total {metrics.total_tokens}")

        # Latency
        lines.append("# HELP gateway_request_latency Average request latency in ms")
        lines.append("# TYPE gateway_request_latency gauge")
        lines.append(f"gateway_request_latency {metrics.avg_latency_ms}")

        # Cache metrics
        lines.append("# HELP gateway_cache_hits_total Total cache hits")
        lines.append("# TYPE gateway_cache_hits_total counter")
        lines.append(f"gateway_cache_hits_total {metrics.cache_hits}")

        lines.append("# HELP gateway_cache_misses_total Total cache misses")
        lines.append("# TYPE gateway_cache_misses_total counter")
        lines.append(f"gateway_cache_misses_total {metrics.cache_misses}")

        lines.append("# HELP gateway_cache_hit_rate Cache hit rate (0-1)")
        lines.append("# TYPE gateway_cache_hit_rate gauge")
        lines.append(f"gateway_cache_hit_rate {metrics.cache_hit_rate}")

        # Per-provider breakdown
        lines.append("# HELP gateway_provider_requests Requests per provider")
        lines.append("# TYPE gateway_provider_requests counter")
        for provider, data in metrics._provider_data.items():
            lines.append(f'gateway_provider_requests{{provider="{provider}"}} {data["requests"]}')

        # Per-provider cost
        lines.append("# HELP gateway_provider_cost Cost per provider in USD")
        lines.append("# TYPE gateway_provider_cost counter")
        for provider, data in metrics._provider_data.items():
            lines.append(f'gateway_provider_cost{{provider="{provider}"}} {data["cost"]}')

        # Per-provider latency
        lines.append("# HELP gateway_provider_latency Average latency per provider in ms")
        lines.append("# TYPE gateway_provider_latency gauge")
        for provider, data in metrics._provider_data.items():
            latencies = data.get("latencies", [])
            avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
            lines.append(f'gateway_provider_latency{{provider="{provider}"}} {avg_lat}')

        return "\n".join(lines) + "\n"
