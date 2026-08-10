"""Cache manager for multi-provider AI gateway."""

from typing import Optional, Any, Dict
from datetime import datetime

from .base import CacheBackend
from .sqlite_cache import SQLiteCache
from .models import CacheEntry, CacheResult, CacheMetrics, CacheStatus


class CacheManager:
    """Manages caching for the multi-provider gateway."""

    def __init__(self, backend: Optional[CacheBackend] = None):
        """
        Initialize cache manager.

        Args:
            backend: Cache backend to use (creates SQLite backend if None)
        """
        self.backend = backend or SQLiteCache()
        self.enabled = True

        # Default TTLs per model (in seconds)
        self.model_ttl_defaults = {
            "gpt-4": 3600,  # 1 hour
            "gpt-4-turbo": 3600,  # 1 hour
            "gpt-3.5-turbo": 1800,  # 30 minutes
            "gpt-3.5-turbo-16k": 1800,  # 30 minutes
        }

    async def initialize(self):
        """Initialize the cache backend."""
        if hasattr(self.backend, 'initialize'):
            await self.backend.initialize()

    async def get(self, key: str) -> CacheResult:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            CacheResult
        """
        if not self.enabled:
            return CacheResult(
                status=CacheStatus.MISS,
                entry=None,
                key=key
            )

        return await self.backend.get(key)

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Set a value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
            metadata: Additional metadata

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        # Use default TTL for model if not specified
        if ttl is None and metadata and "model" in metadata:
            model = metadata["model"]
            ttl = self.model_ttl_defaults.get(model, self.backend.default_ttl)

        return await self.backend.set(key, value, ttl, metadata)

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        return await self.backend.delete(key)

    async def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        return await self.backend.clear()

    async def size(self) -> int:
        """
        Get the number of entries in cache.

        Returns:
            Number of entries
        """
        return await self.backend.size()

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        return await self.backend.cleanup_expired()

    def get_metrics(self) -> CacheMetrics:
        """
        Get cache metrics.

        Returns:
            CacheMetrics
        """
        return self.backend.get_metrics()

    def reset_metrics(self):
        """Reset cache metrics."""
        self.backend.reset_metrics()

    def enable(self):
        """Enable caching."""
        self.enabled = True

    def disable(self):
        """Disable caching."""
        self.enabled = False

    def is_enabled(self) -> bool:
        """
        Check if caching is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self.enabled

    def set_model_ttl(self, model: str, ttl: int):
        """
        Set default TTL for a model.

        Args:
            model: Model name
            ttl: TTL in seconds
        """
        self.model_ttl_defaults[model] = ttl

    def get_model_ttl(self, model: str) -> Optional[int]:
        """
        Get default TTL for a model.

        Args:
            model: Model name

        Returns:
            TTL in seconds or None if not set
        """
        return self.model_ttl_defaults.get(model)

    async def get_cost_savings(self) -> Dict[str, Any]:
        """
        Calculate cost savings from cache hits.

        Returns:
            Dictionary with savings metrics
        """
        metrics = self.get_metrics()

        # Estimate savings based on hit rate
        # Assume average cost per API call is $0.01
        avg_cost_per_call = 0.01

        hits = metrics.hits + metrics.stale_hits
        savings = hits * avg_cost_per_call

        return {
            "total_hits": hits,
            "total_misses": metrics.misses,
            "hit_rate": metrics.hit_rate,
            "estimated_savings_usd": savings,
            "metrics": metrics.to_dict()
        }

    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        metrics = self.get_metrics()
        size = await self.size()
        savings = await self.get_cost_savings()

        return {
            "enabled": self.enabled,
            "size": size,
            "backend": self.backend.__class__.__name__,
            "metrics": metrics.to_dict(),
            "cost_savings": savings
        }


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """
    Get the global cache manager instance.

    Returns:
        Global CacheManager instance
    """
    global _cache_manager

    if _cache_manager is None:
        _cache_manager = CacheManager()

    return _cache_manager