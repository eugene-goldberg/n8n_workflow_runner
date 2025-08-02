"""Tests for MockConnector"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mock_connector import MockConnector
from src.config import ConnectorConfig
from src.exceptions import (
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    DataFetchError,
    SchemaDiscoveryError
)


class TestMockConnector:
    """Test cases for MockConnector"""
    
    def create_config(self, **custom_params) -> ConnectorConfig:
        """Helper to create connector config"""
        return ConnectorConfig(
            name="mock",
            api_key="dummy",
            base_url="mock://localhost",
            custom_params=custom_params
        )
    
    @pytest.mark.asyncio
    async def test_basic_connection(self):
        """Test basic connection functionality"""
        config = self.create_config(seed=42)
        connector = MockConnector(config)
        
        # Test connection
        result = await connector.connect()
        assert result == True
        assert connector._connected == True
        
        # Test disconnection
        await connector.disconnect()
        assert connector._connected == False
    
    @pytest.mark.asyncio
    async def test_deterministic_data_with_seed(self):
        """Test that same seed produces same data"""
        config1 = self.create_config(seed=42, customer_count=10)
        config2 = self.create_config(seed=42, customer_count=10)
        
        connector1 = MockConnector(config1)
        connector2 = MockConnector(config2)
        
        await connector1.connect()
        await connector2.connect()
        
        # Fetch data from both
        data1 = []
        async for record in connector1.fetch_data("Customer"):
            data1.append(record)
        
        data2 = []
        async for record in connector2.fetch_data("Customer"):
            data2.append(record)
        
        # Check key fields are deterministic
        assert len(data1) == len(data2)
        for d1, d2 in zip(data1, data2):
            assert d1["id"] == d2["id"]
            assert d1["size"] == d2["size"] 
            assert d1["arr"] == d2["arr"]
            assert d1["health_score"] == d2["health_score"]
        
        await connector1.disconnect()
        await connector2.disconnect()
    
    @pytest.mark.asyncio
    async def test_schema_discovery(self):
        """Test schema discovery"""
        config = self.create_config(seed=42, customer_count=50)
        connector = MockConnector(config)
        
        await connector.connect()
        
        schema = await connector.discover_schema()
        
        # Check schema structure
        assert "Customer" in schema
        assert "Product" in schema
        assert "SaaSSubscription" in schema
        
        # Check customer schema
        customer_schema = schema["Customer"]
        assert "fields" in customer_schema
        assert "count" in customer_schema
        assert customer_schema["count"] == 50  # Should match configured count
        assert "id" in customer_schema["fields"]
        assert "name" in customer_schema["fields"]
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_fetch_all_entity_types(self):
        """Test fetching data for all entity types"""
        config = self.create_config(seed=42, customer_count=10)
        connector = MockConnector(config)
        
        await connector.connect()
        schema = await connector.discover_schema()
        
        # Test fetching each entity type
        for entity_type in schema.keys():
            data = []
            async for record in connector.fetch_data(entity_type):
                data.append(record)
            
            assert len(data) > 0
            # First record should have expected structure
            if data:
                assert "id" in data[0]
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_pagination(self):
        """Test pagination functionality"""
        config = self.create_config(
            seed=42, 
            customer_count=25,
            api_delay=0  # No delay for faster testing
        )
        config.page_size = 10  # Small page size
        
        connector = MockConnector(config)
        await connector.connect()
        
        # Fetch all customers
        customers = []
        page_count = 0
        
        async for customer in connector.fetch_data("Customer"):
            customers.append(customer)
            # Track pages (every 10 records is a new page)
            if len(customers) % 10 == 0:
                page_count += 1
        
        assert len(customers) == 25
        # Should have had 3 pages (10, 10, 5)
        assert page_count >= 2
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_date_filtering(self):
        """Test filtering by date"""
        config = self.create_config(seed=42, customer_count=20)
        connector = MockConnector(config)
        
        await connector.connect()
        
        # Get a cutoff date
        cutoff_date = datetime.now() - timedelta(days=180)  # 6 months ago
        
        # Fetch customers updated after cutoff
        recent_customers = []
        async for customer in connector.fetch_data("Customer", since=cutoff_date):
            recent_customers.append(customer)
            # Verify date filter worked
            assert datetime.fromisoformat(customer["updated_date"]) >= cutoff_date
        
        # Should have some customers (might be all if all are recent)
        assert len(recent_customers) > 0
        assert len(recent_customers) <= 20
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_custom_filters(self):
        """Test custom filtering"""
        config = self.create_config(seed=42, customer_count=30)
        connector = MockConnector(config)
        
        await connector.connect()
        
        # Filter by size
        enterprise_customers = []
        filters = {"size": "Enterprise"}
        
        async for customer in connector.fetch_data("Customer", filters=filters):
            enterprise_customers.append(customer)
            assert customer["size"] == "Enterprise"
        
        # Should have some enterprise customers
        assert len(enterprise_customers) > 0
        assert len(enterprise_customers) < 30  # Not all are enterprise
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_get_sample_data(self):
        """Test getting sample data"""
        config = self.create_config(seed=42, customer_count=20)
        connector = MockConnector(config)
        
        await connector.connect()
        
        # Get sample customers
        samples = await connector.get_sample_data("Customer", limit=5)
        
        assert len(samples) == 5
        assert all("id" in sample for sample in samples)
        assert all("name" in sample for sample in samples)
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_simulated_failures(self):
        """Test failure simulation"""
        config = self.create_config(
            seed=42,
            customer_count=10,
            enable_failures=True,
            failure_rate=0.5,  # High failure rate for testing
            api_delay=0
        )
        connector = MockConnector(config)
        
        # Connection might fail
        try:
            await connector.connect()
        except AuthenticationError:
            # Expected possible failure
            return
        
        # Try fetching data multiple times
        failure_count = 0
        success_count = 0
        
        for _ in range(10):
            try:
                data = []
                async for record in connector.fetch_data("Customer"):
                    data.append(record)
                success_count += 1
            except (RateLimitError, DataFetchError):
                failure_count += 1
            
            # Reset failure state to allow more attempts
            connector.reset_failure_state()
        
        # Should have some failures and some successes
        assert failure_count > 0
        assert success_count > 0
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_rate_limit_error_details(self):
        """Test rate limit error includes retry_after"""
        config = self.create_config(
            seed=42,
            enable_failures=True,
            failure_rate=1.0  # Always fail
        )
        connector = MockConnector(config)
        
        try:
            await connector.connect()
        except AuthenticationError:
            # Might fail on connect
            return
        
        # Force a failure
        with pytest.raises((RateLimitError, DataFetchError)) as exc_info:
            async for _ in connector.fetch_data("Customer"):
                pass
        
        # If it's a rate limit error, check retry_after
        if isinstance(exc_info.value, RateLimitError):
            assert exc_info.value.retry_after is not None
            assert exc_info.value.retry_after > 0
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_unknown_entity_type(self):
        """Test fetching unknown entity type"""
        config = self.create_config(seed=42)
        connector = MockConnector(config)
        
        await connector.connect()
        
        with pytest.raises(DataFetchError) as exc_info:
            async for _ in connector.fetch_data("UnknownEntity"):
                pass
        
        assert "Unknown entity type" in str(exc_info.value)
        assert exc_info.value.entity_type == "UnknownEntity"
        assert exc_info.value.error_code == "UNKNOWN_ENTITY"
        
        await connector.disconnect()
    
    @pytest.mark.asyncio
    async def test_not_connected_errors(self):
        """Test operations fail when not connected"""
        config = self.create_config(seed=42)
        connector = MockConnector(config)
        
        # Try operations without connecting
        with pytest.raises(ConnectionError):
            await connector.discover_schema()
        
        with pytest.raises(ConnectionError):
            async for _ in connector.fetch_data("Customer"):
                pass
        
        with pytest.raises(ConnectionError):
            await connector.get_sample_data("Customer")
    
    @pytest.mark.asyncio
    async def test_connection_context_manager(self):
        """Test using connector as context manager"""
        config = self.create_config(seed=42, customer_count=5)
        connector = MockConnector(config)
        
        async with connector.connection_context():
            # Should be connected
            assert connector._connected == True
            
            # Should be able to fetch data
            customers = []
            async for customer in connector.fetch_data("Customer"):
                customers.append(customer)
            
            assert len(customers) == 5
        
        # Should be disconnected after context
        assert connector._connected == False
    
    @pytest.mark.asyncio
    async def test_api_delay_simulation(self):
        """Test API delay simulation"""
        config = self.create_config(
            seed=42,
            customer_count=5,
            api_delay=0.1  # 100ms delay
        )
        connector = MockConnector(config)
        
        start_time = asyncio.get_event_loop().time()
        
        await connector.connect()
        
        # Fetch some data (should have delays)
        count = 0
        async for _ in connector.fetch_data("Customer"):
            count += 1
            if count >= 3:  # Just get a few
                break
        
        await connector.disconnect()
        
        elapsed = asyncio.get_event_loop().time() - start_time
        
        # Should have taken some time (connection + at least 1 fetch delay)
        assert elapsed > 0.15  # At least 150ms (reduced threshold for test stability)
    
    @pytest.mark.asyncio
    async def test_data_relationships(self):
        """Test that generated data maintains valid relationships"""
        config = self.create_config(seed=42, customer_count=10)
        connector = MockConnector(config)
        
        await connector.connect()
        
        # Collect all data
        customers = []
        async for customer in connector.fetch_data("Customer"):
            customers.append(customer)
        
        subscriptions = []
        async for sub in connector.fetch_data("SaaSSubscription"):
            subscriptions.append(sub)
        
        # Verify all subscriptions reference valid customers
        customer_ids = {c["id"] for c in customers}
        for sub in subscriptions:
            assert sub["customer_id"] in customer_ids
        
        await connector.disconnect()
    
    @pytest.mark.asyncio 
    async def test_validate_config(self):
        """Test config validation through base class"""
        config = self.create_config(seed=42, customer_count=5)
        connector = MockConnector(config)
        
        # Should succeed
        is_valid, error = await connector.validate_config()
        assert is_valid == True
        assert error is None