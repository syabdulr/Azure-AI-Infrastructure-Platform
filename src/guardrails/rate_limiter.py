"""
Rate limiter for Azure AI Infrastructure Platform

This module provides:
- Token bucket algorithm for rate limiting
- User-based rate limits
- Per-endpoint limits
- Burst handling
- Distributed support (Redis-ready)
"""

from typing import Dict, Any, Optional
import time
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class TokenBucket:
    """Token bucket for rate limiting"""
    
    def __init__(
        self,
        capacity: int,
        refill_rate: int,
        refill_interval: int = 60
    ):
        """
        Initialize token bucket
        
        Args:
            capacity: Maximum tokens (burst size)
            refill_rate: Tokens to add per refill interval
            refill_interval: Refill interval in seconds (default: 60)
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.refill_interval = refill_interval
        
        self.tokens = capacity
        self.last_refill = time.time()
    
    def refill(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_refill
        
        # Calculate how many refills have occurred
        refills = int(elapsed // self.refill_interval)
        
        if refills > 0:
            # Add tokens for each refill
            tokens_to_add = refills * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_refill = now
            
            logger.debug(f"Refilled {tokens_to_add} tokens (bucket now has {self.tokens}/{self.capacity})")
    
    def consume(self, tokens: int = 1) -> Dict[str, Any]:
        """
        Consume tokens from bucket
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            Dictionary with:
            - allowed: bool
            - remaining_tokens: int
            - retry_after: int (seconds until next token)
        """
        # Refill first
        self.refill()
        
        if self.tokens >= tokens:
            # Enough tokens available
            self.tokens -= tokens
            return {
                "allowed": True,
                "remaining_tokens": self.tokens,
                "retry_after": 0
            }
        else:
            # Not enough tokens
            # Calculate time until next token
            tokens_needed = tokens - self.tokens
            refills_needed = (tokens_needed + self.refill_rate - 1) // self.refill_rate
            retry_after = refills_needed * self.refill_interval
            
            return {
                "allowed": False,
                "remaining_tokens": self.tokens,
                "retry_after": retry_after
            }


class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(
        self,
        tokens_per_minute: int = 60,
        burst_size: Optional[int] = None
    ):
        """
        Initialize rate limiter
        
        Args:
            tokens_per_minute: Refill rate (tokens per minute)
            burst_size: Maximum burst capacity (default: same as refill rate)
        """
        self.tokens_per_minute = tokens_per_minute
        self.burst_size = burst_size or tokens_per_minute
        
        # User buckets
        self.user_buckets: Dict[str, TokenBucket] = {}
        
        # Endpoint-specific limits
        self.endpoint_limits: Dict[str, int] = {
            "/chat": 30,  # 30 requests per minute
            "/chat/stream": 60,  # 60 requests per minute (streaming)
            "/rag/query": 60,  # 60 requests per minute
            "/rag/index": 10,  # 10 requests per minute
            "/rag/index/batch": 5,  # 5 requests per minute
            "/prompts/evaluate": 30,  # 30 requests per minute
        }
        
        logger.info(f"Rate limiter initialized: {tokens_per_minute} tokens/min, burst {self.burst_size}")
    
    def _get_user_bucket(self, user_id: str) -> TokenBucket:
        """
        Get or create user's token bucket
        
        Args:
            user_id: User identifier
            
        Returns:
            TokenBucket for the user
        """
        if user_id not in self.user_buckets:
            self.user_buckets[user_id] = TokenBucket(
                capacity=self.burst_size,
                refill_rate=self.tokens_per_minute
            )
        
        return self.user_buckets[user_id]
    
    def _get_endpoint_limit(self, endpoint: str) -> int:
        """
        Get limit for specific endpoint
        
        Args:
            endpoint: API endpoint path
            
        Returns:
            Tokens per minute for endpoint
        """
        # Check exact match
        if endpoint in self.endpoint_limits:
            return self.endpoint_limits[endpoint]
        
        # Check prefix match
        for endpoint_pattern, limit in self.endpoint_limits.items():
            if endpoint.startswith(endpoint_pattern):
                return limit
        
        # Default limit
        return self.tokens_per_minute
    
    def check_limit(
        self,
        user_id: str,
        endpoint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Check if request is within rate limits
        
        Args:
            user_id: User identifier
            endpoint: API endpoint path
            
        Returns:
            Dictionary with:
            - allowed: bool
            - remaining_tokens: int
            - retry_after: int (seconds)
            - burst_size: int
            - tokens_per_minute: int
        """
        # Get user bucket
        user_bucket = self._get_user_bucket(user_id)
        
        # Get endpoint-specific limit
        if endpoint:
            endpoint_limit = self._get_endpoint_limit(endpoint)
            # Use endpoint-specific bucket
            bucket_key = f"{user_id}:{endpoint}"
            
            if bucket_key not in self.user_buckets:
                self.user_buckets[bucket_key] = TokenBucket(
                    capacity=min(self.burst_size, endpoint_limit * 2),
                    refill_rate=endpoint_limit
                )
            
            user_bucket = self.user_buckets[bucket_key]
        
        # Check limit
        result = user_bucket.consume()
        
        # Add additional info
        result["burst_size"] = user_bucket.capacity
        result["tokens_per_minute"] = user_bucket.refill_rate
        
        if not result["allowed"]:
            logger.warning(
                f"Rate limit exceeded for user {user_id} "
                f"(endpoint: {endpoint or 'default'}), "
                f"retry after {result['retry_after']}s"
            )
        
        return result
    
    def consume_token(
        self,
        user_id: str,
        tokens: int = 1,
        endpoint: Optional[str] = None
    ) -> bool:
        """
        Consume tokens for a user
        
        Args:
            user_id: User identifier
            tokens: Number of tokens to consume
            endpoint: API endpoint path
            
        Returns:
            True if successful, False if rate limited
        """
        result = self.check_limit(user_id, endpoint)
        return result["allowed"]
    
    def get_user_status(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get rate limit status for user
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary with status information
        """
        # Get overall user bucket
        overall_bucket = self._get_user_bucket(user_id)
        
        # Get endpoint-specific buckets
        endpoint_status = {}
        
        for endpoint_pattern in self.endpoint_limits.keys():
            bucket_key = f"{user_id}:{endpoint_pattern}"
            if bucket_key in self.user_buckets:
                endpoint_bucket = self.user_buckets[bucket_key]
                endpoint_status[endpoint_pattern] = {
                    "remaining_tokens": endpoint_bucket.tokens,
                    "capacity": endpoint_bucket.capacity,
                    "refill_rate": endpoint_bucket.refill_rate
                }
        
        return {
            "user_id": user_id,
            "overall": {
                "remaining_tokens": overall_bucket.tokens,
                "capacity": overall_bucket.capacity,
                "refill_rate": overall_bucket.refill_rate
            },
            "endpoints": endpoint_status
        }
    
    def set_endpoint_limit(self, endpoint: str, tokens_per_minute: int):
        """
        Set rate limit for an endpoint
        
        Args:
            endpoint: API endpoint path
            tokens_per_minute: Tokens per minute
        """
        self.endpoint_limits[endpoint] = tokens_per_minute
        logger.info(f"Set endpoint limit: {endpoint} = {tokens_per_minute} tokens/min")
    
    def reset_user(self, user_id: str):
        """
        Reset rate limit for a user
        
        Args:
            user_id: User identifier
        """
        if user_id in self.user_buckets:
            del self.user_buckets[user_id]
            logger.info(f"Reset rate limit for user {user_id}")
    
    def cleanup_old_buckets(self, max_age: int = 3600):
        """
        Clean up old buckets to prevent memory leaks
        
        Args:
            max_age: Maximum age in seconds
        """
        now = time.time()
        to_remove = []
        
        for user_id, bucket in self.user_buckets.items():
            age = now - bucket.last_refill
            if age > max_age and bucket.tokens >= bucket.capacity:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.user_buckets[user_id]
        
        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old buckets")


# Global instance
rate_limiter = RateLimiter(tokens_per_minute=60, burst_size=10)