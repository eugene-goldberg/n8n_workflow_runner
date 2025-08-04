"""Configuration settings for the LangGraph Agentic RAG system."""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 2000


@dataclass
class PostgresConfig:
    """PostgreSQL database configuration."""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def pgvector_connection_string(self) -> str:
        """Get connection string for pgvector operations."""
        return f"{self.connection_string}?sslmode=disable"


@dataclass
class Neo4jConfig:
    """Neo4j database configuration."""
    uri: str
    username: str
    password: str


@dataclass
class LangSmithConfig:
    """LangSmith observability configuration."""
    api_key: Optional[str]
    project: str = "langgraph-agentic-rag"
    tracing_enabled: bool = True


@dataclass
class ApplicationConfig:
    """General application configuration."""
    log_level: str = "INFO"
    environment: str = "development"
    
    # Vector search settings
    vector_dimension: int = 1536  # OpenAI embeddings dimension
    vector_search_k: int = 10
    
    # Graph search settings
    max_graph_depth: int = 3
    max_graph_nodes: int = 50
    
    # Agent settings
    max_iterations: int = 10
    enable_human_in_loop: bool = True


class Settings:
    """Main settings class aggregating all configurations."""
    
    def __init__(self):
        self.openai = OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview"),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "2000"))
        )
        
        self.postgres = PostgresConfig(
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", "5432")),
            database=os.getenv("POSTGRES_DB", "agentic_rag"),
            user=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password")
        )
        
        self.neo4j = Neo4jConfig(
            uri=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
            username=os.getenv("NEO4J_USERNAME", "neo4j"),
            password=os.getenv("NEO4J_PASSWORD", "password")
        )
        
        self.langsmith = LangSmithConfig(
            api_key=os.getenv("LANGCHAIN_API_KEY"),
            project=os.getenv("LANGCHAIN_PROJECT", "langgraph-agentic-rag"),
            tracing_enabled=os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true"
        )
        
        self.app = ApplicationConfig(
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            environment=os.getenv("ENVIRONMENT", "development")
        )
    
    def validate(self) -> None:
        """Validate required settings."""
        if not self.openai.api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        if self.langsmith.tracing_enabled and not self.langsmith.api_key:
            raise ValueError("LANGCHAIN_API_KEY is required when tracing is enabled")


# Global settings instance
settings = Settings()