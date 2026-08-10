"""Cache models for multi-provider AI gateway."""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any, Dict


class CacheStatus(Enum):
    """Cache status."""
    HIT = "hit"
    MISS = "miss"
    STALE = "stale"


@dataclass
class CacheEntry:
    """A cache entry with value and metadata."""

    key: str
    value: Any
    ttl_seconds: int
    created_at: datetime
    expires_at: datetime
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost: float

    def is_expired(self) -> bool:
        """Check if entry is expired."""
        return datetime.now() > self.expires_at

    def time_until_expiry(self) -> float:
        """Get seconds until expiry."""
        delta = self.expires_at - datetime.now()
        return delta.total_seconds()

    def age_seconds(self) -> float:
        """Get age of entry in seconds."""
        delta = datetime.now() - self.created_at
        return delta.total_seconds()


@dataclass
class CacheResult:
    """Result of a cache operation."""

    status: CacheStatus
    entry: Optional[CacheEntry]
    key: Optional[str]

    @property
    def is_hit(self) -> bool:
        """Whether cache was hit."""
        return self.status == CacheStatus.HIT

    @property
    def is_miss(self) -> bool:
        """Whether cache was missed."""
        return self.status == CacheStatus.MISS

    @property
    def is_stale(self) -> bool:
        """Whether cache entry was stale."""
        return self.status == CacheStatus.STALE


@dataclass
class CacheMetrics:
    """Cache performance metrics."""

    hits: int = 0
    misses: int = 0
    stale_hits: int = 0
    evictions: int = 0
    total_requests: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.hits + self.stale_hits) / self.total_requests

    @property
    def miss_rate(self) -> float:
        """Calculate miss rate."""
        if self.total_requests == 0:
            return 0.0
        return self.misses / self.total_requests

    @property
    def stale_rate(self) -> float:
        """Calculate stale rate."""
        if self.hits + self.stale_hits == 0:
            return 0.0
        return self.stale_hits / (self.hits + self.stale_hits)

    def record_hit(self):
        """Record a cache hit."""
        self.hits += 1
        self.total_requests += 1

    def record_miss(self):
        """Record a cache miss."""
        self.misses += 1
        self.total_requests += 1

    def record_stale_hit(self):
        """Record a stale cache hit."""
        self.stale_hits += 1
        self.total_requests += 1

    def record_eviction(self):
        """Record an eviction."""
        self.evictions += 1

    def reset(self):
        """Reset metrics."""
        self.hits = 0
        self.misses = 0
        self.stale_hits = 0
        self.evictions = 0
        self.total_requests = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "hits": self.hits,
            "misses": self.misses,
            "stale_hits": self.stale_hits,
            "evictions": self.evictions,
            "total_requests": self.total_requests,
            "hit_rate": self.hit_rate,
            "miss_rate": self.miss_rate,
            "stale_rate": self.stale_rate
        }