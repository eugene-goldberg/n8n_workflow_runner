# Feature 1.1: Base Connector Framework

## Overview
The Base Connector Framework provides the foundation for all data source connectors in the ingestion pipeline. It defines the abstract interface that all specific connectors must implement.

## Status
✅ **Complete**

### Summary
- All core components implemented
- 49 tests passing with 96% code coverage
- Ready for use by other features

## Specifications

### Size
Small (2-3 days)

### Dependencies
None

### Description
Create an abstract base class that defines the interface for all data source connectors. This includes methods for connection management, schema discovery, data fetching, and error handling.

## Implementation Checklist

### Core Components
- [ ] Create `BaseConnector` abstract class
- [ ] Define `ConnectorConfig` dataclass
- [ ] Implement connection lifecycle methods
- [ ] Add rate limiting interface
- [ ] Add retry logic interface
- [ ] Create error handling framework

### Key Methods
- [ ] `connect()` - Establish connection and verify credentials
- [ ] `disconnect()` - Clean up resources
- [ ] `discover_schema()` - Auto-discover available data and schema
- [ ] `fetch_data()` - Fetch data with pagination support
- [ ] `get_sample_data()` - Get sample records for testing
- [ ] `validate_config()` - Validate connector configuration

### Testing
- [ ] Unit tests for config validation
- [ ] Tests for abstract interface enforcement
- [ ] Mock implementation for testing
- [ ] Error scenario tests
- [ ] Rate limiting tests

## Acceptance Criteria
1. Base abstract class properly defined
2. Config dataclass with validation
3. Rate limiting interface defined
4. Error handling interface defined
5. All unit tests passing
6. Documentation complete

## Code Structure
```
feature_1_1_base_connector/
├── src/
│   ├── __init__.py
│   ├── base_connector.py
│   ├── config.py
│   ├── exceptions.py
│   └── rate_limiter.py
├── tests/
│   ├── __init__.py
│   ├── test_base_connector.py
│   ├── test_config.py
│   └── test_rate_limiter.py
├── docs/
│   └── design.md
└── README.md
```

## Usage Example
```python
from src.connectors.base_connector import BaseConnector, ConnectorConfig

class SalesforceConnector(BaseConnector):
    async def connect(self) -> bool:
        # Implementation
        pass
    
    async def discover_schema(self) -> Dict[str, Any]:
        # Implementation
        pass
    
    async def fetch_data(self, entity_type: str, 
                        since: datetime = None) -> AsyncIterator[Dict]:
        # Implementation
        pass
```

## Test Plan

### Unit Tests
1. Test that BaseConnector cannot be instantiated directly
2. Test ConnectorConfig validation rules
3. Test rate limiter functionality
4. Test retry logic configuration
5. Test error handling patterns

### Integration Tests
1. Test with mock implementation
2. Test connection lifecycle
3. Test data fetching with pagination
4. Test error recovery

## Notes
- This is the foundation for all connectors, so design carefully
- Consider future requirements for different auth types
- Make rate limiting flexible for different API limits
- Ensure good error messages for debugging

## Next Steps
After completing this feature:
1. Implement Feature 1.2 (Mock Connector) to test the base framework
2. Use the mock connector for testing other components
3. Begin implementing real connectors (Salesforce, etc.)