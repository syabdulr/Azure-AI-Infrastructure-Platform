"""Base cache interface."""

from abc import ABC, abstractmethod
from typing import Optional, Any, Dict
from datetime import datetime, timedelta

from .models import CacheEntry, CacheResult, CacheMetrics, CacheStatus


class CacheBackend(ABC):
    """Abstract base class for cache backends."""

    def __init__(self, default_ttl: int = 3600):
        """
        Initialize cache backend.

        Args:
            default_ttl: Default TTL in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self.metrics = CacheMetrics()

    @abstractmethod
    async def get(self, key: str) -> CacheResult:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            CacheResult with status and entry
        """
        pass

    @abstractmethod
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
            ttl: TTL in seconds (uses default if None)
            metadata: Additional metadata (provider, model, tokens, cost)

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def size(self) -> int:
        """
        Get the number of entries in cache.

        Returns:
            Number of entries
        """
        pass

    @abstractmethod
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        pass

    def create_cache_entry(
        self,
        key: str,
        value: Any,
        ttl: int,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CacheEntry:
        """
        Create a cache entry.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds
            metadata: Additional metadata

        Returns:
            CacheEntry
        """
        now = datetime.now()

        return CacheEntry(
            key=key,
            value=value,
            ttl_seconds=ttl,
            created_at=now,
            expires_at=now + timedelta(seconds=ttl),
            provider=metadata.get("provider", "unknown") if metadata else "unknown",
            model=metadata.get("model", "unknown") if metadata else "unknown",
            prompt_tokens=metadata.get("prompt_tokens", 0) if metadata else 0,
            completion_tokens=metadata.get("completion_tokens", 0) if metadata else 0,
            cost=metadata.get("cost", 0.0) if metadata else 0.0
        )

    def get_metrics(self) -> CacheMetrics:
        """
        Get cache metrics.

        Returns:
            CacheMetrics
        """
        return self.metrics

    def reset_metrics(self):
        """Reset cache metrics."""
        self.metrics.reset()

    async def get_or_set(
        self,
        key: str,
        value_factory,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> CacheResult:
        """
        Get value from cache or set it if not present.

        Args:
            key: Cache key
            value_factory: Async function to generate value if not in cache
            ttl: TTL in seconds (uses default if None)
            metadata: Additional metadata

        Returns:
            CacheResult
        """
        # Try to get from cache
        result = await self.get(key)

        if result.is_hit:
            return result

        # Generate new value
        value = await value_factory()

        # Set in cache
        success = await self.set(key, value, ttl, metadata)

        if success:
            return CacheResult(
                status=CacheStatus.HIT,  # Treat as hit since we just cached it
                entry=self.create_cache_entry(key, value, ttl or self.default_ttl, metadata),
                key=key
            )

        return result