"""Rate limiting functionality for connectors"""

import asyncio
import time
from dataclasses import dataclass
from typing import Optional
from collections import deque


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    
    requests_per_minute: int
    burst_size: Optional[int] = None
    
    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.requests_per_minute // 10


class RateLimiter:
    """Token bucket rate limiter for API calls"""
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        self.max_tokens = config.burst_size
        self.tokens = self.max_tokens
        self.refill_rate = config.requests_per_minute / 60.0  # tokens per second
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
        
        # Track request times for sliding window
        self.request_times = deque()
        self.window_size = 60  # seconds
    
    async def acquire(self, tokens: int = 1) -> None:
        """Acquire tokens, blocking if necessary"""
        async with self._lock:
            await self._refill()
            
            while self.tokens < tokens:
                # Calculate wait time
                deficit = tokens - self.tokens
                wait_time = deficit / self.refill_rate
                
                # Wait and refill
                await asyncio.sleep(wait_time)
                await self._refill()
            
            # Consume tokens
            self.tokens -= tokens
            
            # Track request time
            current_time = time.time()
            self.request_times.append(current_time)
            
            # Clean old request times
            cutoff_time = current_time - self.window_size
            while self.request_times and self.request_times[0] < cutoff_time:
                self.request_times.popleft()
    
    async def _refill(self) -> None:
        """Refill tokens based on elapsed time"""
        current_time = time.time()
        elapsed = current_time - self.last_refill
        
        # Calculate new tokens
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.tokens + new_tokens, self.max_tokens)
        
        # Update last refill time
        self.last_refill = current_time
    
    def get_current_rate(self) -> float:
        """Get current request rate (requests per minute)"""
        current_time = time.time()
        cutoff_time = current_time - self.window_size
        
        # Count recent requests
        recent_requests = sum(1 for t in self.request_times if t >= cutoff_time)
        
        # Calculate rate per minute
        return (recent_requests / self.window_size) * 60
    
    def get_available_tokens(self) -> float:
        """Get current available tokens"""
        # Refill before returning count
        current_time = time.time()
        elapsed = current_time - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.tokens + new_tokens, self.max_tokens)
        self.last_refill = current_time
        return self.tokens
    
    async def wait_if_needed(self) -> None:
        """Wait if we're approaching rate limit"""
        async with self._lock:
            await self._refill()
            
            # If we're below 20% capacity, wait a bit
            if self.tokens < self.max_tokens * 0.2:
                wait_time = (self.max_tokens * 0.5) / self.refill_rate
                await asyncio.sleep(wait_time)
                await self._refill()