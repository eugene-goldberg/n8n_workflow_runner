"""State types for the agentic RAG system."""

from typing import TypedDict, List, Dict, Any, Optional, Annotated, Literal
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage


class RouterDecision(TypedDict):
    """Router decision output."""
    route: Literal["simple_greeting", "fact_lookup", "relational_query", "hybrid_search", "ambiguous"]
    reasoning: str


class RetrievalResult(TypedDict):
    """Result from a retrieval operation."""
    content: str
    metadata: Dict[str, Any]
    source: str
    score: float


class ToolCall(TypedDict):
    """Record of a tool call."""
    tool_name: str
    arguments: Dict[str, Any]
    result: Any
    error: Optional[str]


class AgentState(TypedDict):
    """Main state object for the agentic RAG system.
    
    This state is passed between all nodes in the LangGraph and
    persisted by the checkpointer.
    """
    # Conversation messages
    messages: Annotated[List[BaseMessage], add_messages]
    
    # Current user query
    query: str
    
    # Router decision
    route_decision: Optional[RouterDecision]
    
    # Retrieved context
    retrieval_results: List[RetrievalResult]
    
    # Tool execution history
    tool_calls: List[ToolCall]
    
    # Error handling
    error: Optional[str]
    error_count: int
    
    # Human-in-the-loop
    needs_approval: bool
    approval_request: Optional[str]
    human_feedback: Optional[str]
    
    # Final answer
    final_answer: Optional[str]
    
    # Metadata
    session_id: str
    thread_id: str
    iteration_count: int
    max_iterations: int