"""
Metrics collector for Azure AI Infrastructure Platform

This module provides:
- Custom metrics collection
- Counter metrics
- Gauge metrics
- Histogram metrics
- Summary metrics
- Metric labels and tags
- Prometheus export
"""

import logging
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class Counter:
    """Counter metric - only increases"""

    def __init__(self, name: str, help_text: str = ""):
        """
        Initialize counter

        Args:
            name: Metric name
            help_text: Help text
        """
        self.name = name
        self.help_text = help_text
        self.value = 0.0
        self.label_values = defaultdict(lambda: 0.0)

    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Increment counter

        Args:
            value: Value to increment by
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            self.label_values[label_key] += value
        else:
            self.value += value

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Get counter value

        Args:
            labels: Metric labels

        Returns:
            Counter value
        """
        if labels:
            label_key = self._labels_to_key(labels)
            return self.label_values[label_key]
        return self.value

    def reset(self, labels: Optional[Dict[str, str]] = None):
        """
        Reset counter

        Args:
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            self.label_values[label_key] = 0.0
        else:
            self.value = 0.0
            self.label_values.clear()

    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """
        Convert labels to string key

        Args:
            labels: Metric labels

        Returns:
            String key
        """
        sorted_labels = sorted(labels.items())
        return ",".join([f'{k}="{v}"' for k, v in sorted_labels])


class Gauge:
    """Gauge metric - can go up or down"""

    def __init__(self, name: str, help_text: str = ""):
        """
        Initialize gauge

        Args:
            name: Metric name
            help_text: Help text
        """
        self.name = name
        self.help_text = help_text
        self.value = 0.0
        self.label_values = defaultdict(lambda: 0.0)

    def set(self, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Set gauge value

        Args:
            value: Value to set
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            self.label_values[label_key] = value
        else:
            self.value = value

    def inc(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Increment gauge

        Args:
            value: Value to increment by
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            self.label_values[label_key] += value
        else:
            self.value += value

    def dec(self, value: float = 1.0, labels: Optional[Dict[str, str]] = None):
        """
        Decrement gauge

        Args:
            value: Value to decrement by
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            self.label_values[label_key] -= value
        else:
            self.value -= value

    def get(self, labels: Optional[Dict[str, str]] = None) -> float:
        """
        Get gauge value

        Args:
            labels: Metric labels

        Returns:
            Gauge value
        """
        if labels:
            label_key = self._labels_to_key(labels)
            return self.label_values[label_key]
        return self.value

    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """
        Convert labels to string key

        Args:
            labels: Metric labels

        Returns:
            String key
        """
        sorted_labels = sorted(labels.items())
        return ",".join([f'{k}="{v}"' for k, v in sorted_labels])


class Histogram:
    """Histogram metric - tracks distribution of values"""

    def __init__(self, name: str, buckets: Optional[List[float]] = None, help_text: str = ""):
        """
        Initialize histogram

        Args:
            name: Metric name
            buckets: Bucket boundaries
            help_text: Help text
        """
        self.name = name
        self.help_text = help_text
        self.buckets = buckets or [5, 10, 50, 100, 500, 1000]
        self.buckets.sort()

        self.count = 0
        self.sum = 0.0
        self.bucket_counts = defaultdict(int)
        self.label_data = defaultdict(
            lambda: {"count": 0, "sum": 0.0, "bucket_counts": defaultdict(int)}
        )

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe a value

        Args:
            value: Value to observe
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            data = self.label_data[label_key]
            data["count"] += 1
            data["sum"] += value

            for bucket in self.buckets:
                if value <= bucket:
                    data["bucket_counts"][bucket] += 1
        else:
            self.count += 1
            self.sum += value

            for bucket in self.buckets:
                if value <= bucket:
                    self.bucket_counts[bucket] += 1

    def get(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get histogram data

        Args:
            labels: Metric labels

        Returns:
            Histogram data
        """
        if labels:
            label_key = self._labels_to_key(labels)
            data = self.label_data[label_key]
            return {
                "count": data["count"],
                "sum": data["sum"],
                "buckets": dict(data["bucket_counts"]),
            }

        return {"count": self.count, "sum": self.sum, "buckets": dict(self.bucket_counts)}

    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """
        Convert labels to string key

        Args:
            labels: Metric labels

        Returns:
            String key
        """
        sorted_labels = sorted(labels.items())
        return ",".join([f'{k}="{v}"' for k, v in sorted_labels])


class Summary:
    """Summary metric - tracks quantiles"""

    def __init__(self, name: str, quantiles: Optional[List[float]] = None, help_text: str = ""):
        """
        Initialize summary

        Args:
            name: Metric name
            quantiles: Quantiles to track
            help_text: Help text
        """
        self.name = name
        self.help_text = help_text
        self.quantiles = quantiles or [0.5, 0.9, 0.95, 0.99]
        self.quantiles.sort()

        self.count = 0
        self.sum = 0.0
        self.values = []
        self.label_data = defaultdict(lambda: {"count": 0, "sum": 0.0, "values": []})

    def observe(self, value: float, labels: Optional[Dict[str, str]] = None):
        """
        Observe a value

        Args:
            value: Value to observe
            labels: Metric labels
        """
        if labels:
            label_key = self._labels_to_key(labels)
            data = self.label_data[label_key]
            data["count"] += 1
            data["sum"] += value
            data["values"].append(value)
        else:
            self.count += 1
            self.sum += value
            self.values.append(value)

    def get(self, labels: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Get summary data

        Args:
            labels: Metric labels

        Returns:
            Summary data with quantiles
        """
        if labels:
            label_key = self._labels_to_key(labels)
            data = self.label_data[label_key]
            return self._calculate_quantiles(data["values"])

        return self._calculate_quantiles(self.values)

    def _calculate_quantiles(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate quantiles from values

        Args:
            values: List of values

        Returns:
            Dictionary with quantiles
        """
        if not values:
            return {"count": 0, "sum": 0.0, "quantiles": {str(q): 0.0 for q in self.quantiles}}

        sorted_values = sorted(values)
        count = len(sorted_values)
        sum_val = sum(sorted_values)

        quantiles = {}
        for q in self.quantiles:
            index = int(q * count)
            if index >= count:
                index = count - 1
            quantiles[str(q)] = sorted_values[index]

        return {"count": count, "sum": sum_val, "quantiles": quantiles}

    def _labels_to_key(self, labels: Dict[str, str]) -> str:
        """
        Convert labels to string key

        Args:
            labels: Metric labels

        Returns:
            String key
        """
        sorted_labels = sorted(labels.items())
        return ",".join([f'{k}="{v}"' for k, v in sorted_labels])


class MetricsCollector:
    """Collect and manage application metrics"""

    def __init__(self):
        """Initialize metrics collector"""
        self.counters = {}
        self.gauges = {}
        self.histograms = {}
        self.summaries = {}

        # Initialize default metrics
        self._initialize_default_metrics()

    def _initialize_default_metrics(self):
        """Initialize default metrics"""
        # API metrics
        self.create_counter("api_requests_total", "Total API requests")
        self.create_histogram(
            "api_request_duration_ms", [5, 10, 50, 100, 500, 1000], "API request duration"
        )
        self.create_summary("api_response_time_ms", [0.5, 0.9, 0.95, 0.99], "API response time")
        self.create_gauge("active_connections", "Active connections")

        # AI metrics
        self.create_counter("ai_requests_total", "Total AI requests")
        self.create_counter("ai_tokens_total", "Total AI tokens")
        self.create_gauge("ai_cost_total", "Total AI cost")
        self.create_histogram("ai_latency_ms", [50, 100, 200, 500, 1000], "AI latency")
        self.create_gauge("ai_error_rate", "AI error rate")

        # RAG metrics
        self.create_counter("rag_queries_total", "Total RAG queries")
        self.create_histogram("rag_retrieval_time_ms", [10, 50, 100, 200], "RAG retrieval time")
        self.create_histogram("rag_generation_time_ms", [50, 100, 200, 500], "RAG generation time")
        self.create_summary("rag_documents_retrieved", [0.5, 0.9, 0.95], "Documents retrieved")
        self.create_summary("rag_relevance_score", [0.5, 0.9, 0.95], "Relevance score")

        # Guardrails metrics
        self.create_counter("guardrails_input_checks_total", "Input safety checks")
        self.create_counter("guardrails_output_checks_total", "Output safety checks")
        self.create_counter("guardrails_violations_total", "Safety violations")
        self.create_counter("guardrails_rate_limited_total", "Rate limited requests")
        self.create_counter("guardrails_pii_detected_total", "PII detected")

        # System metrics
        self.create_gauge("system_cpu_usage_percent", "CPU usage")
        self.create_gauge("system_memory_usage_percent", "Memory usage")
        self.create_gauge("system_disk_usage_percent", "Disk usage")
        self.create_counter("system_uptime_seconds", "System uptime")

    def create_counter(self, name: str, help_text: str = "") -> Counter:
        """
        Create a counter metric

        Args:
            name: Metric name
            help_text: Help text

        Returns:
            Counter metric
        """
        if name not in self.counters:
            self.counters[name] = Counter(name, help_text)
        return self.counters[name]

    def create_gauge(self, name: str, help_text: str = "") -> Gauge:
        """
        Create a gauge metric

        Args:
            name: Metric name
            help_text: Help text

        Returns:
            Gauge metric
        """
        if name not in self.gauges:
            self.gauges[name] = Gauge(name, help_text)
        return self.gauges[name]

    def create_histogram(
        self, name: str, buckets: Optional[List[float]] = None, help_text: str = ""
    ) -> Histogram:
        """
        Create a histogram metric

        Args:
            name: Metric name
            buckets: Bucket boundaries
            help_text: Help text

        Returns:
            Histogram metric
        """
        if name not in self.histograms:
            self.histograms[name] = Histogram(name, buckets, help_text)
        return self.histograms[name]

    def create_summary(
        self, name: str, quantiles: Optional[List[float]] = None, help_text: str = ""
    ) -> Summary:
        """
        Create a summary metric

        Args:
            name: Metric name
            quantiles: Quantiles to track
            help_text: Help text

        Returns:
            Summary metric
        """
        if name not in self.summaries:
            self.summaries[name] = Summary(name, quantiles, help_text)
        return self.summaries[name]

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get all metrics

        Returns:
            Dictionary with all metrics
        """
        return {
            "counters": {name: {"value": counter.get()} for name, counter in self.counters.items()},
            "gauges": {name: {"value": gauge.get()} for name, gauge in self.gauges.items()},
            "histograms": {name: histogram.get() for name, histogram in self.histograms.items()},
            "summaries": {name: summary.get() for name, summary in self.summaries.items()},
        }

    def export_prometheus(self) -> str:
        """
        Export metrics in Prometheus format

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []

        # Export counters
        for name, counter in self.counters.items():
            lines.append(f"# TYPE {name} counter")
            if counter.help_text:
                lines.append(f"# HELP {name} {counter.help_text}")
            lines.append(f"{name} {counter.get()}")

        # Export gauges
        for name, gauge in self.gauges.items():
            lines.append(f"# TYPE {name} gauge")
            if gauge.help_text:
                lines.append(f"# HELP {name} {gauge.help_text}")
            lines.append(f"{name} {gauge.get()}")

        # Export histograms
        for name, histogram in self.histograms.items():
            lines.append(f"# TYPE {name} histogram")
            if histogram.help_text:
                lines.append(f"# HELP {name} {histogram.help_text}")

            data = histogram.get()
            for bucket, count in data["buckets"].items():
                lines.append(f'{name}_bucket{{le="{bucket}"}} {count}')
            lines.append(f"{name}_bucket{{le=\"+Inf\"}} {data['count']}")
            lines.append(f"{name}_sum {data['sum']}")
            lines.append(f"{name}_count {data['count']}")

        # Export summaries
        for name, summary in self.summaries.items():
            lines.append(f"# TYPE {name} summary")
            if summary.help_text:
                lines.append(f"# HELP {name} {summary.help_text}")

            data = summary.get()
            for quantile, value in data["quantiles"].items():
                lines.append(f'{name}{{quantile="{quantile}"}} {value}')
            lines.append(f"{name}_sum {data['sum']}")
            lines.append(f"{name}_count {data['count']}")

        return "\n".join(lines)


# Global instance
metrics_collector = MetricsCollector()
