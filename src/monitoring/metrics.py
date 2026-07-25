"""
Metrics collector for Azure AI Infrastructure Platform

This module provides:
- Metrics collection
- Request latency tracking
- Token usage tracking
- Cost tracking
"""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import asyncio
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricsCollector:
    """Collect and aggregate application metrics"""

    def __init__(self, retention_hours: int = 24):
        """Initialize metrics collector"""
        self.retention_hours = retention_hours
        self.metrics = defaultdict(list)
        self.start_time = datetime.utcnow()
        self._lock = asyncio.Lock()

    async def record_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a metric value

        Args:
            metric_name: Name of the metric
            value: Metric value
            timestamp: Optional timestamp (defaults to now)
        """
        async with self._lock:
            timestamp = timestamp or datetime.utcnow()
            self.metrics[metric_name].append({
                "value": value,
                "timestamp": timestamp
            })

            # Cleanup old metrics
            await self._cleanup_old_metrics()

    async def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        
        for metric_name, values in self.metrics.items():
            self.metrics[metric_name] = [
                v for v in values
                if v["timestamp"] > cutoff
            ]

    async def get_metric_stats(
        self,
        metric_name: str,
        window_minutes: int = 60
    ) -> Dict[str, float]:
        """
        Get statistics for a metric

        Args:
            metric_name: Name of the metric
            window_minutes: Time window in minutes

        Returns:
            Dictionary with min, max, avg, count
        """
        async with self._lock:
            cutoff = datetime.utcnow() - timedelta(minutes=window_minutes)
            values = [
                v["value"] for v in self.metrics.get(metric_name, [])
                if v["timestamp"] > cutoff
            ]

            if not values:
                return {
                    "min": 0.0,
                    "max": 0.0,
                    "avg": 0.0,
                    "count": 0
                }

            return {
                "min": min(values),
                "max": max(values),
                "avg": sum(values) / len(values),
                "count": len(values)
            }

    async def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get all current metrics

        Returns:
            Dictionary with all metrics
        """
        async with self._lock:
            uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
            
            result = {
                "uptime_seconds": uptime_seconds,
                "metrics": {}
            }
            
            for metric_name, values in self.metrics.items():
                if values:
                    latest_value = values[-1]["value"]
                    result["metrics"][metric_name] = latest_value
            
            return result

    async def reset_metrics(self):
        """Reset all metrics"""
        async with self._lock:
            self.metrics.clear()
            self.start_time = datetime.utcnow()
            logger.info("Metrics reset")