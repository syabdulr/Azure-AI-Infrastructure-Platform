"""
Observability routes for Azure AI Infrastructure Platform

This module provides:
- Metrics query API
- Logs query API
- Alerts query API
- Health status API
- System status API
- Prometheus metrics endpoint
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Response

from src.api.routes.monitoring import record_request_metrics
from src.api.schemas import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/observability", tags=["observability"])


# ============================================================================
# Metrics Endpoints
# ============================================================================


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get all metrics

    Returns:
        Dictionary with all metrics
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.metrics_collector import metrics_collector

        # Get all metrics
        metrics = metrics_collector.get_metrics()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {**metrics, "queried_at": datetime.utcnow().isoformat(), "latency_ms": latency_ms}

    except Exception as e:
        logger.error(f"Failed to get metrics: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get metrics: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/metrics/prometheus", response_class=Response)
async def get_prometheus_metrics():
    """
    Get metrics in Prometheus format

    Returns:
        Prometheus-formatted metrics (text/plain)
    """
    try:
        from src.monitoring.metrics_collector import metrics_collector

        # Export metrics in Prometheus format
        metrics_text = metrics_collector.export_prometheus()

        return Response(content=metrics_text, media_type="text/plain")

    except Exception as e:
        logger.error(f"Failed to get Prometheus metrics: {e}")
        raise HTTPException(  # type: ignore
            status_code=500, detail=f"Failed to get Prometheus metrics: {str(e)}"
        )


# ============================================================================
# Logs Endpoints
# ============================================================================


@router.get("/logs")
async def get_logs(
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
) -> Dict[str, Any]:
    """
    Query logs

    Args:
        level: Filter by level (INFO, WARNING, ERROR)
        source: Filter by source
        search: Search in message
        start_time: Start time (ISO format)
        end_time: End time (ISO format)
        limit: Maximum number of results

    Returns:
        Dictionary with logs
    """
    start_time_check = datetime.utcnow()

    try:
        from src.monitoring.log_aggregator import log_aggregator

        # Query logs
        logs = log_aggregator.query_logs(
            level=level,
            source=source,
            search=search,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )

        # Get total count
        total_logs = len(log_aggregator.logs)

        latency_ms = (datetime.utcnow() - start_time_check).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "logs": logs,
            "total": total_logs,
            "count": len(logs),
            "filters": {
                "level": level,
                "source": source,
                "search": search,
                "start_time": start_time,
                "end_time": end_time,
                "limit": limit,
            },
            "queried_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
        }

    except Exception as e:
        logger.error(f"Failed to get logs: {e}")

        latency_ms = (datetime.utcnow() - start_time_check).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get logs: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/logs/stats")
async def get_log_stats() -> Dict[str, Any]:
    """
    Get log statistics

    Returns:
        Dictionary with log statistics
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.log_aggregator import log_aggregator

        # Get log statistics
        stats = log_aggregator.get_log_stats()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {**stats, "queried_at": datetime.utcnow().isoformat(), "latency_ms": latency_ms}

    except Exception as e:
        logger.error(f"Failed to get log stats: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get log stats: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


# ============================================================================
# Alerts Endpoints
# ============================================================================


@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = Query(None),
    active_only: bool = Query(False),
    rule_name: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
) -> Dict[str, Any]:
    """
    Get alerts

    Args:
        severity: Filter by severity (low, medium, high, critical)
        active_only: Only return active alerts
        rule_name: Filter by rule name
        limit: Maximum number of results

    Returns:
        Dictionary with alerts
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.alert_manager import alert_manager

        # Get alerts
        alerts = alert_manager.get_alerts(
            severity=severity, active_only=active_only, rule_name=rule_name, limit=limit
        )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "alerts": alerts,
            "total": len(alert_manager.alerts),
            "count": len(alerts),
            "filters": {
                "severity": severity,
                "active_only": active_only,
                "rule_name": rule_name,
                "limit": limit,
            },
            "queried_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
        }

    except Exception as e:
        logger.error(f"Failed to get alerts: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get alerts: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/alerts/stats")
async def get_alert_stats() -> Dict[str, Any]:
    """
    Get alert statistics

    Returns:
        Dictionary with alert statistics
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.alert_manager import alert_manager

        # Get alert statistics
        stats = alert_manager.get_alert_stats()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {**stats, "queried_at": datetime.utcnow().isoformat(), "latency_ms": latency_ms}

    except Exception as e:
        logger.error(f"Failed to get alert stats: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get alert stats: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/alerts/rules")
async def list_alert_rules() -> Dict[str, Any]:
    """
    List all alert rules

    Returns:
        Dictionary with alert rules
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.alert_manager import alert_manager

        # List rules
        rules = alert_manager.list_rules()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "rules": rules,
            "total": len(rules),
            "queried_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
        }

    except Exception as e:
        logger.error(f"Failed to list alert rules: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to list alert rules: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


# ============================================================================
# Health Endpoints
# ============================================================================


@router.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """
    Get health status

    Returns:
        Dictionary with health status
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.health_checker import health_checker

        # Check health
        health = await health_checker.check_health()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {**health, "latency_ms": latency_ms}

    except Exception as e:
        logger.error(f"Failed to get health status: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get health status: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/health/dependencies")
async def get_dependency_status() -> Dict[str, Any]:
    """
    Get dependency status

    Returns:
        Dictionary with dependency status
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.health_checker import health_checker

        # Check dependencies
        dependencies = await health_checker.check_dependencies()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {**dependencies, "latency_ms": latency_ms}

    except Exception as e:
        logger.error(f"Failed to get dependency status: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get dependency status: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


# ============================================================================
# System Status Endpoints
# ============================================================================


@router.get("/system")
async def get_system_status() -> Dict[str, Any]:
    """
    Get system status

    Returns:
        Dictionary with system status
    """
    start_time = datetime.utcnow()

    try:
        from src.monitoring.health_checker import health_checker

        # Get system status
        status = health_checker.get_system_status()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {**status, "latency_ms": latency_ms}

    except Exception as e:
        logger.error(f"Failed to get system status: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(  # type: ignore
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get system status: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )
