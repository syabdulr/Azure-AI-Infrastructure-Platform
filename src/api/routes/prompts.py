"""
Prompt management routes for Azure AI Infrastructure Platform

This module provides:
- List all prompt templates
- Get template details
- Create new versions
- Set active version
- Evaluate prompts
- Get version metrics
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from src.api.routes.monitoring import record_request_metrics
from src.api.schemas import ErrorCode, ErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/prompts", tags=["prompts"])


# ============================================================================
# Template Management Endpoints
# ============================================================================


@router.get("/templates")
async def list_templates() -> Dict[str, Any]:
    """
    List all available prompt templates

    Returns:
        Dictionary with list of templates
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_versioning import version_manager
        from src.llm.prompts.templates import template_factory

        # Get all template names
        template_names = template_factory.list_templates()

        # Get information for each template
        templates = []
        for name in template_names:
            template_info = version_manager.get_template_info(name)
            if template_info:
                templates.append(
                    {
                        "name": name,
                        "versions": template_info["versions"],
                        "active_version": template_info["active_version"],
                        "total_versions": template_info["total_versions"],
                    }
                )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "templates": templates,
            "total": len(templates),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to list templates: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to list templates: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/templates/{template_name}")
async def get_template_details(template_name: str) -> Dict[str, Any]:
    """
    Get prompt template details

    Args:
        template_name: Template name

    Returns:
        Template details with all versions
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_versioning import version_manager
        from src.llm.prompts.templates import template_factory

        # Get template from factory
        template = template_factory.get_template(template_name)

        if not template:
            raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")

        # Get version information
        template_info = version_manager.get_template_info(template_name)

        # Get all versions
        versions_data = {}
        for version_str in template_info["versions"]:
            version_obj = version_manager.get_version(template_name, version_str)
            if version_obj:
                versions_data[version_str] = version_obj.to_dict()

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "name": template_name,
            "active_version": template_info["active_version"],
            "versions": versions_data,
            "total_versions": len(versions_data),
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get template details: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get template details: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.post("/templates/{template_name}/versions")
async def create_template_version(template_name: str, version_data: dict) -> Dict[str, Any]:
    """
    Create a new version of a prompt template

    Args:
        template_name: Template name
        version_data: Version data with 'version', 'template', 'metadata', 'set_as_active'

    Returns:
        Created version information
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_versioning import version_manager

        # Validate required fields
        if "version" not in version_data or "template" not in version_data:
            raise HTTPException(
                status_code=400, detail="Missing required fields: 'version' and 'template'"
            )

        # Create new version
        new_version = version_manager.add_version(
            template_name=template_name,
            version=version_data["version"],
            template=version_data["template"],
            metadata=version_data.get("metadata", {}),
            set_as_active=version_data.get("set_as_active", False),
        )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "name": template_name,
            "version": new_version.version,
            "status": "created",
            "is_active": new_version.is_active,
            "created_at": new_version.created_at.isoformat(),
            "latency_ms": latency_ms,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to create template version: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to create template version: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.post("/templates/{template_name}/set-active")
async def set_active_version(template_name: str, version_data: dict) -> Dict[str, Any]:
    """
    Set the active version for a template

    Args:
        template_name: Template name
        version_data: Version data with 'version'

    Returns:
        Updated template information
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_versioning import version_manager

        # Validate required fields
        if "version" not in version_data:
            raise HTTPException(status_code=400, detail="Missing required field: 'version'")

        # Set active version
        version_manager.set_active_version(
            template_name=template_name, version=version_data["version"]
        )

        # Get updated template info
        template_info = version_manager.get_template_info(template_name)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "name": template_name,
            "active_version": template_info["active_version"],
            "status": "updated",
            "latency_ms": latency_ms,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to set active version: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to set active version: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


# ============================================================================
# Evaluation Endpoints
# ============================================================================


@router.post("/evaluate")
async def evaluate_prompt(evaluation_data: dict) -> Dict[str, Any]:
    """
    Evaluate a prompt with metrics

    Args:
        evaluation_data: Evaluation data with 'prompt', 'response', 'expected_answer', 'context', 'query'

    Returns:
        Evaluation metrics
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_evaluator import evaluator

        # Validate required fields
        if "prompt" not in evaluation_data or "response" not in evaluation_data:
            raise HTTPException(
                status_code=400, detail="Missing required fields: 'prompt' and 'response'"
            )

        # Evaluate prompt
        metrics = evaluator.evaluate(
            prompt=evaluation_data["prompt"],
            response=evaluation_data["response"],
            expected_answer=evaluation_data.get("expected_answer"),
            context=evaluation_data.get("context"),
            query=evaluation_data.get("query"),
        )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "metrics": metrics,
            "evaluated_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
        }

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to evaluate prompt: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to evaluate prompt: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


@router.get("/templates/{template_name}/metrics")
async def get_template_metrics(
    template_name: str, versions: Optional[List[str]] = Query(None)
) -> Dict[str, Any]:
    """
    Get metrics for all versions of a template

    Args:
        template_name: Template name
        versions: List of versions to compare (all if None)

    Returns:
        Version metrics
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_versioning import version_manager

        # Get version comparison
        comparison = version_manager.compare_versions(template_name, versions)

        # Get template info
        template_info = version_manager.get_template_info(template_name)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "name": template_name,
            "active_version": template_info["active_version"],
            "versions": comparison,
            "total_versions": len(comparison),
            "timestamp": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
        }

    except Exception as e:
        logger.error(f"Failed to get template metrics: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to get template metrics: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )


# ============================================================================
# Batch Operations Endpoints
# ============================================================================


@router.post("/evaluate/batch")
async def batch_evaluate_prompts(evaluations: List[dict]) -> Dict[str, Any]:
    """
    Batch evaluate multiple prompts

    Args:
        evaluations: List of evaluation dictionaries

    Returns:
        List of evaluation results
    """
    start_time = datetime.utcnow()

    try:
        from src.llm.prompt_evaluator import evaluator

        # Batch evaluate
        results = evaluator.batch_evaluate(evaluations)

        # Aggregate metrics
        aggregated = evaluator.aggregate_metrics(results)

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=False)

        return {
            "results": results,
            "aggregated": aggregated,
            "total_evaluations": len(results),
            "evaluated_at": datetime.utcnow().isoformat(),
            "latency_ms": latency_ms,
        }

    except Exception as e:
        logger.error(f"Failed to batch evaluate prompts: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        record_request_metrics(tokens=0, cost=0.0, latency_ms=latency_ms, error=True)

        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=f"Failed to batch evaluate prompts: {str(e)}",
                details={},
                timestamp=datetime.utcnow(),
            ),
        )
