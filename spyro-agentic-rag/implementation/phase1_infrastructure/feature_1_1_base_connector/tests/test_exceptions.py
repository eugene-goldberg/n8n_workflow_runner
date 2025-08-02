"""Tests for custom exceptions"""

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.exceptions import (
    ConnectorError,
    ConnectionError,
    AuthenticationError,
    RateLimitError,
    DataFetchError,
    SchemaDiscoveryError,
    ValidationError
)


class TestExceptions:
    """Test cases for custom exceptions"""
    
    def test_connector_error_base(self):
        """Test base ConnectorError"""
        error = ConnectorError("Base error message")
        assert str(error) == "Base error message"
        assert isinstance(error, Exception)
    
    def test_connection_error(self):
        """Test ConnectionError"""
        error = ConnectionError("Failed to connect")
        assert str(error) == "Failed to connect"
        assert isinstance(error, ConnectorError)
    
    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"
        assert isinstance(error, ConnectorError)
    
    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after"""
        error = RateLimitError("Rate limit exceeded", retry_after=60.5)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 60.5
        assert isinstance(error, ConnectorError)
    
    def test_rate_limit_error_without_retry_after(self):
        """Test RateLimitError without retry_after"""
        error = RateLimitError("Rate limit exceeded")
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after is None
    
    def test_data_fetch_error(self):
        """Test DataFetchError with additional attributes"""
        error = DataFetchError(
            "Failed to fetch data",
            entity_type="Customer",
            error_code="ERR_404"
        )
        assert str(error) == "Failed to fetch data"
        assert error.entity_type == "Customer"
        assert error.error_code == "ERR_404"
        assert isinstance(error, ConnectorError)
    
    def test_data_fetch_error_minimal(self):
        """Test DataFetchError with minimal args"""
        error = DataFetchError("Failed to fetch")
        assert str(error) == "Failed to fetch"
        assert error.entity_type is None
        assert error.error_code is None
    
    def test_schema_discovery_error(self):
        """Test SchemaDiscoveryError"""
        error = SchemaDiscoveryError("Failed to discover schema")
        assert str(error) == "Failed to discover schema"
        assert isinstance(error, ConnectorError)
    
    def test_validation_error(self):
        """Test ValidationError with field and value"""
        error = ValidationError(
            "Invalid value for field",
            field="email",
            value="not-an-email"
        )
        assert str(error) == "Invalid value for field"
        assert error.field == "email"
        assert error.value == "not-an-email"
        assert isinstance(error, ConnectorError)
    
    def test_validation_error_minimal(self):
        """Test ValidationError with minimal args"""
        error = ValidationError("Validation failed")
        assert str(error) == "Validation failed"
        assert error.field is None
        assert error.value is None
    
    def test_exception_inheritance(self):
        """Test that all exceptions inherit from ConnectorError"""
        exceptions = [
            ConnectionError("test"),
            AuthenticationError("test"),
            RateLimitError("test"),
            DataFetchError("test"),
            SchemaDiscoveryError("test"),
            ValidationError("test")
        ]
        
        for exc in exceptions:
            assert isinstance(exc, ConnectorError)
            assert isinstance(exc, Exception)
    
    def test_exception_catching(self):
        """Test catching exceptions at different levels"""
        # Can catch specific exception
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Auth failed")
        
        # Can catch base ConnectorError
        with pytest.raises(ConnectorError):
            raise AuthenticationError("Auth failed")
        
        # Can catch generic Exception
        with pytest.raises(Exception):
            raise AuthenticationError("Auth failed")