"""Routing schemas for query classification and strategy selection"""

from enum import Enum
from pydantic import BaseModel, Field


class RetrievalStrategy(str, Enum):
    """Enumeration of possible retrieval strategies"""
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID_SEQUENTIAL = "hybrid_sequential"
    HYBRID_PARALLEL = "hybrid_parallel"
    NO_RETRIEVAL = "no_retrieval"


class RouterOutput(BaseModel):
    """Output schema for the routing decision"""
    strategy: RetrievalStrategy = Field(
        ...,
        description="The selected retrieval strategy based on query analysis"
    )
    reasoning: str = Field(
        ...,
        description="Brief explanation of why this strategy was chosen"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score for the routing decision"
    )
    detected_entities: list[str] = Field(
        default_factory=list,
        description="Business entities detected in the query"
    )
    query_type: str = Field(
        default="unknown",
        description="Classified query type (e.g., factual, relational, conceptual)"
    )