"""State schemas for the LangGraph workflow"""

from typing import List, Dict, Optional, Any, Annotated
from typing_extensions import TypedDict
from datetime import datetime
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field

from .routing import RetrievalStrategy


class AgentState(TypedDict):
    """State that flows through the LangGraph workflow"""
    # Core conversation state
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    
    # Routing and strategy
    strategy: Optional[RetrievalStrategy]
    query_analysis: Optional[Dict[str, Any]]
    
    # Retrieved context
    raw_context: List[Dict[str, Any]]
    ranked_context: List[Dict[str, Any]]
    
    # Quality and self-correction
    quality_score: float
    quality_reasoning: str
    retry_count: int
    rewritten_queries: List[str]
    
    # Error tracking
    error_log: List[str]
    failed_strategies: List[str]
    
    # Metadata
    start_time: datetime
    end_time: Optional[datetime]
    total_tokens_used: int


class QueryMetrics(BaseModel):
    """Metrics for a single query execution"""
    query_id: str = Field(description="Unique identifier for the query")
    query: str = Field(description="Original user query")
    strategy: RetrievalStrategy = Field(description="Selected retrieval strategy")
    tools_used: List[str] = Field(description="List of tools invoked")
    latency_ms: float = Field(description="Total query latency in milliseconds")
    
    # Quality metrics
    initial_quality_score: float = Field(description="Quality score before any rewrites")
    final_quality_score: float = Field(description="Final quality score after corrections")
    rewrite_count: int = Field(description="Number of query rewrites attempted")
    
    # Resource usage
    total_tokens: int = Field(description="Total LLM tokens consumed")
    vector_search_count: int = Field(default=0)
    graph_query_count: int = Field(default=0)
    
    # Success indicators
    succeeded: bool = Field(description="Whether the query was successfully answered")
    error_message: Optional[str] = Field(default=None)
    
    # Timestamps
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class GradingOutput(BaseModel):
    """Output schema for context grading"""
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Relevance score for the retrieved context"
    )
    reasoning: str = Field(
        description="Explanation of the grading decision"
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Key information that appears to be missing"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="Suggestions for improving the query"
    )


class RewrittenQueries(BaseModel):
    """Output schema for query rewriting"""
    original: str = Field(description="The original query that failed")
    alternatives: List[str] = Field(
        description="Alternative query formulations",
        min_items=1,
        max_items=3
    )
    strategy_suggestion: Optional[RetrievalStrategy] = Field(
        default=None,
        description="Suggested strategy for the rewritten queries"
    )