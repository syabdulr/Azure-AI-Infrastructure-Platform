"""Unit tests for metrics collector"""

import pytest
from src.monitoring.metrics_collector import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricsCollector
)


# ============================================================================
# Counter Tests
# ============================================================================

@pytest.mark.unit
class TestCounter:
    """Test Counter metric"""
    
    def test_counter_init(self):
        """Test counter initialization"""
        counter = Counter("test_counter", "Test counter")
        assert counter.name == "test_counter"
        assert counter.help_text == "Test counter"
        assert counter.value == 0.0
        assert len(counter.label_values) == 0
    
    def test_counter_increment(self):
        """Test counter increment"""
        counter = Counter("test_counter")
        counter.inc()
        assert counter.value == 1.0
    
    def test_counter_increment_by_value(self):
        """Test counter increment by specific value"""
        counter = Counter("test_counter")
        counter.inc(5.0)
        assert counter.value == 5.0
    
    def test_counter_increment_with_labels(self):
        """Test counter increment with labels"""
        counter = Counter("test_counter")
        counter.inc(1.0, {"endpoint": "/chat", "method": "POST"})
        
        label_key = counter._labels_to_key({"endpoint": "/chat", "method": "POST"})
        assert counter.label_values[label_key] == 1.0
    
    def test_counter_get(self):
        """Test counter get"""
        counter = Counter("test_counter")
        counter.inc(3.0)
        assert counter.get() == 3.0
    
    def test_counter_get_with_labels(self):
        """Test counter get with labels"""
        counter = Counter("test_counter")
        counter.inc(2.0, {"endpoint": "/chat"})
        
        value = counter.get({"endpoint": "/chat"})
        assert value == 2.0
    
    def test_counter_reset(self):
        """Test counter reset"""
        counter = Counter("test_counter")
        counter.inc(5.0)
        counter.reset()
        assert counter.value == 0.0
    
    def test_counter_reset_with_labels(self):
        """Test counter reset with labels"""
        counter = Counter("test_counter")
        counter.inc(3.0, {"endpoint": "/chat"})
        counter.reset({"endpoint": "/chat"})
        
        label_key = counter._labels_to_key({"endpoint": "/chat"})
        assert counter.label_values[label_key] == 0.0


# ============================================================================
# Gauge Tests
# ============================================================================

@pytest.mark.unit
class TestGauge:
    """Test Gauge metric"""
    
    def test_gauge_init(self):
        """Test gauge initialization"""
        gauge = Gauge("test_gauge", "Test gauge")
        assert gauge.name == "test_gauge"
        assert gauge.help_text == "Test gauge"
        assert gauge.value == 0.0
    
    def test_gauge_set(self):
        """Test gauge set"""
        gauge = Gauge("test_gauge")
        gauge.set(42.0)
        assert gauge.value == 42.0
    
    def test_gauge_set_with_labels(self):
        """Test gauge set with labels"""
        gauge = Gauge("test_gauge")
        gauge.set(50.0, {"endpoint": "/chat"})
        
        label_key = gauge._labels_to_key({"endpoint": "/chat"})
        assert gauge.label_values[label_key] == 50.0
    
    def test_gauge_inc(self):
        """Test gauge increment"""
        gauge = Gauge("test_gauge")
        gauge.set(10.0)
        gauge.inc(5.0)
        assert gauge.value == 15.0
    
    def test_gauge_dec(self):
        """Test gauge decrement"""
        gauge = Gauge("test_gauge")
        gauge.set(10.0)
        gauge.dec(3.0)
        assert gauge.value == 7.0
    
    def test_gauge_get(self):
        """Test gauge get"""
        gauge = Gauge("test_gauge")
        gauge.set(25.0)
        assert gauge.get() == 25.0


# ============================================================================
# Histogram Tests
# ============================================================================

@pytest.mark.unit
class TestHistogram:
    """Test Histogram metric"""
    
    def test_histogram_init(self):
        """Test histogram initialization"""
        histogram = Histogram("test_histogram", [5, 10, 50], "Test histogram")
        assert histogram.name == "test_histogram"
        assert histogram.buckets == [5, 10, 50]
        assert histogram.count == 0
        assert histogram.sum == 0.0
    
    def test_histogram_observe(self):
        """Test histogram observe"""
        histogram = Histogram("test_histogram", [5, 10, 50])
        histogram.observe(7.5)
        assert histogram.count == 1
        assert histogram.sum == 7.5
    
    def test_histogram_bucket_counts(self):
        """Test histogram bucket counts"""
        histogram = Histogram("test_histogram", [5, 10, 50])
        
        histogram.observe(3.0)
        histogram.observe(7.0)
        histogram.observe(15.0)
        
        assert histogram.bucket_counts[5] == 1  # 3.0 <= 5
        assert histogram.bucket_counts[10] == 2  # 3.0, 7.0 <= 10
        assert histogram.bucket_counts[50] == 3  # All <= 50
    
    def test_histogram_observe_with_labels(self):
        """Test histogram observe with labels"""
        histogram = Histogram("test_histogram", [5, 10, 50])
        histogram.observe(8.0, {"endpoint": "/chat"})
        
        data = histogram.get({"endpoint": "/chat"})
        assert data["count"] == 1
        assert data["sum"] == 8.0
    
    def test_histogram_get(self):
        """Test histogram get"""
        histogram = Histogram("test_histogram", [5, 10, 50])
        histogram.observe(10.0)
        
        data = histogram.get()
        assert data["count"] == 1
        assert data["sum"] == 10.0
        assert 10 in data["buckets"]


# ============================================================================
# Summary Tests
# ============================================================================

@pytest.mark.unit
class TestSummary:
    """Test Summary metric"""
    
    def test_summary_init(self):
        """Test summary initialization"""
        summary = Summary("test_summary", [0.5, 0.9], "Test summary")
        assert summary.name == "test_summary"
        assert summary.quantiles == [0.5, 0.9]
        assert summary.count == 0
        assert len(summary.values) == 0
    
    def test_summary_observe(self):
        """Test summary observe"""
        summary = Summary("test_summary", [0.5, 0.9])
        summary.observe(10.0)
        summary.observe(20.0)
        
        assert summary.count == 2
        assert summary.sum == 30.0
        assert len(summary.values) == 2
    
    def test_summary_quantiles(self):
        """Test summary quantiles"""
        summary = Summary("test_summary", [0.5, 0.9])
        
        # Add values
        for i in range(100):
            summary.observe(i)
        
        data = summary.get()
        assert "quantiles" in data
        assert "0.5" in data["quantiles"]
        assert "0.9" in data["quantiles"]
    
    def test_summary_get_with_labels(self):
        """Test summary get with labels"""
        summary = Summary("test_summary", [0.5])
        summary.observe(15.0, {"endpoint": "/chat"})
        
        data = summary.get({"endpoint": "/chat"})
        assert data["count"] == 1
        assert data["sum"] == 15.0


# ============================================================================
# MetricsCollector Tests
# ============================================================================

@pytest.mark.unit
class TestMetricsCollector:
    """Test MetricsCollector"""
    
    def test_metrics_collector_init(self):
        """Test metrics collector initialization"""
        collector = MetricsCollector()
        assert len(collector.counters) > 0
        assert len(collector.gauges) > 0
        assert len(collector.histograms) > 0
        assert len(collector.summaries) > 0
    
    def test_metrics_collector_default_metrics(self):
        """Test default metrics are created"""
        collector = MetricsCollector()
        
        # Check API metrics
        assert "api_requests_total" in collector.counters
        assert "api_request_duration_ms" in collector.histograms
        assert "active_connections" in collector.gauges
        
        # Check AI metrics
        assert "ai_requests_total" in collector.counters
        assert "ai_cost_total" in collector.gauges
        
        # Check RAG metrics
        assert "rag_queries_total" in collector.counters
        assert "rag_retrieval_time_ms" in collector.histograms
        
        # Check Guardrails metrics
        assert "guardrails_input_checks_total" in collector.counters
    
    def test_metrics_collector_create_counter(self):
        """Test creating counter"""
        collector = MetricsCollector()
        counter = collector.create_counter("custom_counter", "Custom counter")
        
        assert counter.name == "custom_counter"
        assert "custom_counter" in collector.counters
    
    def test_metrics_collector_create_gauge(self):
        """Test creating gauge"""
        collector = MetricsCollector()
        gauge = collector.create_gauge("custom_gauge", "Custom gauge")
        
        assert gauge.name == "custom_gauge"
        assert "custom_gauge" in collector.gauges
    
    def test_metrics_collector_create_histogram(self):
        """Test creating histogram"""
        collector = MetricsCollector()
        histogram = collector.create_histogram(
            "custom_histogram",
            [1, 5, 10],
            "Custom histogram"
        )
        
        assert histogram.name == "custom_histogram"
        assert "custom_histogram" in collector.histograms
    
    def test_metrics_collector_create_summary(self):
        """Test creating summary"""
        collector = MetricsCollector()
        summary = collector.create_summary(
            "custom_summary",
            [0.5, 0.9],
            "Custom summary"
        )
        
        assert summary.name == "custom_summary"
        assert "custom_summary" in collector.summaries
    
    def test_metrics_collector_get_metrics(self):
        """Test getting all metrics"""
        collector = MetricsCollector()
        metrics = collector.get_metrics()
        
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
        assert "summaries" in metrics
    
    def test_metrics_collector_export_prometheus(self):
        """Test Prometheus export"""
        collector = MetricsCollector()
        prometheus_format = collector.export_prometheus()
        
        assert "# TYPE" in prometheus_format
        assert "api_requests_total" in prometheus_format
        assert "active_connections" in prometheus_format