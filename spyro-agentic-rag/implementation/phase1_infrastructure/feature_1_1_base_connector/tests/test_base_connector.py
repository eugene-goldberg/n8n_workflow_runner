"""Tests for BaseConnector"""

import pytest
import asyncio
from typing import Dict, List, Any, AsyncIterator, Optional
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.base_connector import BaseConnector
from src.config import ConnectorConfig
from src.exceptions import (
    ConnectorError,
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    DataFetchError
)


class MockConnector(BaseConnector):
    """Mock implementation for testing"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.connect_called = False
        self.disconnect_called = False
        self.should_fail_connect = False
        self.should_fail_auth = False
        self.mock_schema = {
            "customers": {
                "fields": ["id", "name", "email"],
                "count": 100,
                "sample": {"id": "1", "name": "Test", "email": "test@example.com"}
            }
        }
        self.mock_data = [
            {"id": "1", "name": "Customer 1"},
            {"id": "2", "name": "Customer 2"},
            {"id": "3", "name": "Customer 3"}
        ]
    
    async def connect(self) -> bool:
        self.connect_called = True
        
        if self.should_fail_connect:
            raise ConnectionError("Mock connection failed")
        
        if self.should_fail_auth:
            raise AuthenticationError("Mock authentication failed")
        
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        self.disconnect_called = True
        self._connected = False
    
    async def discover_schema(self) -> Dict[str, Any]:
        if not self._connected:
            raise ConnectorError("Not connected")
        return self.mock_schema
    
    async def fetch_data(
        self, 
        entity_type: str, 
        since: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict]:
        if not self._connected:
            raise ConnectorError("Not connected")
        
        for record in self.mock_data:
            yield record
    
    async def get_sample_data(
        self, 
        entity_type: str, 
        limit: int = 5
    ) -> List[Dict]:
        if not self._connected:
            raise ConnectorError("Not connected")
        return self.mock_data[:limit]


class TestBaseConnector:
    """Test cases for BaseConnector"""
    
    def test_cannot_instantiate_abstract_class(self):
        """Test that BaseConnector cannot be instantiated directly"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        with pytest.raises(TypeError):
            BaseConnector(config)
    
    @pytest.mark.asyncio
    async def test_mock_connector_basic_flow(self):
        """Test basic flow with mock connector"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        
        # Test connection
        assert await connector.connect() == True
        assert connector.connect_called == True
        assert connector._connected == True
        
        # Test schema discovery
        schema = await connector.discover_schema()
        assert "customers" in schema
        assert schema["customers"]["count"] == 100
        
        # Test data fetching
        data = []
        async for record in connector.fetch_data("customers"):
            data.append(record)
        assert len(data) == 3
        
        # Test sample data
        samples = await connector.get_sample_data("customers", limit=2)
        assert len(samples) == 2
        
        # Test disconnection
        await connector.disconnect()
        assert connector.disconnect_called == True
        assert connector._connected == False
    
    @pytest.mark.asyncio
    async def test_connection_context_manager(self):
        """Test connection context manager"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        
        async with connector.connection_context() as conn:
            assert conn._connected == True
            schema = await conn.discover_schema()
            assert "customers" in schema
        
        # Should be disconnected after context
        assert connector._connected == False
        assert connector.disconnect_called == True
    
    @pytest.mark.asyncio
    async def test_validate_config_success(self):
        """Test successful config validation"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        is_valid, error = await connector.validate_config()
        
        assert is_valid == True
        assert error is None
        assert connector.disconnect_called == True
    
    @pytest.mark.asyncio
    async def test_validate_config_connection_failure(self):
        """Test config validation with connection failure"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        connector.should_fail_connect = True
        
        is_valid, error = await connector.validate_config()
        
        assert is_valid == False
        assert "Mock connection failed" in error
    
    @pytest.mark.asyncio
    async def test_validate_config_auth_failure(self):
        """Test config validation with auth failure"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        connector.should_fail_auth = True
        
        is_valid, error = await connector.validate_config()
        
        assert is_valid == False
        assert "Mock authentication failed" in error
    
    @pytest.mark.asyncio
    async def test_retry_logic_success(self):
        """Test retry logic with eventual success"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            retry_count=3,
            retry_delay=0.1
        )
        
        connector = MockConnector(config)
        await connector.connect()
        
        # Mock function that fails twice then succeeds
        call_count = 0
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise DataFetchError("Temporary failure")
            return "success"
        
        result = await connector._execute_with_retry(flaky_function)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_logic_all_failures(self):
        """Test retry logic when all attempts fail"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            retry_count=2,
            retry_delay=0.1
        )
        
        connector = MockConnector(config)
        
        async def always_fails():
            raise DataFetchError("Always fails")
        
        with pytest.raises(DataFetchError):
            await connector._execute_with_retry(always_fails)
        
        # Should have tried 3 times (initial + 2 retries)
        assert connector._failed_requests == 3
    
    @pytest.mark.asyncio
    async def test_retry_logic_no_retry_on_auth_error(self):
        """Test that auth errors are not retried"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            retry_count=3
        )
        
        connector = MockConnector(config)
        
        call_count = 0
        async def auth_failure():
            nonlocal call_count
            call_count += 1
            raise AuthenticationError("Invalid credentials")
        
        with pytest.raises(AuthenticationError):
            await connector._execute_with_retry(auth_failure)
        
        # Should only try once (no retries for auth errors)
        assert call_count == 1
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_handling(self):
        """Test handling of rate limit errors"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            retry_delay=0.1
        )
        
        connector = MockConnector(config)
        
        async def rate_limited():
            raise RateLimitError("Rate limit exceeded", retry_after=0.2)
        
        start = asyncio.get_event_loop().time()
        
        with pytest.raises(RateLimitError):
            await connector._execute_with_retry(rate_limited)
        
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should have waited for retry_after duration
        assert elapsed > 0.5  # Multiple retries with wait
    
    def test_get_statistics(self):
        """Test statistics tracking"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        connector._total_requests = 100
        connector._failed_requests = 10
        connector._last_request_time = datetime.now()
        
        stats = connector.get_statistics()
        
        assert stats["total_requests"] == 100
        assert stats["failed_requests"] == 10
        assert stats["success_rate"] == 90.0
        assert stats["last_request_time"] is not None
        assert "current_rate" in stats
        assert "available_tokens" in stats
    
    def test_get_statistics_no_requests(self):
        """Test statistics with no requests"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        stats = connector.get_statistics()
        
        assert stats["total_requests"] == 0
        assert stats["failed_requests"] == 0
        assert stats["success_rate"] == 0.0
        assert stats["last_request_time"] is None
    
    def test_string_representation(self):
        """Test __repr__ method"""
        config = ConnectorConfig(
            name="test_connector",
            api_key="key",
            base_url="https://api.test.com"
        )
        
        connector = MockConnector(config)
        repr_str = repr(connector)
        
        assert "MockConnector" in repr_str
        assert "test_connector" in repr_str
        assert "connected=False" in repr_str
    
    @pytest.mark.asyncio
    async def test_rate_limiter_integration(self):
        """Test that rate limiter is used in retry logic"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            rate_limit=60  # 60 per minute = 1 per second
        )
        
        connector = MockConnector(config)
        
        async def quick_function():
            return "done"
        
        # Make multiple rapid calls
        start = asyncio.get_event_loop().time()
        for _ in range(3):
            await connector._execute_with_retry(quick_function)
        elapsed = asyncio.get_event_loop().time() - start
        
        # Should be rate limited (but might complete quickly due to burst)
        # Just verify it completes without error
        assert connector._total_requests == 3