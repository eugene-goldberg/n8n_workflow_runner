# Feature 1.2: Mock Data Connector

## Overview
The Mock Data Connector implements the BaseConnector interface to provide realistic test data without requiring real API connections. This is essential for testing other components of the ingestion pipeline.

## Status
✅ **COMPLETE** - All tests passing with 96% coverage

## Specifications

### Size
Small (1-2 days)

### Dependencies
- Feature 1.1 (Base Connector Framework) ✅

### Description
Create a mock connector that generates realistic test data for various entity types (Customer, Subscription, Product, etc.) to test the ingestion pipeline without external dependencies.

## Implementation Checklist

### Core Components
- [x] Create `MockConnector` class extending `BaseConnector`
- [x] Implement all abstract methods
- [x] Generate realistic test data
- [x] Support pagination simulation
- [x] Support date filtering
- [x] Add configurable failure scenarios

### Data Generation
- [x] Customer entities with realistic attributes
- [x] SaaSSubscription with ARR/MRR data
- [x] Product catalog with features
- [x] Team and Project entities
- [x] Risk and Event entities
- [x] Relationships between entities

### Testing Features
- [x] Configurable data volume
- [x] Deterministic data generation (with seed)
- [x] Simulate API delays
- [x] Simulate failures (rate limit, network errors)
- [x] Data consistency across calls

## Acceptance Criteria
1. Implements all BaseConnector methods
2. Generates realistic, consistent test data
3. Supports all entity types in the SpyroSolutions model
4. Includes relationships between entities
5. Deterministic output with seed
6. Comprehensive test coverage

## Test Scenarios
1. Basic data fetching
2. Pagination handling
3. Date filtering
4. Schema discovery
5. Error simulation
6. Rate limit simulation
7. Large dataset handling

## Usage Example
```python
config = ConnectorConfig(
    name="mock",
    api_key="dummy",
    base_url="mock://localhost",
    custom_params={
        "seed": 42,
        "customer_count": 100,
        "enable_failures": True,
        "failure_rate": 0.1
    }
)

connector = MockConnector(config)
async with connector.connection_context():
    # Discover schema
    schema = await connector.discover_schema()
    
    # Fetch customers
    async for customer in connector.fetch_data("Customer"):
        print(customer)
```

## Test Results

### Coverage Report
```
Name                    Stmts   Miss  Cover   Missing
-----------------------------------------------------
src/mock_connector.py     136      5    96%   98, 206, 281-283
src/data_generator.py     104      1    99%   226
```

### Test Summary
- 30 tests passing
- All acceptance criteria met
- Deterministic data generation verified
- Error simulation working correctly
- Pagination and filtering tested