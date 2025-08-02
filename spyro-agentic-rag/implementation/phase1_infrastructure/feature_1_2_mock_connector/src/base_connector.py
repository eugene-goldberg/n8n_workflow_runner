"""Base connector abstract class for all data source connectors"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncIterator, Optional, Tuple
from datetime import datetime
from contextlib import asynccontextmanager

from .config import ConnectorConfig
from .rate_limiter import RateLimiter, RateLimitConfig
from .exceptions import (
    ConnectorError,
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    DataFetchError
)


logger = logging.getLogger(__name__)


class BaseConnector(ABC):
    """Abstract base class for all data source connectors"""
    
    def __init__(self, config: ConnectorConfig):
        """Initialize connector with configuration
        
        Args:
            config: Connector configuration object
        """
        self.config = config
        self._session = None
        self._connected = False
        self._rate_limiter = RateLimiter(
            RateLimitConfig(requests_per_minute=config.rate_limit)
        )
        
        # Retry configuration
        self._retry_count = config.retry_count
        self._retry_delay = config.retry_delay
        
        # Statistics
        self._total_requests = 0
        self._failed_requests = 0
        self._last_request_time = None
    
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection and verify credentials
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ConnectionError: If connection fails
            AuthenticationError: If authentication fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Clean up resources and close connection"""
        pass
    
    @abstractmethod
    async def discover_schema(self) -> Dict[str, Any]:
        """Auto-discover available data and schema
        
        Returns:
            Dict containing schema information:
            {
                "entity_type": {
                    "fields": ["field1", "field2", ...],
                    "count": estimated_count,
                    "sample": sample_record
                }
            }
            
        Raises:
            SchemaDiscoveryError: If schema discovery fails
        """
        pass
    
    @abstractmethod
    async def fetch_data(
        self, 
        entity_type: str, 
        since: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict]:
        """Fetch data with pagination support
        
        Args:
            entity_type: Type of entity to fetch
            since: Only fetch records updated after this time
            filters: Additional filters to apply
            
        Yields:
            Dict: Individual records
            
        Raises:
            DataFetchError: If data fetching fails
        """
        pass
    
    @abstractmethod
    async def get_sample_data(
        self, 
        entity_type: str, 
        limit: int = 5
    ) -> List[Dict]:
        """Get sample records for testing
        
        Args:
            entity_type: Type of entity to sample
            limit: Maximum number of records to return
            
        Returns:
            List of sample records
            
        Raises:
            DataFetchError: If sampling fails
        """
        pass
    
    async def validate_config(self) -> Tuple[bool, Optional[str]]:
        """Validate connector configuration
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Test connection
            connected = await self.connect()
            if not connected:
                return False, "Failed to establish connection"
            
            # Test schema discovery
            schema = await self.discover_schema()
            if not schema:
                return False, "No schema discovered"
            
            # Test data fetch
            for entity_type in list(schema.keys())[:1]:  # Test first entity type
                sample = await self.get_sample_data(entity_type, limit=1)
                if not sample:
                    logger.warning(f"No sample data for {entity_type}")
            
            return True, None
            
        except Exception as e:
            return False, str(e)
        finally:
            await self.disconnect()
    
    @asynccontextmanager
    async def connection_context(self):
        """Context manager for connection lifecycle"""
        try:
            await self.connect()
            yield self
        finally:
            await self.disconnect()
    
    async def _execute_with_retry(
        self, 
        func, 
        *args, 
        **kwargs
    ) -> Any:
        """Execute function with retry logic
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(self._retry_count + 1):
            try:
                # Apply rate limiting
                await self._rate_limiter.acquire()
                
                # Execute function
                result = await func(*args, **kwargs)
                
                # Update statistics
                self._total_requests += 1
                self._last_request_time = datetime.now()
                
                return result
                
            except RateLimitError as e:
                # Handle rate limit specifically
                logger.warning(f"Rate limit hit: {e}")
                if e.retry_after:
                    await asyncio.sleep(e.retry_after)
                else:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                last_exception = e
                
            except Exception as e:
                # Log error
                logger.error(
                    f"Request failed (attempt {attempt + 1}/{self._retry_count + 1}): {e}"
                )
                
                # Update statistics
                self._failed_requests += 1
                
                # Don't retry on certain errors
                if isinstance(e, (AuthenticationError, ValueError)):
                    raise
                
                # Wait before retry
                if attempt < self._retry_count:
                    await asyncio.sleep(self._retry_delay * (attempt + 1))
                
                last_exception = e
        
        # All retries failed
        raise last_exception or ConnectorError("All retry attempts failed")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get connector statistics
        
        Returns:
            Dictionary with statistics
        """
        success_rate = 0.0
        if self._total_requests > 0:
            success_rate = (
                (self._total_requests - self._failed_requests) / 
                self._total_requests
            ) * 100
        
        return {
            "total_requests": self._total_requests,
            "failed_requests": self._failed_requests,
            "success_rate": success_rate,
            "last_request_time": self._last_request_time,
            "current_rate": self._rate_limiter.get_current_rate(),
            "available_tokens": self._rate_limiter.get_available_tokens()
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"{self.__class__.__name__}("
            f"name='{self.config.name}', "
            f"connected={self._connected})"
        )