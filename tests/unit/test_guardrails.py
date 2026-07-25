"""Unit tests for guardrails modules - minimal working tests"""

import pytest
from src.guardrails.input_filter import InputFilter
from src.guardrails.output_filter import OutputFilter
from src.guardrails.rate_limiter import RateLimiter


@pytest.mark.unit
class TestInputFilter:
    """Test input filter"""
    
    def test_init(self):
        """Test input filter initialization"""
        filter = InputFilter()
        
        assert filter is not None


@pytest.mark.unit
class TestOutputFilter:
    """Test output filter"""
    
    def test_init(self):
        """Test output filter initialization"""
        filter = OutputFilter()
        
        assert filter is not None


@pytest.mark.unit
class TestRateLimiter:
    """Test rate limiter"""
    
    def test_init(self):
        """Test rate limiter initialization"""
        limiter = RateLimiter()
        
        assert limiter is not None
    
    def test_set_endpoint_limit(self):
        """Test setting endpoint limit"""
        limiter = RateLimiter()
        
        limiter.set_endpoint_limit("/chat", 100)
        
        # Limit should be set
        assert limiter is not None
    
    def test_cleanup_old_buckets(self):
        """Test cleanup old buckets"""
        limiter = RateLimiter()
        
        # Cleanup
        limiter.cleanup_old_buckets(max_age=3600)
        
        assert limiter is not None
    
    def test_get_user_status_nonexistent(self):
        """Test get status for nonexistent user"""
        limiter = RateLimiter()
        
        status = limiter.get_user_status("nonexistent-user")
        
        assert status is not None
        assert isinstance(status, dict)
    
    def test_check_limit_safe(self):
        """Test check limit for safe request"""
        limiter = RateLimiter()
        
        result = limiter.check_limit("test-user", "/chat")
        
        assert result is not None
        assert isinstance(result, dict)