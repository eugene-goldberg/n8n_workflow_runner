# Base Connector Framework Design

## Overview

The Base Connector Framework provides a standardized interface for all data source connectors in the SpyroSolutions ingestion pipeline. It handles common concerns like authentication, rate limiting, retry logic, and error handling.

## Architecture

### Core Components

1. **BaseConnector (Abstract Class)**
   - Defines the interface all connectors must implement
   - Provides common functionality (retry logic, rate limiting, statistics)
   - Handles connection lifecycle management

2. **ConnectorConfig**
   - Configuration dataclass with validation
   - Supports multiple authentication types (API key, OAuth2, Basic)
   - Configurable rate limits, timeouts, and retry behavior

3. **RateLimiter**
   - Token bucket implementation for API rate limiting
   - Configurable requests per minute and burst size
   - Tracks request history for monitoring

4. **Exception Hierarchy**
   - `ConnectorError`: Base exception
   - Specific exceptions for different failure types
   - Rich error information for debugging

## Key Features

### Rate Limiting
- Token bucket algorithm with configurable burst
- Automatic blocking when rate limit approached
- Real-time rate monitoring

### Retry Logic
- Configurable retry count and delays
- Exponential backoff for transient failures
- No retry for authentication errors
- Special handling for rate limit errors

### Connection Management
- Connection lifecycle methods (connect/disconnect)
- Context manager support for automatic cleanup
- Connection validation before operations

### Error Handling
- Typed exceptions for different error scenarios
- Detailed error information (entity type, error codes)
- Graceful degradation on failures

## Usage Example

```python
class SalesforceConnector(BaseConnector):
    async def connect(self) -> bool:
        # Establish connection to Salesforce
        self._session = aiohttp.ClientSession()
        # Authenticate
        return True
    
    async def fetch_data(self, entity_type: str, since=None):
        # Use self._execute_with_retry for automatic retry/rate limiting
        async for page in self._fetch_pages(entity_type):
            for record in page:
                yield record

# Usage
config = ConnectorConfig(
    name="salesforce",
    api_key="xxx",
    base_url="https://instance.salesforce.com",
    rate_limit=100  # 100 requests/minute
)

connector = SalesforceConnector(config)
async with connector.connection_context():
    async for customer in connector.fetch_data("Customer"):
        process(customer)
```

## Implementation Status

✅ **Completed**
- Abstract base class with all required methods
- Configuration with validation
- Rate limiter with token bucket algorithm
- Comprehensive exception hierarchy
- Retry logic with exponential backoff
- Connection lifecycle management
- Statistics tracking
- 49 passing tests with 96% coverage

## Design Decisions

1. **Async-First**: All I/O operations are async for better performance
2. **Token Bucket**: More flexible than fixed-window rate limiting
3. **Abstract Base Class**: Enforces consistent interface across connectors
4. **Dataclass Config**: Type-safe configuration with validation
5. **Context Manager**: Ensures proper resource cleanup

## Performance Considerations

- Rate limiter uses minimal memory (deque for request history)
- Async operations allow concurrent data fetching
- Token refill calculation is O(1)
- Statistics tracking has negligible overhead

## Security Considerations

- API keys not included in to_dict() output
- SSL verification enabled by default
- OAuth2 support for secure authentication
- No credential logging

## Future Enhancements

1. Circuit breaker pattern for failing endpoints
2. Metrics export (Prometheus format)
3. Connection pooling support
4. Webhook support for real-time updates
5. Schema caching for performance