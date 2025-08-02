"""Tests for RateLimiter"""

import pytest
import asyncio
import time
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.rate_limiter import RateLimiter, RateLimitConfig


class TestRateLimiter:
    """Test cases for RateLimiter"""
    
    @pytest.mark.asyncio
    async def test_basic_rate_limiting(self):
        """Test basic rate limiting functionality"""
        config = RateLimitConfig(requests_per_minute=60)
        limiter = RateLimiter(config)
        
        # Should allow immediate requests up to burst size
        start = time.time()
        for _ in range(6):  # Default burst size is 60/10 = 6
            await limiter.acquire()
        
        # Should complete quickly (under 100ms)
        assert time.time() - start < 0.1
    
    @pytest.mark.asyncio
    async def test_rate_limit_blocking(self):
        """Test that rate limiter blocks when limit exceeded"""
        config = RateLimitConfig(requests_per_minute=60, burst_size=2)
        limiter = RateLimiter(config)
        
        # Use up burst capacity
        await limiter.acquire()
        await limiter.acquire()
        
        # Next request should block
        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start
        
        # Should have waited approximately 1 second (60 requests/min = 1/sec)
        assert 0.8 < elapsed < 1.2
    
    @pytest.mark.asyncio
    async def test_token_refill(self):
        """Test that tokens refill over time"""
        config = RateLimitConfig(requests_per_minute=120, burst_size=2)
        limiter = RateLimiter(config)
        
        # Use all tokens
        await limiter.acquire(2)
        # Check tokens are approximately 0 (allowing for tiny refill during execution)
        assert limiter.get_available_tokens() < 0.1
        
        # Wait for refill
        await asyncio.sleep(1)  # 120/min = 2/sec, so should have 2 tokens
        
        # Check tokens were refilled
        tokens = limiter.get_available_tokens()
        assert 1.5 < tokens <= 2
    
    @pytest.mark.asyncio
    async def test_burst_size_configuration(self):
        """Test custom burst size configuration"""
        config = RateLimitConfig(requests_per_minute=100, burst_size=10)
        limiter = RateLimiter(config)
        
        # Should allow 10 immediate requests
        start = time.time()
        for _ in range(10):
            await limiter.acquire()
        
        assert time.time() - start < 0.1
        
        # 11th request should block
        start = time.time()
        await limiter.acquire()
        assert time.time() - start > 0.5
    
    @pytest.mark.asyncio
    async def test_multiple_token_acquisition(self):
        """Test acquiring multiple tokens at once"""
        config = RateLimitConfig(requests_per_minute=60, burst_size=5)
        limiter = RateLimiter(config)
        
        # Acquire 3 tokens at once
        await limiter.acquire(3)
        # Check approximately 2 tokens left (allowing for tiny refill)
        tokens_left = limiter.get_available_tokens()
        assert 1.9 < tokens_left < 2.1
        
        # Try to acquire more than available
        start = time.time()
        await limiter.acquire(3)
        elapsed = time.time() - start
        
        # Should have waited for refill
        assert elapsed > 0.5
    
    @pytest.mark.asyncio
    async def test_current_rate_calculation(self):
        """Test calculation of current request rate"""
        config = RateLimitConfig(requests_per_minute=60)
        limiter = RateLimiter(config)
        
        # Make some requests
        for _ in range(10):
            await limiter.acquire()
            await asyncio.sleep(0.1)
        
        # Check current rate
        current_rate = limiter.get_current_rate()
        # Should be approximately 10 requests in 1 second = 600/min
        # But we spread them over 1 second, so actual rate varies
        assert 0 < current_rate < 700
    
    @pytest.mark.asyncio
    async def test_wait_if_needed(self):
        """Test wait_if_needed functionality"""
        config = RateLimitConfig(requests_per_minute=60, burst_size=10)
        limiter = RateLimiter(config)
        
        # Use most tokens (leaving only 1, which is 10% < 20%)
        await limiter.acquire(9)
        
        # wait_if_needed should wait since we're below 20% capacity
        start = time.time()
        await limiter.wait_if_needed()
        elapsed = time.time() - start
        
        # Should have waited to refill to 50% capacity
        # 50% of 10 is 5, we had 1, need 4 more
        # At 1 token/sec, that's 4 seconds, but let's be conservative
        assert elapsed > 3.5
        assert limiter.get_available_tokens() > 4
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test rate limiter with concurrent requests"""
        config = RateLimitConfig(requests_per_minute=60, burst_size=5)
        limiter = RateLimiter(config)
        
        async def make_request(request_id: int):
            await limiter.acquire()
            return request_id
        
        # Launch 10 concurrent requests
        start = time.time()
        tasks = [make_request(i) for i in range(10)]
        results = await asyncio.gather(*tasks)
        elapsed = time.time() - start
        
        # Should complete all requests
        assert len(results) == 10
        assert all(i in results for i in range(10))
        
        # Should take at least 5 seconds (5 burst + 5 more at 1/sec)
        assert elapsed > 4.5
    
    @pytest.mark.asyncio
    async def test_sliding_window_cleanup(self):
        """Test that old request times are cleaned up"""
        config = RateLimitConfig(requests_per_minute=60)
        limiter = RateLimiter(config)
        
        # Make some requests
        for _ in range(5):
            await limiter.acquire()
        
        initial_count = len(limiter.request_times)
        assert initial_count == 5
        
        # Wait beyond window size
        # Note: window_size is 60 seconds, so we'll simulate this
        limiter.request_times[0] = time.time() - 61
        limiter.request_times[1] = time.time() - 61
        
        # Make another request to trigger cleanup
        await limiter.acquire()
        
        # Old times should be cleaned up
        assert len(limiter.request_times) == 4  # 3 old + 1 new
    
    def test_rate_limit_config_defaults(self):
        """Test RateLimitConfig default values"""
        config = RateLimitConfig(requests_per_minute=100)
        
        assert config.requests_per_minute == 100
        assert config.burst_size == 10  # Default: requests_per_minute // 10
    
    def test_rate_limit_config_custom_burst(self):
        """Test RateLimitConfig with custom burst size"""
        config = RateLimitConfig(requests_per_minute=100, burst_size=20)
        
        assert config.requests_per_minute == 100
        assert config.burst_size == 20