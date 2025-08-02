"""Base Connector Framework for SpyroSolutions Ingestion Pipeline"""

from .base_connector import BaseConnector, ConnectorConfig
from .exceptions import (
    ConnectorError,
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    DataFetchError
)
from .rate_limiter import RateLimiter, RateLimitConfig

__all__ = [
    "BaseConnector",
    "ConnectorConfig",
    "ConnectorError",
    "ConnectionError", 
    "AuthenticationError",
    "RateLimitError",
    "DataFetchError",
    "RateLimiter",
    "RateLimitConfig"
]