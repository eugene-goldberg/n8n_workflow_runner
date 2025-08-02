"""Custom exceptions for the connector framework"""

from typing import Any, Optional


class ConnectorError(Exception):
    """Base exception for all connector-related errors"""
    pass


class ConnectionError(ConnectorError):
    """Raised when connection to data source fails"""
    pass


class AuthenticationError(ConnectorError):
    """Raised when authentication fails"""
    pass


class RateLimitError(ConnectorError):
    """Raised when rate limit is exceeded"""
    
    def __init__(self, message: str, retry_after: float = None):
        super().__init__(message)
        self.retry_after = retry_after


class DataFetchError(ConnectorError):
    """Raised when data fetching fails"""
    
    def __init__(self, message: str, entity_type: str = None, error_code: str = None):
        super().__init__(message)
        self.entity_type = entity_type
        self.error_code = error_code


class SchemaDiscoveryError(ConnectorError):
    """Raised when schema discovery fails"""
    pass


class ValidationError(ConnectorError):
    """Raised when data validation fails"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        super().__init__(message)
        self.field = field
        self.value = value