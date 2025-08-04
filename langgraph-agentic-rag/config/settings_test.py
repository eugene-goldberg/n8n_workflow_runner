"""Test settings with lower-tier model to avoid rate limits"""

import os
from pydantic_settings import BaseSettings
from pydantic import Field


class OpenAISettings(BaseSettings):
    """OpenAI configuration"""
    api_key: str = Field(default=os.getenv("OPENAI_API_KEY", ""))
    model: str = Field(default="gpt-3.5-turbo")  # Use 3.5 for testing to avoid rate limits
    temperature: float = Field(default=0.0)
    max_tokens: int = Field(default=2000)
    
    class Config:
        env_prefix = "OPENAI_"


class Neo4jSettings(BaseSettings):
    """Neo4j configuration"""
    uri: str = Field(default="bolt://localhost:7687")
    username: str = Field(default="neo4j")
    password: str = Field(default="password123")
    
    class Config:
        env_prefix = "NEO4J_"


class PostgresSettings(BaseSettings):
    """PostgreSQL configuration for pgvector and state persistence"""
    host: str = Field(default="localhost")
    port: int = Field(default=5432)
    database: str = Field(default="langgraph_rag")
    user: str = Field(default="postgres")
    password: str = Field(default="postgres")
    
    @property
    def pgvector_connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    class Config:
        env_prefix = "POSTGRES_"


class AppSettings(BaseSettings):
    """Application settings"""
    max_iterations: int = Field(default=10)
    debug: bool = Field(default=False)
    
    class Config:
        env_prefix = "APP_"


class Settings(BaseSettings):
    """Main settings aggregator"""
    openai: OpenAISettings = Field(default_factory=OpenAISettings)
    neo4j: Neo4jSettings = Field(default_factory=Neo4jSettings)
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    app: AppSettings = Field(default_factory=AppSettings)


# Global settings instance
settings = Settings()