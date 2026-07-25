"""Additional unit tests for metrics collector"""

import pytest
from src.monitoring.metrics_collector import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    MetricsCollector
)


@pytest.mark.unit
class TestMetricsCollectorExtended:
    """Extended tests for metrics collector to increase coverage"""
    
    def test_metrics_collector_create_counter_custom(self):
        """Test creating custom counter"""
        collector = MetricsCollector()
        
        counter = collector.create_counter("custom_counter", "Custom counter description")
        
        assert counter is not None
        assert counter.name == "custom_counter"
        assert "custom_counter" in collector.counters
    
    def test_metrics_collector_create_gauge_custom(self):
        """Test creating custom gauge"""
        collector = MetricsCollector()
        
        gauge = collector.create_gauge("custom_gauge", "Custom gauge description")
        
        assert gauge is not None
        assert gauge.name == "custom_gauge"
        assert "custom_gauge" in collector.gauges
    
    def test_metrics_collector_create_histogram_custom(self):
        """Test creating custom histogram"""
        collector = MetricsCollector()
        
        histogram = collector.create_histogram(
            "custom_histogram",
            [1, 5, 10, 50],
            "Custom histogram description"
        )
        
        assert histogram is not None
        assert histogram.name == "custom_histogram"
        assert "custom_histogram" in collector.histograms
    
    def test_metrics_collector_create_summary_custom(self):
        """Test creating custom summary"""
        collector = MetricsCollector()
        
        summary = collector.create_summary(
            "custom_summary",
            [0.5, 0.9],
            "Custom summary description"
        )
        
        assert summary is not None
        assert summary.name == "custom_summary"
        assert "custom_summary" in collector.summaries
    
    def test_metrics_collector_get_metrics_all_types(self):
        """Test getting all metrics types"""
        collector = MetricsCollector()
        
        metrics = collector.get_metrics()
        
        # Verify all metric types are present
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "histograms" in metrics
        assert "summaries" in metrics
        
        # Verify metrics are dictionaries
        assert isinstance(metrics["counters"], dict)
        assert isinstance(metrics["gauges"], dict)
        assert isinstance(metrics["histograms"], dict)
        assert isinstance(metrics["summaries"], dict)
        
        # Verify default metrics exist
        assert "api_requests_total" in metrics["counters"]
        assert "ai_requests_total" in metrics["counters"]
        assert "active_connections" in metrics["gauges"]
        assert "api_request_duration_ms" in metrics["histograms"]
        assert "api_response_time_ms" in metrics["summaries"]
    
    def test_metrics_collector_export_prometheus_format(self):
        """Test Prometheus export format"""
        collector = MetricsCollector()
        
        # Generate some metrics
        counter = collector.counters["api_requests_total"]
        counter.inc(10)
        
        gauge = collector.gauges["active_connections"]
        gauge.set(5)
        
        # Export to Prometheus
        prometheus = collector.export_prometheus()
        
        # Verify format
        assert isinstance(prometheus, str)
        assert len(prometheus) > 0
        
        # Verify content
        assert "# TYPE" in prometheus
        assert "api_requests_total" in prometheus
        assert "active_connections" in prometheus
        assert "api_request_duration_ms" in prometheus
        assert "api_response_time_ms" in prometheus
    
    def test_metrics_collector_initialize_all_default_metrics(self):
        """Test that all default metrics are initialized"""
        collector = MetricsCollector()
        
        # API metrics
        assert "api_requests_total" in collector.counters
        assert "api_request_duration_ms" in collector.histograms
        assert "api_response_time_ms" in collector.summaries
        assert "active_connections" in collector.gauges
        
        # AI metrics
        assert "ai_requests_total" in collector.counters
        assert "ai_tokens_total" in collector.counters
        assert "ai_cost_total" in collector.gauges
        assert "ai_latency_ms" in collector.histograms
        
        # RAG metrics
        assert "rag_queries_total" in collector.counters
        assert "rag_retrieval_time_ms" in collector.histograms
        assert "rag_generation_time_ms" in collector.histograms
        assert "rag_documents_retrieved" in collector.summaries
        
        # Guardrails metrics
        assert "guardrails_input_checks_total" in collector.counters
        assert "guardrails_output_checks_total" in collector.counters
        assert "guardrails_violations_total" in collector.counters
        
        # System metrics
        assert "system_cpu_usage_percent" in collector.gauges
        assert "system_memory_usage_percent" in collector.gauges
        assert "system_disk_usage_percent" in collector.gauges
    
    def test_metrics_collector_operate_on_all_default_counters(self):
        """Test operating on all default counters"""
        collector = MetricsCollector()
        
        # Increment all counters
        for name, counter in collector.counters.items():
            counter.inc(5)
        
        # Verify all incremented
        for name, counter in collector.counters.items():
            value = counter.get()
            assert value >= 5
    
    def test_metrics_collector_operate_on_all_default_gauges(self):
        """Test operating on all default gauges"""
        collector = MetricsCollector()
        
        # Set all gauges
        for name, gauge in collector.gauges.items():
            gauge.set(42.0)
        
        # Verify all set
        for name, gauge in collector.gauges.items():
            value = gauge.get()
            assert value == 42.0
    
    def test_metrics_collector_labels_to_key_empty(self):
        """Test labels to key with empty labels"""
        collector = MetricsCollector()
        counter = collector.counters["api_requests_total"]
        
        key = counter._labels_to_key({})
        assert key == ""
    
    def test_metrics_collector_labels_to_key_sorted(self):
        """Test labels to key with sorted labels"""
        collector = MetricsCollector()
        counter = collector.counters["api_requests_total"]
        
        key1 = counter._labels_to_key({"method": "POST", "endpoint": "/chat"})
        key2 = counter._labels_to_key({"endpoint": "/chat", "method": "POST"})
        
        # Keys should be the same regardless of order
        assert key1 == key2