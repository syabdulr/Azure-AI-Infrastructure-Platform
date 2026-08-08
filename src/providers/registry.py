"""Provider registry for managing multiple LLM providers."""

from datetime import datetime
from typing import Dict, List, Optional, Set
import asyncio
import logging

from .base import Provider, ProviderError
from .models import (
    ProviderConfig,
    ModelConfig,
    ProviderStatus,
    HealthCheckResult,
    RoutingStrategy,
    GatewayRequest,
    GatewayResponse,
    RoutingDecision,
    ModelCapability
)

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    Registry for managing multiple LLM providers.

    Handles provider registration, health monitoring, and provides
    unified interface for routing requests across providers.
    """

    def __init__(self):
        """Initialize provider registry."""
        self._providers: Dict[str, Provider] = {}
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._health_check_results: Dict[str, HealthCheckResult] = {}
        self._round_robin_index = 0
        self._lock = asyncio.Lock()

    async def register(self, provider: Provider) -> None:
        """
        Register a provider.

        Args:
            provider: Provider instance to register
        """
        async with self._lock:
            if provider.config.name in self._providers:
                raise ValueError(
                    f"Provider {provider.config.name} already registered"
                )

            self._providers[provider.config.name] = provider
            logger.info(f"Registered provider: {provider.config.name}")

            # Perform initial health check
            await self._check_provider_health(provider)

    async def unregister(self, provider_name: str) -> None:
        """
        Unregister a provider.

        Args:
            provider_name: Name of provider to unregister
        """
        async with self._lock:
            if provider_name not in self._providers:
                raise ValueError(f"Provider {provider_name} not registered")

            del self._providers[provider_name]
            del self._health_check_results[provider_name]
            logger.info(f"Unregistered provider: {provider_name}")

    def get_provider(self, name: str) -> Optional[Provider]:
        """Get provider by name."""
        return self._providers.get(name)

    def get_all_providers(self) -> List[Provider]:
        """Get all registered providers."""
        return list(self._providers.values())

    def get_healthy_providers(self) -> List[Provider]:
        """Get all healthy providers."""
        return [
            provider
            for provider in self._providers.values()
            if provider.is_healthy()
        ]

    def get_available_providers(self) -> List[Provider]:
        """Get all available providers (healthy or degraded)."""
        return [
            provider
            for provider in self._providers.values()
            if provider.is_available()
        ]

    def get_provider_status(self, name: str) -> Optional[ProviderStatus]:
        """Get provider status."""
        provider = self._providers.get(name)
        return provider.status if provider else None

    def get_health_check_result(self, name: str) -> Optional[HealthCheckResult]:
        """Get latest health check result."""
        return self._health_check_results.get(name)

    async def start_health_checks(self) -> None:
        """Start periodic health checks for all providers."""
        if self._health_check_task and not self._health_check_task.done():
            logger.warning("Health checks already running")
            return

        self._health_check_task = asyncio.create_task(self._health_check_loop())
        logger.info("Started health check loop")

    async def stop_health_checks(self) -> None:
        """Stop periodic health checks."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
            logger.info("Stopped health check loop")

    async def _health_check_loop(self) -> None:
        """Main health check loop."""
        while True:
            try:
                await self._check_all_providers()
                await asyncio.sleep(self._health_check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(self._health_check_interval)

    async def _check_all_providers(self) -> None:
        """Check health of all providers."""
        tasks = [
            self._check_provider_health(provider)
            for provider in self._providers.values()
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _check_provider_health(self, provider: Provider) -> None:
        """
        Check health of a single provider.

        Args:
            provider: Provider to check
        """
        try:
            result = await provider.health_check()
            self._health_check_results[provider.config.name] = result

            # Update provider status based on health check
            if result.status == ProviderStatus.HEALTHY:
                provider.status = ProviderStatus.HEALTHY
            elif result.status == ProviderStatus.DEGRADED:
                provider.status = ProviderStatus.DEGRADED
            else:
                provider.status = ProviderStatus.UNHEALTHY

            logger.debug(
                f"Health check for {provider.config.name}: "
                f"{result.status.value} ({result.latency_ms}ms)"
            )

        except Exception as e:
            logger.error(f"Health check failed for {provider.config.name}: {e}")
            provider.status = ProviderStatus.UNHEALTHY
            self._health_check_results[provider.config.name] = HealthCheckResult(
                provider_name=provider.config.name,
                status=ProviderStatus.UNHEALTHY,
                timestamp=datetime.now(),
                latency_ms=0.0,
                error=str(e)
            )

    async def route_request(
        self,
        request: GatewayRequest
    ) -> GatewayResponse:
        """
        Route a request to an appropriate provider.

        Args:
            request: The gateway request

        Returns:
            GatewayResponse from the chosen provider

        Raises:
            ProviderError: If no suitable provider is available
        """
        strategy = request.routing_strategy or RoutingStrategy.COST_OPTIMIZED
        decision = await self._make_routing_decision(request, strategy)

        logger.info(
            f"Routing request {request.request_id} to "
            f"{decision.provider_name} using {strategy.value}"
        )

        try:
            provider = self._providers[decision.provider_name]
            response = await provider.generate_with_fallback(
                request,
                model=decision.model_name
            )

            # Add routing metadata
            response.routing_strategy = strategy
            response.routing_reason = decision.reason

            return response

        except ProviderError as e:
            # Try alternate providers if available
            if decision.alternate_providers:
                logger.warning(
                    f"Primary provider {decision.provider_name} failed, "
                    f"trying alternates"
                )
                for alt_provider_name in decision.alternate_providers:
                    try:
                        alt_provider = self._providers[alt_provider_name]
                        response = await alt_provider.generate_with_fallback(
                            request,
                            model=decision.model_name
                        )
                        response.routing_strategy = strategy
                        response.routing_reason = (
                            f"{decision.reason} (fallback from {decision.provider_name})"
                        )
                        return response
                    except ProviderError:
                        continue

            raise ProviderError(
                f"All providers failed for request {request.request_id}"
            )

    async def _make_routing_decision(
        self,
        request: GatewayRequest,
        strategy: RoutingStrategy
    ) -> RoutingDecision:
        """
        Make a routing decision based on strategy.

        Args:
            request: The gateway request
            strategy: Routing strategy to use

        Returns:
            RoutingDecision with chosen provider and reason
        """
        available_providers = self.get_available_providers()

        if not available_providers:
            raise ProviderError("No available providers")

        # Strategy implementations
        if strategy == RoutingStrategy.ROUND_ROBIN:
            return await self._route_round_robin(available_providers, request)
        elif strategy == RoutingStrategy.COST_OPTIMIZED:
            return await self._route_cost_optimized(available_providers, request)
        elif strategy == RoutingStrategy.PERFORMANCE_BASED:
            return await self._route_performance_based(available_providers, request)
        elif strategy == RoutingStrategy.HEALTH_BASED:
            return await self._route_health_based(available_providers, request)
        elif strategy == RoutingStrategy.CAPABILITY_BASED:
            return await self._route_capability_based(available_providers, request)
        else:
            # Default to cost optimized
            return await self._route_cost_optimized(available_providers, request)

    async def _route_round_robin(
        self,
        providers: List[Provider],
        request: GatewayRequest
    ) -> RoutingDecision:
        """Route using round-robin strategy."""
        async with self._lock:
            provider = providers[self._round_robin_index % len(providers)]
            self._round_robin_index += 1

        return RoutingDecision(
            provider_name=provider.config.name,
            model_name=list(provider.get_available_models().keys())[0],
            strategy=RoutingStrategy.ROUND_ROBIN,
            reason="Round-robin selection",
            confidence=0.7,
            alternate_providers=[p.config.name for p in providers if p != provider]
        )

    async def _route_cost_optimized(
        self,
        providers: List[Provider],
        request: GatewayRequest
    ) -> RoutingDecision:
        """Route to cheapest available provider."""
        required_capabilities = request.model_requirements or set()

        # Filter providers with required capabilities
        capable_providers = []
        for provider in providers:
            for model in provider.get_available_models().values():
                if required_capabilities.issubset(model.capabilities):
                    capable_providers.append((provider, model))
                    break

        if not capable_providers:
            # Fall back to any provider if no capabilities specified
            capable_providers = [
                (p, list(p.get_available_models().values())[0])
                for p in providers
            ]

        # Sort by cost
        capable_providers.sort(key=lambda x: x[1].cost_per_1k_tokens)

        provider, model = capable_providers[0]
        alternate_providers = [
            p.config.name for p, _ in capable_providers[1:5]  # Top 4 alternates
        ]

        return RoutingDecision(
            provider_name=provider.config.name,
            model_name=model.name,
            strategy=RoutingStrategy.COST_OPTIMIZED,
            reason=f"Cheapest provider with required capabilities (${model.cost_per_1k_tokens}/1k tokens)",
            confidence=0.8,
            alternate_providers=alternate_providers
        )

    async def _route_performance_based(
        self,
        providers: List[Provider],
        request: GatewayRequest
    ) -> RoutingDecision:
        """Route to best performing provider (lowest latency, highest success rate)."""
        # Score providers based on success rate and latency
        scored_providers = []
        for provider in providers:
            success_rate = provider.get_success_rate()
            latency = provider.metrics.avg_latency_ms

            # Normalize latency (lower is better)
            latency_score = max(0, 1 - (latency / 5000))  # 5s = 0 score

            # Combined score
            combined_score = (success_rate * 0.6) + (latency_score * 0.4)
            scored_providers.append((provider, combined_score))

        # Sort by score descending
        scored_providers.sort(key=lambda x: x[1], reverse=True)

        provider = scored_providers[0][0]
        model = list(provider.get_available_models().keys())[0]
        alternate_providers = [
            p.config.name for p, _ in scored_providers[1:5]
        ]

        return RoutingDecision(
            provider_name=provider.config.name,
            model_name=model.name,
            strategy=RoutingStrategy.PERFORMANCE_BASED,
            reason=f"Highest performing provider (success: {provider.get_success_rate():.1%}, latency: {provider.metrics.avg_latency_ms:.0f}ms)",
            confidence=0.75,
            alternate_providers=alternate_providers
        )

    async def _route_health_based(
        self,
        providers: List[Provider],
        request: GatewayRequest
    ) -> RoutingDecision:
        """Route to healthiest provider only."""
        healthy_providers = self.get_healthy_providers()

        if healthy_providers:
            providers = healthy_providers

        # Sort by health check result (success rate)
        sorted_providers = sorted(
            providers,
            key=lambda p: self._health_check_results.get(
                p.config.name,
                HealthCheckResult(
                    provider_name=p.config.name,
                    status=ProviderStatus.UNKNOWN,
                    timestamp=datetime.now(),
                    latency_ms=0.0
                )
            ).success_rate or 0.0,
            reverse=True
        )

        provider = sorted_providers[0]
        model = list(provider.get_available_models().keys())[0]
        alternate_providers = [p.config.name for p in sorted_providers[1:5]]

        return RoutingDecision(
            provider_name=provider.config.name,
            model_name=model.name,
            strategy=RoutingStrategy.HEALTH_BASED,
            reason=f"Healthiest provider (status: {provider.status.value})",
            confidence=0.85,
            alternate_providers=alternate_providers
        )

    async def _route_capability_based(
        self,
        providers: List[Provider],
        request: GatewayRequest
    ) -> RoutingDecision:
        """Route based on required capabilities."""
        required_capabilities = request.model_requirements or set()

        if not required_capabilities:
            # Fall back to cost optimized if no capabilities required
            return await self._route_cost_optimized(providers, request)

        # Find providers with all required capabilities
        capable_providers = []
        for provider in providers:
            for model in provider.get_available_models().values():
                if required_capabilities.issubset(model.capabilities):
                    capable_providers.append((provider, model))

        if not capable_providers:
            raise ProviderError(
                f"No provider supports required capabilities: {required_capabilities}"
            )

        # Sort by cost
        capable_providers.sort(key=lambda x: x[1].cost_per_1k_tokens)

        provider, model = capable_providers[0]
        alternate_providers = [
            p.config.name for p, _ in capable_providers[1:5]
        ]

        return RoutingDecision(
            provider_name=provider.config.name,
            model_name=model.name,
            strategy=RoutingStrategy.CAPABILITY_BASED,
            reason=f"Provider with required capabilities: {required_capabilities}",
            confidence=0.9,
            alternate_providers=alternate_providers
        )