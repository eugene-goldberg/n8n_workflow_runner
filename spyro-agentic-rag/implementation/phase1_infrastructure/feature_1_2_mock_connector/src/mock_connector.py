"""Mock connector implementation for testing"""

import asyncio
import random
from typing import Dict, List, Any, AsyncIterator, Optional
from datetime import datetime, timedelta
import logging

from .base_connector import BaseConnector
from .config import ConnectorConfig
from .exceptions import (
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    DataFetchError,
    SchemaDiscoveryError
)
from .data_generator import DataGenerator


logger = logging.getLogger(__name__)


class MockConnector(BaseConnector):
    """Mock connector for testing the ingestion pipeline"""
    
    def __init__(self, config: ConnectorConfig):
        """Initialize mock connector
        
        Args:
            config: Connector configuration
                custom_params can include:
                - seed: Random seed for deterministic data
                - customer_count: Number of customers to generate
                - enable_failures: Enable random failures
                - failure_rate: Rate of random failures (0.0-1.0)
                - api_delay: Simulated API delay in seconds
        """
        super().__init__(config)
        
        # Extract custom parameters
        params = config.custom_params or {}
        self.seed = params.get("seed")
        self.customer_count = params.get("customer_count", 100)
        self.enable_failures = params.get("enable_failures", False)
        self.failure_rate = params.get("failure_rate", 0.1)
        self.api_delay = params.get("api_delay", 0.1)
        
        # Initialize data generator
        self.generator = DataGenerator(seed=self.seed)
        
        # Pre-generated data cache
        self._data_cache = {}
        self._schema = None
        
        # Pagination settings
        self.page_size = config.page_size
        
        # Track state for failure simulation
        self._request_count = 0
        self._last_failure_time = None
    
    async def connect(self) -> bool:
        """Simulate connection establishment"""
        logger.info(f"Connecting to mock data source with seed={self.seed}")
        
        # Simulate connection delay
        await asyncio.sleep(self.api_delay)
        
        # Simulate authentication failure if configured
        if self.enable_failures and random.random() < self.failure_rate:
            raise AuthenticationError("Mock authentication failed (simulated)")
        
        # Pre-generate all data on connection
        await self._generate_all_data()
        
        self._connected = True
        logger.info(f"Successfully connected to mock data source")
        return True
    
    async def disconnect(self) -> None:
        """Clean up mock connection"""
        logger.info("Disconnecting from mock data source")
        self._connected = False
        self._data_cache.clear()
        self._schema = None
    
    async def discover_schema(self) -> Dict[str, Any]:
        """Return schema for all entity types"""
        if not self._connected:
            raise ConnectionError("Not connected to mock data source")
        
        # Simulate API delay
        await asyncio.sleep(self.api_delay)
        
        # Simulate random failure
        if await self._should_fail():
            raise SchemaDiscoveryError("Schema discovery failed (simulated)")
        
        if self._schema is None:
            self._schema = self.generator.get_schema()
            
            # Update counts based on actual generated data
            for entity_type in self._schema:
                if entity_type in self._data_cache:
                    self._schema[entity_type]["count"] = len(self._data_cache[entity_type])
        
        return self._schema
    
    async def fetch_data(
        self, 
        entity_type: str, 
        since: Optional[datetime] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[Dict]:
        """Fetch mock data with pagination support"""
        if not self._connected:
            raise ConnectionError("Not connected to mock data source")
        
        # Check if entity type exists
        if entity_type not in self._data_cache:
            raise DataFetchError(
                f"Unknown entity type: {entity_type}",
                entity_type=entity_type,
                error_code="UNKNOWN_ENTITY"
            )
        
        # Get all data for entity type
        all_data = self._data_cache[entity_type]
        
        # Apply date filtering if specified
        if since:
            filtered_data = []
            since_str = since.isoformat()
            
            for record in all_data:
                # Check various date fields
                date_fields = ["updated_date", "created_date", "date", "identified_date"]
                record_date = None
                
                for field in date_fields:
                    if field in record:
                        record_date = record[field]
                        break
                
                if record_date and record_date >= since_str:
                    filtered_data.append(record)
            
            all_data = filtered_data
        
        # Apply additional filters
        if filters:
            filtered_data = []
            for record in all_data:
                match = True
                for key, value in filters.items():
                    if key not in record or record[key] != value:
                        match = False
                        break
                if match:
                    filtered_data.append(record)
            all_data = filtered_data
        
        # Simulate pagination
        total_records = len(all_data)
        pages = (total_records + self.page_size - 1) // self.page_size
        
        for page in range(pages):
            # Simulate API delay
            await asyncio.sleep(self.api_delay)
            
            # Simulate random failure
            if await self._should_fail():
                if random.random() < 0.5:
                    raise RateLimitError(
                        "Rate limit exceeded (simulated)",
                        retry_after=random.uniform(1, 5)
                    )
                else:
                    raise DataFetchError(
                        "Data fetch failed (simulated)",
                        entity_type=entity_type,
                        error_code="FETCH_ERROR"
                    )
            
            # Get page of data
            start_idx = page * self.page_size
            end_idx = min(start_idx + self.page_size, total_records)
            
            for record in all_data[start_idx:end_idx]:
                yield record
    
    async def get_sample_data(
        self, 
        entity_type: str, 
        limit: int = 5
    ) -> List[Dict]:
        """Get sample records for testing"""
        if not self._connected:
            raise ConnectionError("Not connected to mock data source")
        
        # Simulate API delay
        await asyncio.sleep(self.api_delay)
        
        if entity_type not in self._data_cache:
            raise DataFetchError(
                f"Unknown entity type: {entity_type}",
                entity_type=entity_type
            )
        
        data = self._data_cache[entity_type]
        return data[:limit]
    
    async def _generate_all_data(self) -> None:
        """Pre-generate all mock data"""
        logger.info("Generating mock data...")
        
        # Generate in dependency order
        
        # 1. Generate products (no dependencies)
        self.generator._reset_random_state("Product")
        self._data_cache["Product"] = [
            self.generator.generate_product(i) for i in range(3)
        ]
        
        # 2. Generate customers (no dependencies)
        self.generator._reset_random_state("Customer")
        self._data_cache["Customer"] = [
            self.generator.generate_customer(i) for i in range(self.customer_count)
        ]
        
        # 3. Generate teams (depends on products)
        self.generator._reset_random_state("Team")
        self._data_cache["Team"] = [
            self.generator.generate_team(i) for i in range(8)
        ]
        
        # 4. Generate subscriptions (depends on customers and products)
        self.generator._reset_random_state("SaaSSubscription")
        subscription_count = int(self.customer_count * 1.5)  # Some customers have multiple
        self._data_cache["SaaSSubscription"] = [
            self.generator.generate_subscription(i) for i in range(subscription_count)
        ]
        
        # 5. Generate projects (depends on teams)
        self.generator._reset_random_state("Project")
        self._data_cache["Project"] = [
            self.generator.generate_project(i) for i in range(20)
        ]
        
        # 6. Generate risks (depends on customers and teams)
        self.generator._reset_random_state("Risk")
        self._data_cache["Risk"] = [
            self.generator.generate_risk(i) for i in range(30)
        ]
        
        # 7. Generate events (depends on customers and teams)
        self.generator._reset_random_state("Event")
        self._data_cache["Event"] = [
            self.generator.generate_event(i) for i in range(50)
        ]
        
        # 8. Generate customer success scores (one per customer)
        self.generator._reset_random_state("CustomerSuccessScore")
        self._data_cache["CustomerSuccessScore"] = [
            self.generator.generate_customer_success_score(customer["id"])
            for customer in self._data_cache["Customer"]
        ]
        
        logger.info(f"Generated mock data: {', '.join(f'{k}={len(v)}' for k, v in self._data_cache.items())}")
    
    async def _should_fail(self) -> bool:
        """Determine if request should fail based on configuration"""
        if not self.enable_failures:
            return False
        
        self._request_count += 1
        
        # Don't fail too frequently
        if self._last_failure_time:
            time_since_failure = datetime.now() - self._last_failure_time
            if time_since_failure < timedelta(seconds=5):
                return False
        
        # Random failure based on rate
        if random.random() < self.failure_rate:
            self._last_failure_time = datetime.now()
            return True
        
        return False
    
    def reset_failure_state(self) -> None:
        """Reset failure simulation state (useful for testing)"""
        self._request_count = 0
        self._last_failure_time = None