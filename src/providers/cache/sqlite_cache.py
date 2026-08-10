"""SQLite cache backend."""

import aiosqlite
import json
import os
from typing import Optional, Any, Dict
from datetime import datetime

from .base import CacheBackend
from .models import CacheEntry, CacheResult, CacheStatus


class SQLiteCache(CacheBackend):
    """SQLite-based cache backend."""

    def __init__(self, db_path: str = ".cache/gateway.db", default_ttl: int = 3600):
        """
        Initialize SQLite cache.

        Args:
            db_path: Path to SQLite database file
            default_ttl: Default TTL in seconds
        """
        super().__init__(default_ttl=default_ttl)
        self.db_path = db_path
        self._db = None

        # Ensure directory exists (only if not using in-memory DB)
        if db_path != ":memory:":
            os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)

    async def _get_db(self):
        """Get database connection, creating if needed."""
        if self._db is None:
            self._db = await aiosqlite.connect(self.db_path)
        return self._db

    async def _initialize_db(self):
        """Initialize database schema."""
        db = await self._get_db()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                prompt_tokens INTEGER NOT NULL,
                completion_tokens INTEGER NOT NULL,
                cost REAL NOT NULL
            )
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_expires_at
            ON cache_entries(expires_at)
        """)

        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_provider_model
            ON cache_entries(provider, model)
        """)

        await db.commit()

    async def get(self, key: str) -> CacheResult:
        """
        Get a value from cache.

        Args:
            key: Cache key

        Returns:
            CacheResult
        """
        try:
            db = await self._get_db()

            cursor = await db.execute(
                "SELECT * FROM cache_entries WHERE key = ?",
                (key,)
            )
            row = await cursor.fetchone()

            if not row:
                self.metrics.record_miss()
                return CacheResult(
                    status=CacheStatus.MISS,
                    entry=None,
                    key=key
                )

            # Parse row into CacheEntry
            entry = self._row_to_entry(row)

            # Check if expired
            if entry.is_expired():
                # Delete expired entry
                await db.execute(
                    "DELETE FROM cache_entries WHERE key = ?",
                    (key,)
                )
                await db.commit()

                self.metrics.record_miss()
                return CacheResult(
                    status=CacheStatus.MISS,
                    entry=None,
                    key=key
                )

            self.metrics.record_hit()
            return CacheResult(
                status=CacheStatus.HIT,
                entry=entry,
                key=key
            )

        except Exception as e:
            self.metrics.record_miss()
            return CacheResult(
                status=CacheStatus.MISS,
                entry=None,
                key=key
            )

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
        try:
            ttl = ttl or self.default_ttl

            entry = self.create_cache_entry(key, value, ttl, metadata)

            db = await self._get_db()

            await db.execute("""
                INSERT OR REPLACE INTO cache_entries
                (key, value, ttl_seconds, created_at, expires_at, provider, model, prompt_tokens, completion_tokens, cost)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entry.key,
                json.dumps(entry.value),
                entry.ttl_seconds,
                entry.created_at.isoformat(),
                entry.expires_at.isoformat(),
                entry.provider,
                entry.model,
                entry.prompt_tokens,
                entry.completion_tokens,
                entry.cost
            ))

            await db.commit()
            return True

        except Exception as e:
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete a value from cache.

        Args:
            key: Cache key

        Returns:
            True if deleted, False otherwise
        """
        try:
            db = await self._get_db()

            cursor = await db.execute(
                "DELETE FROM cache_entries WHERE key = ?",
                (key,)
            )
            await db.commit()

            return cursor.rowcount > 0

        except Exception as e:
            return False

    async def clear(self) -> bool:
        """
        Clear all cache entries.

        Returns:
            True if successful, False otherwise
        """
        try:
            db = await self._get_db()

            await db.execute("DELETE FROM cache_entries")
            await db.commit()
            return True

        except Exception as e:
            return False

    async def size(self) -> int:
        """
        Get the number of entries in cache.

        Returns:
            Number of entries
        """
        try:
            db = await self._get_db()

            cursor = await db.execute("SELECT COUNT(*) FROM cache_entries")
            result = await cursor.fetchone()
            return result[0] if result else 0

        except Exception as e:
            return 0

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries from cache.

        Returns:
            Number of entries removed
        """
        try:
            db = await self._get_db()

            now = datetime.now().isoformat()

            cursor = await db.execute(
                "DELETE FROM cache_entries WHERE expires_at < ?",
                (now,)
            )
            await db.commit()

            deleted = cursor.rowcount
            self.metrics.record_eviction()
            return deleted

        except Exception as e:
            return 0

    def _row_to_entry(self, row) -> CacheEntry:
        """
        Convert database row to CacheEntry.

        Args:
            row: Database row

        Returns:
            CacheEntry
        """
        return CacheEntry(
            key=row[0],
            value=json.loads(row[1]),
            ttl_seconds=row[2],
            created_at=datetime.fromisoformat(row[3]),
            expires_at=datetime.fromisoformat(row[4]),
            provider=row[5],
            model=row[6],
            prompt_tokens=row[7],
            completion_tokens=row[8],
            cost=row[9]
        )

    async def initialize(self):
        """Initialize the cache database."""
        await self._initialize_db()

    async def get_entries_by_provider(self, provider: str) -> list[CacheEntry]:
        """
        Get all entries for a provider.

        Args:
            provider: Provider name

        Returns:
            List of CacheEntry
        """
        try:
            db = await self._get_db()

            cursor = await db.execute(
                "SELECT * FROM cache_entries WHERE provider = ?",
                (provider,)
            )
            rows = await cursor.fetchall()

            return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            return []

    async def get_entries_by_model(self, provider: str, model: str) -> list[CacheEntry]:
        """
        Get all entries for a provider and model.

        Args:
            provider: Provider name
            model: Model name

        Returns:
            List of CacheEntry
        """
        try:
            db = await self._get_db()

            cursor = await db.execute(
                "SELECT * FROM cache_entries WHERE provider = ? AND model = ?",
                (provider, model)
            )
            rows = await cursor.fetchall()

            return [self._row_to_entry(row) for row in rows]

        except Exception as e:
            return []

    async def close(self):
        """Close the database connection."""
        if self._db is not None:
            await self._db.close()
            self._db = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()