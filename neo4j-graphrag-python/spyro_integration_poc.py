#!/usr/bin/env python3
"""
Proof of Concept: SpyroSolutions integration with neo4j-graphrag-python

This demonstrates how to:
1. Use the official neo4j-graphrag-python library
2. Integrate our deterministic router
3. Maintain compatibility with existing SpyroSolutions API
"""

import os
from typing import List, Tuple, Optional
from enum import Enum
import neo4j
from neo4j_graphrag.retrievers import HybridRetriever, VectorRetriever, Text2CypherRetriever
from neo4j_graphrag.retrievers.base import Retriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem
from fastapi import FastAPI
from pydantic import BaseModel

# Router implementation (from our previous work)
class RetrievalStrategy(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID_SEQUENTIAL = "hybrid_sequential"
    HYBRID_PARALLEL = "hybrid_parallel"
    NO_RETRIEVAL = "no_retrieval"

class DeterministicRouter:
    """Our deterministic router with business rules"""
    
    def route(self, query: str) -> Tuple[RetrievalStrategy, float, List[str]]:
        # Simplified routing logic for POC
        query_lower = query.lower()
        
        # Business queries -> Graph
        if any(term in query_lower for term in ["revenue", "risk", "commitment", "sla"]):
            return RetrievalStrategy.GRAPH, 0.9, []
        
        # Relationship queries -> Hybrid
        if any(term in query_lower for term in ["related", "connected", "similar"]):
            return RetrievalStrategy.HYBRID_SEQUENTIAL, 0.8, []
        
        # Default -> Vector
        return RetrievalStrategy.VECTOR, 0.7, []

# Custom retriever that integrates our router
class RouterEnabledRetriever(Retriever):
    """Custom retriever that uses deterministic routing"""
    
    def __init__(
        self, 
        driver: neo4j.Driver,
        vector_retriever: VectorRetriever,
        hybrid_retriever: HybridRetriever, 
        text2cypher: Text2CypherRetriever,
        router: DeterministicRouter,
        neo4j_database: Optional[str] = None
    ):
        super().__init__(driver, neo4j_database)
        self.vector_retriever = vector_retriever
        self.hybrid_retriever = hybrid_retriever
        self.text2cypher = text2cypher
        self.router = router
        self.last_strategy_used = None
        self.last_confidence = None
    
    def search(self, query_text: str, top_k: int = 5, **kwargs) -> RetrieverResult:
        """Route query to appropriate retriever based on pattern analysis"""
        
        # Get routing decision
        strategy, confidence, entities = self.router.route(query_text)
        self.last_strategy_used = strategy.value
        self.last_confidence = confidence
        
        print(f"Router decision: {strategy.value} (confidence: {confidence:.2f})")
        
        # Execute appropriate retriever
        if strategy == RetrievalStrategy.GRAPH:
            # Use Text2Cypher for graph queries
            return self.text2cypher.search(query_text=query_text, top_k=top_k)
            
        elif strategy in [RetrievalStrategy.HYBRID_SEQUENTIAL, RetrievalStrategy.HYBRID_PARALLEL]:
            # Use HybridRetriever for combined search
            return self.hybrid_retriever.search(query_text=query_text, top_k=top_k)
            
        else:
            # Default to vector search
            return self.vector_retriever.search(query_text=query_text, top_k=top_k)

# FastAPI app (similar to SpyroSolutions)
app = FastAPI(title="SpyroSolutions GraphRAG POC")

class QueryRequest(BaseModel):
    message: str
    top_k: int = 5

class QueryResponse(BaseModel):
    response: str
    retriever_used: str
    confidence: float
    context_items: int

# Initialize components
def create_graphrag_pipeline():
    """Create the GraphRAG pipeline with router integration"""
    
    # Neo4j connection
    driver = neo4j.GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=(
            os.getenv("NEO4J_USERNAME", "neo4j"),
            os.getenv("NEO4J_PASSWORD", "password")
        )
    )
    
    # Initialize embedder and LLM
    embedder = OpenAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    
    llm = OpenAILLM(
        model_name=os.getenv("LLM_MODEL", "gpt-4"),
        model_params={"temperature": 0.7}
    )
    
    # Create retrievers
    vector_retriever = VectorRetriever(
        driver=driver,
        index_name="vector",
        embedder=embedder,
        return_properties=["text", "embedding"]
    )
    
    hybrid_retriever = HybridRetriever(
        driver=driver,
        vector_index_name="vector",
        fulltext_index_name="fulltext",
        embedder=embedder
    )
    
    text2cypher = Text2CypherRetriever(
        driver=driver,
        llm=llm,
        neo4j_schema=None  # Auto-detect schema
    )
    
    # Create router
    router = DeterministicRouter()
    
    # Create router-enabled retriever
    router_retriever = RouterEnabledRetriever(
        driver=driver,
        vector_retriever=vector_retriever,
        hybrid_retriever=hybrid_retriever,
        text2cypher=text2cypher,
        router=router
    )
    
    # Create GraphRAG instance
    graph_rag = GraphRAG(
        retriever=router_retriever,
        llm=llm
    )
    
    return graph_rag, router_retriever

# Global instances
graph_rag, router_retriever = create_graphrag_pipeline()

@app.post("/query", response_model=QueryResponse)
async def query_graphrag(request: QueryRequest):
    """Main query endpoint compatible with SpyroSolutions API"""
    
    # Execute query
    result = graph_rag.search(
        query_text=request.message,
        return_context=True,
        retriever_config={"top_k": request.top_k}
    )
    
    # Format response
    return QueryResponse(
        response=result.answer,
        retriever_used=router_retriever.last_strategy_used,
        confidence=router_retriever.last_confidence,
        context_items=len(result.retriever_result.items) if hasattr(result, 'retriever_result') else 0
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "SpyroSolutions GraphRAG POC"}

# Test script
if __name__ == "__main__":
    import asyncio
    
    test_queries = [
        "What is the revenue at risk for TechCorp?",
        "Show me customers with high churn risk",
        "Find companies similar to Acme Corp",
        "What are the key features of our analytics platform?",
        "Which customers have SLA compliance issues?"
    ]
    
    async def test_pipeline():
        print("Testing SpyroSolutions GraphRAG Pipeline\n")
        print("=" * 60)
        
        for query in test_queries:
            request = QueryRequest(message=query)
            response = await query_graphrag(request)
            
            print(f"\nQuery: {query}")
            print(f"Retriever: {response.retriever_used} (confidence: {response.confidence:.2f})")
            print(f"Context items: {response.context_items}")
            print(f"Response: {response.response[:200]}...")
            print("-" * 60)
    
    # Run test
    asyncio.run(test_pipeline())
    
    # To run as API server:
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)