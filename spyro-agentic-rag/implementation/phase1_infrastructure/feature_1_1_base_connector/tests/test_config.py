"""Tests for ConnectorConfig"""

import pytest
from typing import Dict, Any

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import ConnectorConfig


class TestConnectorConfig:
    """Test cases for ConnectorConfig"""
    
    def test_valid_config_creation(self):
        """Test creating a valid configuration"""
        config = ConnectorConfig(
            name="test_connector",
            api_key="test_key",
            base_url="https://api.example.com"
        )
        
        assert config.name == "test_connector"
        assert config.api_key == "test_key"
        assert config.base_url == "https://api.example.com"
        assert config.rate_limit == 100  # default
        assert config.retry_count == 3  # default
        assert config.auth_type == "api_key"  # default
    
    def test_config_with_custom_values(self):
        """Test config with custom values"""
        config = ConnectorConfig(
            name="custom",
            api_key="key",
            base_url="https://api.test.com",
            rate_limit=50,
            retry_count=5,
            timeout=60.0,
            headers={"X-Custom": "value"},
            page_size=200
        )
        
        assert config.rate_limit == 50
        assert config.retry_count == 5
        assert config.timeout == 60.0
        assert config.headers == {"X-Custom": "value"}
        assert config.page_size == 200
    
    def test_oauth2_config(self):
        """Test OAuth2 configuration"""
        config = ConnectorConfig(
            name="oauth_connector",
            api_key="dummy",  # Still required by dataclass
            base_url="https://api.oauth.com",
            auth_type="oauth2",
            client_id="client123",
            client_secret="secret456",
            token_url="https://api.oauth.com/token"
        )
        
        assert config.auth_type == "oauth2"
        assert config.client_id == "client123"
        assert config.client_secret == "secret456"
        assert config.token_url == "https://api.oauth.com/token"
    
    def test_invalid_name(self):
        """Test that empty name raises ValueError"""
        with pytest.raises(ValueError, match="Connector name is required"):
            ConnectorConfig(
                name="",
                api_key="key",
                base_url="https://api.test.com"
            )
    
    def test_invalid_base_url(self):
        """Test that empty base_url raises ValueError"""
        with pytest.raises(ValueError, match="Base URL is required"):
            ConnectorConfig(
                name="test",
                api_key="key",
                base_url=""
            )
    
    def test_invalid_rate_limit(self):
        """Test that invalid rate limit raises ValueError"""
        with pytest.raises(ValueError, match="Rate limit must be positive"):
            ConnectorConfig(
                name="test",
                api_key="key",
                base_url="https://api.test.com",
                rate_limit=0
            )
    
    def test_invalid_retry_count(self):
        """Test that negative retry count raises ValueError"""
        with pytest.raises(ValueError, match="Retry count cannot be negative"):
            ConnectorConfig(
                name="test",
                api_key="key",
                base_url="https://api.test.com",
                retry_count=-1
            )
    
    def test_invalid_timeout(self):
        """Test that invalid timeout raises ValueError"""
        with pytest.raises(ValueError, match="Timeout must be positive"):
            ConnectorConfig(
                name="test",
                api_key="key",
                base_url="https://api.test.com",
                timeout=0
            )
    
    def test_incomplete_oauth2_config(self):
        """Test that incomplete OAuth2 config raises ValueError"""
        with pytest.raises(
            ValueError, 
            match="OAuth2 authentication requires client_id, client_secret, and token_url"
        ):
            ConnectorConfig(
                name="oauth",
                api_key="dummy",
                base_url="https://api.test.com",
                auth_type="oauth2",
                client_id="client123"
                # Missing client_secret and token_url
            )
    
    def test_to_dict(self):
        """Test converting config to dictionary"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            headers={"X-Test": "value"}
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["name"] == "test"
        assert config_dict["base_url"] == "https://api.test.com"
        assert config_dict["headers"] == {"X-Test": "value"}
        assert "api_key" not in config_dict  # Should not include sensitive data
    
    def test_from_dict(self):
        """Test creating config from dictionary"""
        data = {
            "name": "test",
            "api_key": "key",
            "base_url": "https://api.test.com",
            "rate_limit": 200,
            "headers": {"X-Custom": "header"}
        }
        
        config = ConnectorConfig.from_dict(data)
        
        assert config.name == "test"
        assert config.api_key == "key"
        assert config.base_url == "https://api.test.com"
        assert config.rate_limit == 200
        assert config.headers == {"X-Custom": "header"}
    
    def test_custom_params(self):
        """Test custom parameters storage"""
        config = ConnectorConfig(
            name="test",
            api_key="key",
            base_url="https://api.test.com",
            custom_params={
                "api_version": "v2",
                "region": "us-west",
                "custom_field": "value"
            }
        )
        
        assert config.custom_params["api_version"] == "v2"
        assert config.custom_params["region"] == "us-west"
        assert config.custom_params["custom_field"] == "value"