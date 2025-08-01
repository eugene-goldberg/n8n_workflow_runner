# SpyroSolutions Pure Neo4j-GraphRAG-Python Adoption

## Overview

This document outlines how to adopt neo4j-graphrag-python as-is for SpyroSolutions, using only the components provided by the official library without any custom additions.

## Direct Implementation

### 1. Use HybridRetriever for All Queries

The `HybridRetriever` automatically combines vector and fulltext search, which addresses our original problem where business queries weren't using graph tools properly.

```python
from neo4j import GraphDatabase
from neo4j_graphrag.retrievers import HybridRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM

# Initialize Neo4j driver
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "password")
)

# Initialize embedder
embedder = OpenAIEmbeddings(model="text-embedding-3-small")

# Create HybridRetriever - this handles both vector and fulltext search
hybrid_retriever = HybridRetriever(
    driver=driver,
    vector_index_name="vector",
    fulltext_index_name="fulltext",
    embedder=embedder,
    return_properties=["text", "type", "content"]
)

# Initialize LLM
llm = OpenAILLM(
    model_name="gpt-4",
    model_params={"temperature": 0.7}
)

# Create GraphRAG instance
rag = GraphRAG(
    retriever=hybrid_retriever,
    llm=llm
)

# Use it for all queries
result = rag.search(
    query_text="What is the revenue at risk for TechCorp?",
    return_context=True,
    retriever_config={"top_k": 5}
)
```

### 2. Alternative: Use HybridCypherRetriever for Enhanced Graph Traversal

For queries that need additional graph traversal after the initial search:

```python
from neo4j_graphrag.retrievers import HybridCypherRetriever

# Define a Cypher query to traverse relationships after finding initial nodes
retrieval_query = """
MATCH (node)-[:HAS_PROJECT]->(project:Project)
MATCH (project)-[:OWNED_BY]->(customer:Customer)
RETURN node.text as text, project.name as project, customer.name as customer
"""

hybrid_cypher_retriever = HybridCypherRetriever(
    driver=driver,
    vector_index_name="vector",
    fulltext_index_name="fulltext",
    retrieval_query=retrieval_query,
    embedder=embedder
)

# Use with GraphRAG
rag_with_cypher = GraphRAG(
    retriever=hybrid_cypher_retriever,
    llm=llm
)
```

### 3. Complete FastAPI Implementation

```python
from fastapi import FastAPI
from pydantic import BaseModel
import neo4j
from neo4j_graphrag.retrievers import HybridRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.llm import OpenAILLM
import os

app = FastAPI(title="SpyroSolutions GraphRAG API")

class QueryRequest(BaseModel):
    message: str
    top_k: int = 5

class QueryResponse(BaseModel):
    response: str
    context_items: int

# Initialize components
driver = neo4j.GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(
        os.getenv("NEO4J_USERNAME", "neo4j"),
        os.getenv("NEO4J_PASSWORD", "password")
    )
)

embedder = OpenAIEmbeddings(
    model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
)

llm = OpenAILLM(
    model_name=os.getenv("LLM_MODEL", "gpt-4"),
    model_params={"temperature": 0.7}
)

# Use HybridRetriever for everything
retriever = HybridRetriever(
    driver=driver,
    vector_index_name="vector",
    fulltext_index_name="fulltext",
    embedder=embedder
)

rag = GraphRAG(retriever=retriever, llm=llm)

@app.post("/query", response_model=QueryResponse)
async def query_graphrag(request: QueryRequest):
    """Query endpoint using pure neo4j-graphrag-python"""
    
    result = rag.search(
        query_text=request.message,
        return_context=True,
        retriever_config={"top_k": request.top_k}
    )
    
    return QueryResponse(
        response=result.answer,
        context_items=len(result.retriever_result.items) if hasattr(result, 'retriever_result') else 0
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
```

## Why This Solves Our Problem

1. **HybridRetriever automatically combines vector and fulltext search** - This ensures business queries like "revenue at risk for TechCorp" will use both semantic search AND keyword matching on entity names.

2. **No need for explicit tool selection** - The hybrid approach searches both indexes simultaneously.

3. **Built-in ranking** - The library handles result fusion and ranking from both search methods.

## Migration Steps

1. **Install the package**:
   ```bash
   pip install "neo4j-graphrag[openai]"
   ```

2. **Update your existing code** to use HybridRetriever instead of separate vector/graph tools

3. **Keep your existing indexes** - The library works with standard Neo4j vector and fulltext indexes

## Testing

```python
# Test queries that previously failed
test_queries = [
    "What is the revenue at risk for TechCorp?",
    "Show me all customers with subscription issues",
    "Find companies similar to Acme Corp",
    "Which projects are delayed?"
]

for query in test_queries:
    result = rag.search(query, return_context=True)
    print(f"Query: {query}")
    print(f"Answer: {result.answer}")
    print(f"Context items: {len(result.retriever_result.items)}")
    print("---")
```

## Benefits

1. **Simplicity** - Use one retriever for all queries
2. **No custom code** - Everything is from the official library
3. **Automatic hybrid search** - Solves the original problem without complex routing
4. **Production ready** - Backed by Neo4j official support

This approach uses neo4j-graphrag-python exactly as designed, without any custom components or routers.