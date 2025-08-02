"""Configuration classes for connectors"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import timedelta


@dataclass
class ConnectorConfig:
    """Configuration for a data source connector"""
    
    name: str
    api_key: str
    base_url: str
    rate_limit: int = 100  # requests per minute
    retry_count: int = 3
    retry_delay: float = 1.0  # seconds
    timeout: float = 30.0  # seconds
    headers: Dict[str, str] = field(default_factory=dict)
    auth_type: str = "api_key"  # api_key, oauth2, basic
    
    # Optional OAuth2 fields
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    token_url: Optional[str] = None
    
    # Pagination settings
    page_size: int = 100
    max_pages: Optional[int] = None
    
    # Additional settings
    verify_ssl: bool = True
    custom_params: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate configuration after initialization"""
        if not self.name:
            raise ValueError("Connector name is required")
        
        if not self.base_url:
            raise ValueError("Base URL is required")
        
        if self.rate_limit <= 0:
            raise ValueError("Rate limit must be positive")
        
        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")
        
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")
        
        # Validate OAuth2 config if using OAuth2
        if self.auth_type == "oauth2":
            if not all([self.client_id, self.client_secret, self.token_url]):
                raise ValueError(
                    "OAuth2 authentication requires client_id, client_secret, and token_url"
                )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            "name": self.name,
            "base_url": self.base_url,
            "rate_limit": self.rate_limit,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "headers": self.headers,
            "auth_type": self.auth_type,
            "page_size": self.page_size,
            "max_pages": self.max_pages,
            "verify_ssl": self.verify_ssl,
            "custom_params": self.custom_params
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConnectorConfig":
        """Create config from dictionary"""
        return cls(**data)