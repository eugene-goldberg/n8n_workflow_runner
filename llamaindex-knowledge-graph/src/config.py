"""Configuration management for the knowledge graph pipeline"""

import os
from dataclasses import dataclass
from typing import Optional, Dict, List, Literal, Union
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class Config:
    """Configuration for the knowledge graph pipeline"""
    
    # API Keys
    llama_cloud_api_key: str = os.getenv("LLAMA_CLOUD_API_KEY", "")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    
    # Neo4j Configuration
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_username: str = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")
    neo4j_database: str = os.getenv("NEO4J_DATABASE", "neo4j")
    
    # LLM Configuration
    llm_model: str = os.getenv("LLM_MODEL", "gpt-4o")
    llm_temperature: float = float(os.getenv("LLM_TEMPERATURE", "0"))
    
    # Parser Configuration
    parser_result_type: str = "markdown"
    parser_verbose: bool = True
    parser_num_workers: int = 8
    
    # Extraction Configuration
    extraction_strict: bool = True
    extraction_show_progress: bool = True
    
    def validate(self) -> None:
        """Validate required configuration"""
        if not self.llama_cloud_api_key:
            raise ValueError("LLAMA_CLOUD_API_KEY is required")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required")
        if not self.neo4j_password:
            raise ValueError("NEO4J_PASSWORD is required")


@dataclass
class GraphSchema:
    """Define the knowledge graph schema"""
    
    # Entity types for corporate/financial documents
    entities: Union[List[str], type] = None
    
    # Relationship types
    relations: Union[List[str], type] = None
    
    # Validation schema
    validation_schema: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.entities is None:
            self.entities = [
                "PERSON", "COMPANY", "PRODUCT", "FINANCIAL_METRIC",
                "DEPARTMENT", "PROJECT", "TECHNOLOGY", "LOCATION",
                "DATE", "EVENT", "RISK", "OPPORTUNITY"
            ]
        
        if self.relations is None:
            self.relations = [
                "WORKS_FOR", "MANAGES", "REPORTS_TO", "OWNS",
                "INVESTS_IN", "PARTNERS_WITH", "COMPETES_WITH",
                "PRODUCES", "USES", "LOCATED_IN", "OCCURRED_ON",
                "IMPACTS", "DEPENDS_ON", "RELATES_TO"
            ]
        
        if self.validation_schema is None:
            self.validation_schema = {
                "PERSON": ["WORKS_FOR", "MANAGES", "REPORTS_TO"],
                "COMPANY": ["OWNS", "INVESTS_IN", "PARTNERS_WITH", "COMPETES_WITH", "PRODUCES", "LOCATED_IN"],
                "PRODUCT": ["PRODUCED_BY", "USES", "COMPETES_WITH"],
                "FINANCIAL_METRIC": ["RELATES_TO", "IMPACTS"],
                "DEPARTMENT": ["PART_OF", "MANAGES", "LOCATED_IN"],
                "PROJECT": ["MANAGED_BY", "USES", "DEPENDS_ON"],
                "TECHNOLOGY": ["USED_BY", "DEVELOPED_BY"],
                "LOCATION": ["CONTAINS"],
                "DATE": ["OCCURRED_ON"],
                "EVENT": ["OCCURRED_ON", "IMPACTS", "RELATES_TO"],
                "RISK": ["IMPACTS", "MANAGED_BY"],
                "OPPORTUNITY": ["RELATES_TO", "MANAGED_BY"]
            }