"""Tests for observability module."""

from unittest.mock import MagicMock

import pytest

from src.providers.observability.collector import MetricsCollector
from src.providers.observability.models import (
    GatewayMetrics,
    HealthSnapshot,
    MetricSample,
    MetricTag,
    MetricType,
)
from src.providers.observability.prometheus import PrometheusExporter


class TestMetricSample:
    """Test metric sample model."""

    def test_sample_creation(self):
        """Test creating a metric sample."""
        sample = MetricSample(
            name="request_count",
            value=1,
            metric_type=MetricType.COUNTER,
            tags={"provider": "azure_openai", "model": "gpt-4"},
        )
        assert sample.name == "request_count"
        assert sample.value == 1
        assert sample.metric_type == MetricType.COUNTER
        assert sample.tags["provider"] == "azure_openai"

    def test_sample_with_tags(self):
        """Test sample with multiple tags."""
        sample = MetricSample(
            name="request_latency",
            value=250.5,
            metric_type=MetricType.HISTOGRAM,
            tags={"provider": "openai", "model": "gpt-3.5-turbo", "status": "success"},
        )
        assert len(sample.tags) == 3


class TestGatewayMetrics:
    """Test gateway-level metrics aggregation."""

    def test_metrics_creation(self):
        """Test creating gateway metrics."""
        metrics = GatewayMetrics()
        assert metrics.total_requests == 0
        assert metrics.total_errors == 0
        assert metrics.total_cost == 0.0

    def test_record_request(self):
        """Test recording a request."""
        metrics = GatewayMetrics()
        metrics.record_request(
            provider="azure_openai",
            model="gpt-4",
            latency_ms=500.0,
            cost_usd=0.03,
            tokens=150,
            success=True,
        )
        assert metrics.total_requests == 1
        assert metrics.total_cost == 0.03
        assert metrics.total_tokens == 150

    def test_record_error(self):
        """Test recording an error request."""
        metrics = GatewayMetrics()
        metrics.record_request(
            provider="azure_openai",
            model="gpt-4",
            latency_ms=3000.0,
            cost_usd=0.0,
            tokens=0,
            success=False,
        )
        assert metrics.total_requests == 1
        assert metrics.total_errors == 1

    def test_error_rate(self):
        """Test error rate calculation."""
        metrics = GatewayMetrics()
        for i in range(10):
            metrics.record_request(
                provider="openai",
                model="gpt-4",
                latency_ms=500.0,
                cost_usd=0.02,
                tokens=100,
                success=True if i < 9 else False,
            )
        assert metrics.total_requests == 10
        assert metrics.total_errors == 1
        assert metrics.error_rate == pytest.approx(0.1)

    def test_avg_latency(self):
        """Test average latency."""
        metrics = GatewayMetrics()
        metrics.record_request("p1", "m1", 100.0, 0.01, 50, True)
        metrics.record_request("p1", "m1", 300.0, 0.01, 50, True)
        assert metrics.avg_latency_ms == pytest.approx(200.0)

    def test_per_provider_metrics(self):
        """Test per-provider breakdown."""
        metrics = GatewayMetrics()
        metrics.record_request("azure_openai", "gpt-4", 500.0, 0.03, 100, True)
        metrics.record_request("openai", "gpt-4", 400.0, 0.02, 100, True)
        metrics.record_request("azure_openai", "gpt-4", 600.0, 0.03, 100, True)

        provider_metrics = metrics.get_provider_metrics("azure_openai")
        assert provider_metrics["requests"] == 2
        assert provider_metrics["cost"] == 0.06

    def test_per_model_metrics(self):
        """Test per-model breakdown."""
        metrics = GatewayMetrics()
        metrics.record_request("azure_openai", "gpt-4", 500.0, 0.03, 100, True)
        metrics.record_request("azure_openai", "gpt-3.5-turbo", 200.0, 0.001, 100, True)
        metrics.record_request("azure_openai", "gpt-4", 700.0, 0.03, 100, True)

        model_metrics = metrics.get_model_metrics("azure_openai", "gpt-4")
        assert model_metrics["requests"] == 2
        assert model_metrics["cost"] == 0.06

    def test_cache_metrics(self):
        """Test cache hit/miss tracking."""
        metrics = GatewayMetrics()
        metrics.record_cache_hit()
        metrics.record_cache_hit()
        metrics.record_cache_miss()
        assert metrics.cache_hits == 2
        assert metrics.cache_misses == 1
        assert metrics.cache_hit_rate == pytest.approx(2 / 3)

    def test_snapshot(self):
        """Test taking a metrics snapshot."""
        metrics = GatewayMetrics()
        metrics.record_request("azure_openai", "gpt-4", 500.0, 0.03, 100, True)
        metrics.record_cache_hit()

        snap = metrics.snapshot()
        assert snap["total_requests"] == 1
        assert snap["total_cost"] == 0.03
        assert snap["cache_hits"] == 1
        assert snap["error_rate"] == 0.0


class TestHealthSnapshot:
    """Test health snapshot model."""

    def test_health_creation(self):
        """Test creating a health snapshot."""
        health = HealthSnapshot(
            provider_name="azure_openai",
            healthy=True,
            latency_ms=250.0,
            success_rate=0.99,
            error_rate=0.01,
        )
        assert health.provider_name == "azure_openai"
        assert health.healthy is True
        assert health.success_rate == 0.99


class TestMetricsCollector:
    """Test the metrics collector."""

    def test_collector_creation(self):
        """Test creating a collector."""
        collector = MetricsCollector()
        assert collector is not None

    def test_collector_record_request(self):
        """Test recording a request."""
        collector = MetricsCollector()
        collector.record_request(
            provider="azure_openai",
            model="gpt-4",
            latency_ms=500.0,
            cost_usd=0.03,
            tokens=150,
            success=True,
        )
        metrics = collector.get_metrics()
        assert metrics.total_requests == 1

    def test_collector_record_multiple(self):
        """Test recording multiple requests."""
        collector = MetricsCollector()
        for i in range(5):
            collector.record_request(
                provider="openai",
                model="gpt-4",
                latency_ms=400.0 + i * 10,
                cost_usd=0.02,
                tokens=100,
                success=True,
            )
        metrics = collector.get_metrics()
        assert metrics.total_requests == 5

    def test_collector_cache_tracking(self):
        """Test cache tracking through collector."""
        collector = MetricsCollector()
        collector.record_cache_hit()
        collector.record_cache_miss()
        metrics = collector.get_metrics()
        assert metrics.cache_hits == 1
        assert metrics.cache_misses == 1

    def test_collector_provider_breakdown(self):
        """Test provider-level breakdown."""
        collector = MetricsCollector()
        collector.record_request("azure_openai", "gpt-4", 500.0, 0.03, 100, True)
        collector.record_request("openai", "gpt-4", 400.0, 0.02, 100, True)
        collector.record_request("azure_openai", "gpt-4", 600.0, 0.03, 100, True)

        summary = collector.get_provider_summary()
        assert "azure_openai" in summary
        assert summary["azure_openai"]["requests"] == 2
        assert "openai" in summary
        assert summary["openai"]["requests"] == 1

    def test_collector_health_snapshot(self):
        """Test getting health snapshot."""
        collector = MetricsCollector()
        collector.record_request("azure_openai", "gpt-4", 500.0, 0.03, 100, True)
        collector.record_request("azure_openai", "gpt-4", 600.0, 0.03, 100, True)
        collector.record_request("azure_openai", "gpt-4", 3000.0, 0.0, 0, False)

        health = collector.get_health_snapshot("azure_openai")
        assert health is not None
        assert health.provider_name == "azure_openai"
        assert health.success_rate == pytest.approx(2 / 3)
        assert health.error_rate == pytest.approx(1 / 3)

    def test_collector_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()
        collector.record_request("openai", "gpt-4", 500.0, 0.03, 100, True)
        assert collector.get_metrics().total_requests == 1

        collector.reset()
        assert collector.get_metrics().total_requests == 0

    def test_collector_snapshot(self):
        """Test getting full snapshot."""
        collector = MetricsCollector()
        collector.record_request("openai", "gpt-4", 500.0, 0.03, 100, True)
        collector.record_cache_hit()

        snapshot = collector.get_snapshot()
        assert snapshot["total_requests"] == 1
        assert snapshot["cache_hits"] == 1


class TestPrometheusExporter:
    """Test Prometheus format exporter."""

    def test_exporter_creation(self):
        """Test creating exporter."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        assert exporter is not None

    def test_export_empty(self):
        """Test exporting with no metrics."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        output = exporter.export()
        assert isinstance(output, str)
        assert "gateway_requests_total" in output

    def test_export_with_data(self):
        """Test exporting with metrics data."""
        collector = MetricsCollector()
        collector.record_request(
            provider="azure_openai",
            model="gpt-4",
            latency_ms=500.0,
            cost_usd=0.03,
            tokens=100,
            success=True,
        )
        collector.record_request(
            provider="azure_openai",
            model="gpt-4",
            latency_ms=3000.0,
            cost_usd=0.0,
            tokens=0,
            success=False,
        )
        collector.record_cache_hit()

        exporter = PrometheusExporter(collector)
        output = exporter.export()

        assert "gateway_requests_total" in output
        assert "gateway_errors_total" in output
        assert "gateway_cache_hits_total" in output
        assert "gateway_cost_total" in output
        assert "azure_openai" in output

    def test_export_help_text(self):
        """Test that HELP and TYPE lines are present."""
        collector = MetricsCollector()
        exporter = PrometheusExporter(collector)
        output = exporter.export()

        assert "# HELP" in output
        assert "# TYPE" in output

    def test_export_latency_histogram(self):
        """Test that latency metrics are exported."""
        collector = MetricsCollector()
        collector.record_request(
            provider="azure_openai",
            model="gpt-4",
            latency_ms=500.0,
            cost_usd=0.03,
            tokens=100,
            success=True,
        )

        exporter = PrometheusExporter(collector)
        output = exporter.export()

        assert "gateway_request_latency" in output
