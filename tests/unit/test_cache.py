"""Tests for cache module."""

import pytest
import asyncio
from datetime import datetime, timedelta

from src.providers.cache.models import (
    CacheStatus,
    CacheEntry,
    CacheResult,
    CacheMetrics
)
from src.providers.cache.key_generator import (
    generate_cache_key,
    generate_cache_key_from_request,
    hash_string
)
from src.providers.cache.sqlite_cache import SQLiteCache
from src.providers.cache.manager import CacheManager, get_cache_manager


class TestCacheEntry:
    """Tests for CacheEntry model."""

    def test_cache_entry_creation(self):
        """Test creating a cache entry."""
        entry = CacheEntry(
            key="test_key",
            value={"content": "test"},
            ttl_seconds=3600,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.003
        )

        assert entry.key == "test_key"
        assert entry.value["content"] == "test"
        assert entry.provider == "openai"
        assert entry.model == "gpt-4"
        assert entry.is_expired() is False

    def test_cache_entry_expiry(self):
        """Test cache entry expiry."""
        # Expired entry
        expired_entry = CacheEntry(
            key="expired_key",
            value="test",
            ttl_seconds=3600,
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1),
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.003
        )

        assert expired_entry.is_expired() is True

        # Non-expired entry
        valid_entry = CacheEntry(
            key="valid_key",
            value="test",
            ttl_seconds=3600,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.003
        )

        assert valid_entry.is_expired() is False

    def test_cache_entry_age(self):
        """Test cache entry age calculation."""
        entry = CacheEntry(
            key="test_key",
            value="test",
            ttl_seconds=3600,
            created_at=datetime.now() - timedelta(seconds=30),
            expires_at=datetime.now() + timedelta(hours=1),
            provider="openai",
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=50,
            cost=0.003
        )

        age = entry.age_seconds()
        assert age >= 25  # Allow for test execution time
        assert age < 35


class TestCacheMetrics:
    """Tests for CacheMetrics model."""

    def test_metrics_initialization(self):
        """Test metrics initialization."""
        metrics = CacheMetrics()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.stale_hits == 0
        assert metrics.evictions == 0
        assert metrics.total_requests == 0

    def test_metrics_hit_rate(self):
        """Test hit rate calculation."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_hit()
        metrics.record_miss()

        assert metrics.total_requests == 3
        assert metrics.hit_rate == 2.0 / 3.0
        assert metrics.miss_rate == 1.0 / 3.0

    def test_metrics_stale_rate(self):
        """Test stale rate calculation."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_stale_hit()
        metrics.record_stale_hit()

        assert metrics.stale_rate == 2.0 / 3.0

    def test_metrics_reset(self):
        """Test metrics reset."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_miss()

        metrics.reset()

        assert metrics.hits == 0
        assert metrics.misses == 0
        assert metrics.total_requests == 0

    def test_metrics_to_dict(self):
        """Test metrics to dictionary conversion."""
        metrics = CacheMetrics()
        metrics.record_hit()
        metrics.record_miss()

        d = metrics.to_dict()

        assert d["hits"] == 1
        assert d["misses"] == 1
        assert d["hit_rate"] == 0.5
        assert "stale_rate" in d


class TestCacheKeyGenerator:
    """Tests for cache key generation."""

    def test_generate_cache_key_basic(self):
        """Test basic cache key generation."""
        messages = [
            {"role": "user", "content": "Hello"}
        ]

        key = generate_cache_key(
            provider="openai",
            model="gpt-4",
            messages=messages
        )

        assert "openai:gpt-4:" in key
        assert len(key.split(":")) == 3

    def test_generate_cache_key_consistency(self):
        """Test cache key consistency."""
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]

        key1 = generate_cache_key(
            provider="openai",
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        key2 = generate_cache_key(
            provider="openai",
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        assert key1 == key2

    def test_generate_cache_key_different_params(self):
        """Test different parameters produce different keys."""
        messages = [{"role": "user", "content": "Hello"}]

        key1 = generate_cache_key(
            provider="openai",
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )

        key2 = generate_cache_key(
            provider="openai",
            model="gpt-4",
            messages=messages,
            temperature=0.9
        )

        assert key1 != key2

    def test_generate_cache_key_from_request(self):
        """Test cache key from request dictionary."""
        request = {
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.7,
            "max_tokens": 1000
        }

        key = generate_cache_key_from_request(
            provider="openai",
            model="gpt-4",
            request=request
        )

        assert "openai:gpt-4:" in key

    def test_hash_string(self):
        """Test string hashing."""
        hash1 = hash_string("test string")
        hash2 = hash_string("test string")
        hash3 = hash_string("different string")

        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 16


@pytest.mark.asyncio
async def test_cache_set_and_get():
    """Test setting and getting from cache."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    key = "test_key"
    value = {"content": "test response"}

    # Set value
    success = await cache.set(key, value)
    assert success is True

    # Get value
    result = await cache.get(key)
    assert result.is_hit is True
    assert result.entry.value == value


@pytest.mark.asyncio
async def test_cache_miss():
    """Test cache miss."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    result = await cache.get("nonexistent_key")

    assert result.is_miss is True
    assert result.entry is None


@pytest.mark.asyncio
async def test_cache_expiry():
    """Test cache entry expiry."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    key = "expiring_key"
    value = "test"

    # Set with very short TTL
    success = await cache.set(key, value, ttl=1)
    assert success is True

    # Should be available immediately
    result = await cache.get(key)
    assert result.is_hit is True

    # Wait for expiry
    await asyncio.sleep(2)

    # Should be expired
    result = await cache.get(key)
    assert result.is_miss is True


@pytest.mark.asyncio
async def test_cache_delete():
    """Test deleting from cache."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    key = "delete_key"
    value = "test"

    await cache.set(key, value)

    # Verify it exists
    result = await cache.get(key)
    assert result.is_hit is True

    # Delete it
    success = await cache.delete(key)
    assert success is True

    # Verify it's gone
    result = await cache.get(key)
    assert result.is_miss is True


@pytest.mark.asyncio
async def test_cache_clear():
    """Test clearing cache."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    await cache.set("key1", "value1")
    await cache.set("key2", "value2")
    await cache.set("key3", "value3")

    size = await cache.size()
    assert size == 3

    await cache.clear()

    size = await cache.size()
    assert size == 0


@pytest.mark.asyncio
async def test_cache_size():
    """Test cache size."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    assert await cache.size() == 0

    await cache.set("key1", "value1")
    assert await cache.size() == 1

    await cache.set("key2", "value2")
    assert await cache.size() == 2


@pytest.mark.asyncio
async def test_cache_cleanup_expired():
    """Test cleaning up expired entries."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    # Set some entries with different TTLs
    await cache.set("valid_key", "value1", ttl=3600)
    await cache.set("expired_key1", "value2", ttl=1)
    await cache.set("expired_key2", "value3", ttl=1)

    # Wait for expiry
    await asyncio.sleep(2)

    # Cleanup
    removed = await cache.cleanup_expired()
    assert removed >= 2  # At least the two expired entries

    # Verify size
    size = await cache.size()
    assert size == 1  # Only valid_key remains


@pytest.mark.asyncio
async def test_cache_metrics():
    """Test cache metrics."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    # Hit
    await cache.set("key1", "value1")
    await cache.get("key1")

    # Miss
    await cache.get("nonexistent")

    metrics = cache.get_metrics()

    assert metrics.hits == 1
    assert metrics.misses == 1
    assert metrics.total_requests == 2
    assert metrics.hit_rate == 0.5


@pytest.mark.asyncio
async def test_cache_with_metadata():
    """Test caching with metadata."""
    cache = SQLiteCache(db_path=":memory:")
    await cache.initialize()

    key = "metadata_key"
    value = {"content": "test"}
    metadata = {
        "provider": "openai",
        "model": "gpt-4",
        "prompt_tokens": 100,
        "completion_tokens": 50,
        "cost": 0.003
    }

    await cache.set(key, value, metadata=metadata)

    result = await cache.get(key)

    assert result.is_hit is True
    assert result.entry.provider == "openai"
    assert result.entry.model == "gpt-4"
    assert result.entry.prompt_tokens == 100
    assert result.entry.completion_tokens == 50
    assert result.entry.cost == 0.003


@pytest.mark.asyncio
async def test_manager_get_and_set():
    """Test manager get and set."""
    manager = CacheManager(backend=SQLiteCache(db_path=":memory:"))
    await manager.initialize()

    key = "test_key"
    value = {"content": "test"}

    success = await manager.set(key, value)
    assert success is True

    result = await manager.get(key)
    assert result.is_hit is True


@pytest.mark.asyncio
async def test_manager_enable_disable():
    """Test enabling and disabling cache."""
    manager = CacheManager(backend=SQLiteCache(db_path=":memory:"))
    await manager.initialize()

    key = "test_key"
    value = "test"

    # Disable
    manager.disable()
    assert manager.is_enabled() is False

    # Set while disabled
    success = await manager.set(key, value)
    assert success is False

    # Get while disabled
    result = await manager.get(key)
    assert result.is_miss is True

    # Enable
    manager.enable()
    assert manager.is_enabled() is True

    # Now it works
    success = await manager.set(key, value)
    assert success is True


@pytest.mark.asyncio
async def test_manager_model_ttl():
    """Test model-specific TTLs."""
    manager = CacheManager(backend=SQLiteCache(db_path=":memory:"))
    await manager.initialize()

    manager.set_model_ttl("gpt-4", 7200)  # 2 hours

    assert manager.get_model_ttl("gpt-4") == 7200
    assert manager.get_model_ttl("gpt-3.5-turbo") == 1800  # Default


@pytest.mark.asyncio
async def test_manager_cost_savings():
    """Test cost savings calculation."""
    manager = CacheManager(backend=SQLiteCache(db_path=":memory:"))
    await manager.initialize()

    # Simulate some hits
    await manager.set("key1", "value1")
    await manager.set("key2", "value2")
    await manager.get("key1")
    await manager.get("key2")
    await manager.get("nonexistent")  # Miss

    savings = await manager.get_cost_savings()

    assert savings["total_hits"] == 2
    assert savings["total_misses"] == 1
    assert savings["hit_rate"] == 2.0 / 3.0
    assert savings["estimated_savings_usd"] == 0.02  # 2 hits * $0.01


@pytest.mark.asyncio
async def test_manager_cache_stats():
    """Test comprehensive cache stats."""
    manager = CacheManager(backend=SQLiteCache(db_path=":memory:"))
    await manager.initialize()

    stats = await manager.get_cache_stats()

    assert "enabled" in stats
    assert "size" in stats
    assert "backend" in stats
    assert "metrics" in stats
    assert "cost_savings" in stats

    assert stats["enabled"] is True
    assert stats["backend"] == "SQLiteCache"


@pytest.mark.asyncio
async def test_global_manager_singleton():
    """Test global cache manager is a singleton."""
    manager1 = get_cache_manager()
    manager2 = get_cache_manager()

    assert manager1 is manager2


@pytest.mark.asyncio
async def test_global_manager_operations():
    """Test operations on global manager."""
    manager = get_cache_manager()

    # These should work without initialization
    assert manager.is_enabled() is True

    # Can disable
    manager.disable()
    assert manager.is_enabled() is False