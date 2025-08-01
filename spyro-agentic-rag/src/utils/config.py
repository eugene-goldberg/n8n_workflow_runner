"""Configuration management for SpyroSolutions Agentic RAG"""

import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Configuration for the Agentic RAG system"""
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "password123")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # OpenAI Configuration
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # API Configuration
    api_key: str = os.getenv("SPYRO_API_KEY", "spyro-secret-key-123")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    
    # Agent Configuration
    agent_model: str = os.getenv("AGENT_MODEL", "gpt-4o")
    agent_temperature: float = float(os.getenv("AGENT_TEMPERATURE", "0"))
    agent_verbose: bool = os.getenv("AGENT_VERBOSE", "true").lower() == "true"
    agent_max_iterations: int = int(os.getenv("AGENT_MAX_ITERATIONS", "3"))
    
    # Retriever Configuration
    vector_index_name: str = os.getenv("VECTOR_INDEX_NAME", "spyro_vector_index")
    fulltext_index_name: str = os.getenv("FULLTEXT_INDEX_NAME", "spyro_fulltext_index")
    retriever_top_k: int = int(os.getenv("RETRIEVER_TOP_K", "5"))
    
    # Logging Configuration
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_format: str = os.getenv("LOG_FORMAT", "json")
    
    def validate(self) -> bool:
        """Validate required configuration"""
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD is required")
            
        return True
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables"""
        config = cls()
        config.validate()
        return config