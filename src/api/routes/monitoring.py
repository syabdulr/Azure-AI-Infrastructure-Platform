"""
Monitoring routes for Azure AI Infrastructure Platform
"""

import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter

from src.api.schemas import HealthCheckStatus, MetricsResponse, MonitoringStatus
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/monitoring", tags=["monitoring"])


class MetricsStore:
    """Simple in-memory metrics store"""

    def __init__(self):
        self.request_count = 0
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_latency_ms = 0.0
        self.error_count = 0
        self.start_time = datetime.utcnow()

    def record_request(self, tokens: int, cost: float, latency_ms: float, error: bool = False):
        """Record a request"""
        self.request_count += 1
        self.total_tokens += tokens
        self.total_cost += cost
        self.total_latency_ms += latency_ms
        if error:
            self.error_count += 1

    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        uptime_seconds = (datetime.utcnow() - self.start_time).total_seconds()
        error_rate = self.error_count / self.request_count if self.request_count > 0 else 0.0
        avg_latency_ms = (
            self.total_latency_ms / self.request_count if self.request_count > 0 else 0.0
        )

        return {
            "request_count": self.request_count,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "avg_latency_ms": avg_latency_ms,
            "error_rate": error_rate,
            "uptime_seconds": uptime_seconds,
        }


# Global metrics store
metrics_store = MetricsStore()


@router.get("/metrics", response_model=MetricsResponse)
async def get_metrics() -> MetricsResponse:
    """
    Get application metrics

    Returns:
        MetricsResponse with request count, tokens, cost, latency, error rate
    """
    metrics = metrics_store.get_metrics()

    return MetricsResponse(
        request_count=metrics["request_count"],
        total_tokens=metrics["total_tokens"],
        total_cost=metrics["total_cost"],
        avg_latency_ms=metrics["avg_latency_ms"],
        error_rate=metrics["error_rate"],
        uptime_seconds=metrics["uptime_seconds"],
        timestamp=datetime.utcnow(),
    )


@router.get("/status", response_model=MonitoringStatus)
async def get_status() -> MonitoringStatus:
    """
    Get monitoring status of all Azure services

    Returns:
        MonitoringStatus with health of all dependencies
    """
    settings = get_settings()

    # Simple status checks based on configuration
    azure_openai_status = (
        HealthCheckStatus.HEALTHY if settings.azure_openai_endpoint else HealthCheckStatus.UNHEALTHY
    )
    cognitive_search_status = (
        HealthCheckStatus.HEALTHY if settings.azure_search_endpoint else HealthCheckStatus.UNHEALTHY
    )
    storage_status = (
        HealthCheckStatus.HEALTHY if settings.azure_storage_account else HealthCheckStatus.UNHEALTHY
    )
    key_vault_status = (
        HealthCheckStatus.HEALTHY if settings.azure_key_vault_name else HealthCheckStatus.UNHEALTHY
    )
    app_insights_status = (
        HealthCheckStatus.HEALTHY
        if settings.azure_app_insights_name
        else HealthCheckStatus.DEGRADED
    )

    return MonitoringStatus(
        azure_openai_status=azure_openai_status,
        cognitive_search_status=cognitive_search_status,
        storage_status=storage_status,
        key_vault_status=key_vault_status,
        application_insights_status=app_insights_status,
        timestamp=datetime.utcnow(),
    )


def record_request_metrics(tokens: int, cost: float, latency_ms: float, error: bool = False):
    """Record request metrics"""
    metrics_store.record_request(tokens, cost, latency_ms, error)
