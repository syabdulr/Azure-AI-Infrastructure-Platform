"""
Guardrails management routes for Azure AI Infrastructure Platform

This module provides:
- Input safety check endpoints
- Output safety check endpoints
- Rate limit status endpoints
- Violation logging endpoints
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Header
from datetime import datetime
import logging

from src.api.schemas import ErrorCode, ErrorResponse
from src.api.routes.monitoring import record_request_metrics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/guardrails", tags=["guardrails"])


# ============================================================================
# Safety Check Endpoints
# ============================================================================

@router.post("/check-input")
async def check_input_safety(
    request: dict,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Dict[str, Any]:
    """
    Check input safety
    
    Args:
        request: Request with 'text' and optional 'endpoint'
        x_user_id: User ID from header
        
    Returns:
        Safety assessment results
    """
    start_time = datetime.utcnow()
    
    try:
        from src.guardrails.safety_manager import safety_manager
        
        # Get user ID
        user_id = x_user_id or request.get("user_id", "anonymous")
        text = request.get("text", "")
        endpoint = request.get("endpoint", "/chat")
        
        # Check input safety
        result = safety_manager.check_input(
            user_id=user_id,
            text=text,
            endpoint=endpoint
        )
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            **result,
            "checked_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Failed to check input safety: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to check input safety: {str(e)}",
                details={},
                timestamp=datetime.utcnow()
            )
        )


@router.post("/check-output")
async def check_output_safety(
    request: dict,
    x_user_id: Optional[str] = Header(None, alias="X-User-ID")
) -> Dict[str, Any]:
    """
    Check output safety
    
    Args:
        request: Request with 'text', optional 'query' and 'context'
        x_user_id: User ID from header
        
    Returns:
        Safety assessment results
    """
    start_time = datetime.utcnow()
    
    try:
        from src.guardrails.safety_manager import safety_manager
        
        # Get user ID
        user_id = x_user_id or request.get("user_id", "anonymous")
        text = request.get("text", "")
        query = request.get("query")
        context = request.get("context")
        
        # Check output safety
        result = safety_manager.check_output(
            user_id=user_id,
            text=text,
            query=query,
            context=context
        )
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            **result,
            "checked_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Failed to check output safety: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to check output safety: {str(e)}",
                details={},
                timestamp=datetime.utcnow()
            )
        )


# ============================================================================
# Rate Limiting Endpoints
# ============================================================================

@router.get("/limits/{user_id}")
async def get_rate_limit_status(user_id: str) -> Dict[str, Any]:
    """
    Get rate limit status for user
    
    Args:
        user_id: User ID
        
    Returns:
        Rate limit status
    """
    start_time = datetime.utcnow()
    
    try:
        from src.guardrails.rate_limiter import rate_limiter
        
        # Get user status
        status = rate_limiter.get_user_status(user_id)
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            **status,
            "checked_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Failed to get rate limit status: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get rate limit status: {str(e)}",
                details={},
                timestamp=datetime.utcnow()
            )
        )


# ============================================================================
# Violation Logging Endpoints
# ============================================================================

@router.get("/violations")
async def get_violations(
    user_id: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100)
) -> Dict[str, Any]:
    """
    Get recent safety violations
    
    Args:
        user_id: Filter by user (optional)
        severity: Filter by severity (optional)
        limit: Number of results (default: 50)
        
    Returns:
        List of violations
    """
    start_time = datetime.utcnow()
    
    try:
        from src.guardrails.safety_manager import safety_manager
        
        # Get violations
        violations = safety_manager.get_violations(
            user_id=user_id,
            severity=severity,
            limit=limit
        )
        
        # Get total count (without limit)
        all_violations = safety_manager.get_violations(
            user_id=user_id,
            severity=severity,
            limit=10000
        )
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            "violations": violations,
            "total": len(all_violations),
            "count": len(violations),
            "filters": {
                "user_id": user_id,
                "severity": severity,
                "limit": limit
            },
            "queried_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Failed to get violations: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get violations: {str(e)}",
                details={},
                timestamp=datetime.utcnow()
            )
        )


@router.get("/violations/{user_id}/summary")
async def get_user_violation_summary(user_id: str) -> Dict[str, Any]:
    """
    Get violation summary for a user
    
    Args:
        user_id: User ID
        
    Returns:
        Violation summary
    """
    start_time = datetime.utcnow()
    
    try:
        from src.guardrails.safety_manager import safety_manager
        
        # Get summary
        summary = safety_manager.get_user_violation_summary(user_id)
        
        # Check thresholds
        threshold_check = safety_manager.check_user_thresholds(user_id)
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            **summary,
            "threshold_check": threshold_check,
            "queried_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Failed to get violation summary: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get violation summary: {str(e)}",
                details={},
                timestamp=datetime.utcnow()
            )
        )


# ============================================================================
# Policy Management Endpoints
# ============================================================================

@router.get("/policies")
async def list_policies() -> Dict[str, Any]:
    """
    List all safety policies
    
    Returns:
        List of policy names
    """
    start_time = datetime.utcnow()
    
    try:
        from src.guardrails.safety_manager import safety_manager
        
        # Get policies
        policy_names = safety_manager.list_policies()
        
        # Get policy details
        policies = {}
        for name in policy_names:
            policy = safety_manager.get_policy(name)
            if policy:
                policies[name] = {
                    "name": policy.name,
                    "pii_detection_enabled": policy.pii_detection_enabled,
                    "content_filtering_enabled": policy.content_filtering_enabled,
                    "output_safety_checks_enabled": policy.output_safety_checks_enabled,
                    "rate_limiting_enabled": policy.rate_limiting_enabled,
                    "auto_redact_pii": policy.auto_redact_pii,
                    "block_on_violation": policy.block_on_violation,
                    "violation_thresholds": policy.violation_thresholds
                }
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=False
        )
        
        return {
            "policies": policies,
            "total": len(policy_names),
            "queried_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms
        }
        
    except Exception as e:
        logger.error(f"Failed to list policies: {e}")
        
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        record_request_metrics(
            tokens=0,
            cost=0.0,
            latency_ms=latency_ms,
            error=True
        )
        
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to list policies: {str(e)}",
                details={},
                timestamp=datetime.utcnow()
            )
        )