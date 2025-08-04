"""Search tools for the agent to use."""

import asyncio
from typing import List, Dict, Any

from langchain_core.tools import tool

from src.retrievers import (
    VectorRetriever,
    HybridRetriever,
    GraphRetriever,
    VectorCypherRetriever
)
from src.retrievers.enhanced_vector import EnhancedVectorRetriever

# Initialize retrievers (these could be cached or managed differently in production)
# Only use Neo4j for now since we don't have pgvector set up
neo4j_vector_retriever = VectorRetriever(use_neo4j=True)
enhanced_vector_retriever = EnhancedVectorRetriever()
hybrid_retriever = HybridRetriever()
graph_retriever = GraphRetriever()
vector_cypher_retriever = VectorCypherRetriever()


@tool
async def vector_search_tool(query: str, k: int = 5) -> str:
    """Search for semantically similar documents using vector embeddings.
    
    Best for:
    - Finding conceptually related information
    - General knowledge queries
    - When exact keywords might not match
    
    Args:
        query: Natural language search query
        k: Number of results to return
        
    Returns:
        String containing the search results
    """
    # Use enhanced vector retriever for better entity search
    results = await enhanced_vector_retriever.retrieve(query, k=k)
    
    if not results:
        return "No results found for the vector search query."
    
    # Format results for the agent
    formatted_results = []
    for i, result in enumerate(results):
        formatted_results.append(
            f"Result {i+1} (score: {result['score']:.3f}):\n{result['content']}\n"
        )
    
    return "\n---\n".join(formatted_results)


@tool
async def hybrid_search_tool(query: str, k: int = 5) -> str:
    """Search using both semantic similarity and keyword matching.
    
    Best for:
    - Queries with specific names, acronyms, or technical terms
    - When you need both conceptual and exact matches
    - Product names, project codes, or identifiers
    
    Args:
        query: Natural language search query with potential keywords
        k: Number of results to return
        
    Returns:
        String containing the hybrid search results
    """
    results = await hybrid_retriever.retrieve(query, k=k)
    
    if not results:
        return "No results found for the hybrid search query."
    
    # Format results for the agent
    formatted_results = []
    for i, result in enumerate(results):
        formatted_results.append(
            f"Result {i+1} (score: {result['score']:.3f}):\n{result['content']}\n"
        )
    
    return "\n---\n".join(formatted_results)


@tool
async def graph_query_tool(query: str) -> str:
    """Query the knowledge graph to find entities and relationships.
    
    Best for:
    - Questions about relationships between entities
    - Multi-hop queries (e.g., "Who worked on projects led by X?")
    - Structured data queries
    - Finding connections between concepts
    
    Args:
        query: Natural language question about entities and relationships
        
    Returns:
        String containing the graph query results
    """
    results = await graph_retriever.retrieve(query, k=10)
    
    if not results:
        return "No results found from the graph query."
    
    # Format results for the agent
    formatted_results = []
    for i, result in enumerate(results):
        formatted_results.append(f"Graph Result {i+1}:\n{result['content']}\n")
        
        # Include the Cypher query if available
        if 'cypher_query' in result['metadata']:
            formatted_results.append(f"Query used: {result['metadata']['cypher_query']}\n")
    
    return "\n---\n".join(formatted_results)


@tool
async def vector_cypher_search_tool(query: str, k: int = 5) -> str:
    """Advanced search that finds relevant documents then expands context using the graph.
    
    Best for:
    - Complex questions requiring both similarity and relationships
    - When you need enriched context around a topic
    - Finding related entities and their connections
    - Deep, comprehensive answers
    
    Args:
        query: Natural language search query
        k: Number of initial results before expansion
        
    Returns:
        String containing enriched search results with graph context
    """
    results = await vector_cypher_retriever.retrieve(query, k=k)
    
    if not results:
        return "No results found for the vector-cypher search query."
    
    # Format enriched results for the agent
    formatted_results = []
    for i, result in enumerate(results):
        formatted_results.append(
            f"Enriched Result {i+1} (score: {result['score']:.3f}):\n{result['content']}\n"
        )
        
        # Include metadata about related entities if available
        if 'related_entities' in result['metadata'] and result['metadata']['related_entities']:
            entities = result['metadata']['related_entities']
            formatted_results.append(f"Related entities found: {', '.join(entities)}\n")
    
    return "\n---\n".join(formatted_results)


# Tool list for easy access
ALL_SEARCH_TOOLS = [
    vector_search_tool,
    hybrid_search_tool,
    graph_query_tool,
    vector_cypher_search_tool
]