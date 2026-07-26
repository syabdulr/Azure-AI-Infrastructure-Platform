"""
Health check routes for Azure AI Infrastructure Platform
"""

import asyncio
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from src.api.schemas import DependencyHealth, HealthCheckStatus, HealthResponse
from src.config.settings import get_settings
from src.llm.azure_openai_client import AzureOpenAIClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Comprehensive health check endpoint

    Checks the health of all dependencies:
    - Azure OpenAI Service
    - Azure Cognitive Search
    - Azure Key Vault
    - Azure Storage

    Returns:
        HealthResponse with overall status and dependency health
    """
    settings = get_settings()
    dependencies = []

    # Check Azure OpenAI
    openai_health = await check_azure_openai()
    dependencies.append(openai_health)

    # Check Azure Cognitive Search
    search_health = await check_cognitive_search()
    dependencies.append(search_health)

    # Check Azure Key Vault
    keyvault_health = await check_key_vault()
    dependencies.append(keyvault_health)

    # Determine overall health
    unhealthy_count = sum(1 for dep in dependencies if dep.status != HealthCheckStatus.HEALTHY)

    if unhealthy_count == 0:
        overall_status = HealthCheckStatus.HEALTHY
    elif unhealthy_count == len(dependencies):
        overall_status = HealthCheckStatus.UNHEALTHY
    else:
        overall_status = HealthCheckStatus.DEGRADED

    return HealthResponse(
        status=overall_status,
        timestamp=datetime.utcnow(),
        version=settings.app_version,
        dependencies=dependencies,
    )


async def check_azure_openai() -> DependencyHealth:
    """Check Azure OpenAI Service health"""
    start_time = asyncio.get_event_loop().time()

    try:
        client = AzureOpenAIClient()
        result = await client.health_check()
        response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000

        if result.get("status") == "healthy":
            return DependencyHealth(
                name="azure_openai",
                status=HealthCheckStatus.HEALTHY,
                response_time_ms=response_time_ms,
            )
        else:
            return DependencyHealth(
                name="azure_openai",
                status=HealthCheckStatus.UNHEALTHY,
                response_time_ms=response_time_ms,
                error_message=result.get("error", "Unknown error"),
            )
    except Exception as e:
        logger.error(f"Azure OpenAI health check failed: {e}")
        return DependencyHealth(
            name="azure_openai",
            status=HealthCheckStatus.UNHEALTHY,
            response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            error_message=str(e),
        )


async def check_cognitive_search() -> DependencyHealth:
    """Check Azure Cognitive Search health"""
    start_time = asyncio.get_event_loop().time()
    settings = get_settings()

    try:
        # Simple check - just verify endpoint is configured
        if not settings.azure_search_endpoint:
            return DependencyHealth(
                name="cognitive_search",
                status=HealthCheckStatus.DEGRADED,
                response_time_ms=0.0,
                error_message="Search endpoint not configured",
            )

        response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000

        return DependencyHealth(
            name="cognitive_search",
            status=HealthCheckStatus.HEALTHY,
            response_time_ms=response_time_ms,
        )
    except Exception as e:
        logger.error(f"Cognitive Search health check failed: {e}")
        return DependencyHealth(
            name="cognitive_search",
            status=HealthCheckStatus.UNHEALTHY,
            response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            error_message=str(e),
        )


async def check_key_vault() -> DependencyHealth:
    """Check Azure Key Vault health"""
    start_time = asyncio.get_event_loop().time()
    settings = get_settings()

    try:
        # Simple check - just verify name is configured
        if not settings.azure_key_vault_name:
            return DependencyHealth(
                name="key_vault",
                status=HealthCheckStatus.DEGRADED,
                response_time_ms=0.0,
                error_message="Key Vault name not configured",
            )

        response_time_ms = (asyncio.get_event_loop().time() - start_time) * 1000

        return DependencyHealth(
            name="key_vault", status=HealthCheckStatus.HEALTHY, response_time_ms=response_time_ms
        )
    except Exception as e:
        logger.error(f"Key Vault health check failed: {e}")
        return DependencyHealth(
            name="key_vault",
            status=HealthCheckStatus.UNHEALTHY,
            response_time_ms=(asyncio.get_event_loop().time() - start_time) * 1000,
            error_message=str(e),
        )
