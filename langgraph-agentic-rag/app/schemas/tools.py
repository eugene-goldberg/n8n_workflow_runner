"""Tool input/output schemas"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class VectorSearchInput(BaseModel):
    """Input schema for vector similarity search"""
    query: str = Field(
        ...,
        description="The semantic query to be embedded and used for similarity search"
    )
    top_k: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Number of most similar documents to return"
    )
    filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Optional metadata filters to apply"
    )
    include_embeddings: bool = Field(
        default=False,
        description="Whether to include raw embeddings in results"
    )


class GraphSearchInput(BaseModel):
    """Input schema for knowledge graph search"""
    question: str = Field(
        ...,
        description="Natural language question to be converted to Cypher query"
    )
    entity_names: Optional[List[str]] = Field(
        default=None,
        description="Specific entities to focus on in the search"
    )
    relationship_types: Optional[List[str]] = Field(
        default=None,
        description="Specific relationship types to traverse"
    )
    max_hops: int = Field(
        default=2,
        ge=1,
        le=4,
        description="Maximum relationship hops to traverse"
    )


class HybridSearchInput(BaseModel):
    """Input schema for hybrid search strategies"""
    query: str = Field(
        ...,
        description="The user query to process"
    )
    mode: str = Field(
        default="parallel",
        description="Hybrid mode: 'sequential' or 'parallel'"
    )
    vector_weight: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Weight for vector results in fusion (parallel mode)"
    )
    rerank: bool = Field(
        default=True,
        description="Whether to apply cross-encoder reranking"
    )
    top_k: int = Field(
        default=10,
        description="Number of final results to return"
    )


class SearchResult(BaseModel):
    """Unified search result schema"""
    content: str = Field(description="The actual content/text")
    source: str = Field(description="Source identifier (doc ID, node ID, etc.)")
    score: float = Field(description="Relevance/similarity score")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    result_type: str = Field(
        description="Type of result: 'vector', 'graph', or 'hybrid'"
    )


class ToolResponse(BaseModel):
    """Standard response format for all tools"""
    results: List[SearchResult] = Field(
        description="List of search results"
    )
    query_executed: Optional[str] = Field(
        default=None,
        description="Actual query executed (e.g., Cypher for graph)"
    )
    execution_time_ms: float = Field(
        description="Time taken to execute the search"
    )
    total_found: int = Field(
        description="Total number of results found (before limiting)"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if the search failed"
    )