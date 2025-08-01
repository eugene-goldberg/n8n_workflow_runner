# SpyroSolutions Hybrid Agentic RAG Implementation

## Overview

This implementation provides a complete Hybrid Agentic RAG system for SpyroSolutions using the neo4j-graphrag-python library, following the semantic model exactly as specified.

## Semantic Model Implementation

### Entities (Nodes)
Based on the semantic model diagram, we've implemented:

1. **Core Business Entities**:
   - Product
   - Customer  
   - Project
   - Team
   - SaaS Subscription
   - Risk

2. **Metrics & Measurements**:
   - SLA
   - Operational Statistics
   - Roadmap
   - Feature
   - Annual Recurring Revenue (ARR)
   - Customer Success Score
   - Events

3. **Financial & Strategic**:
   - Operational Cost
   - Profitability
   - Company Objective

### Relationships
All relationships from the semantic model are implemented:
- Product → SLA, Operational Statistics, Roadmap, Team, Customer
- Customer → SaaS Subscription, Success Score, Events, Risk
- Project → Features, Operational Cost, Profitability, Company Objectives
- Financial flows: Subscription → ARR, Risk → Customer/Revenue impacts
- Feature commitments and roadmap relationships

## Technical Architecture

### 1. Knowledge Graph Builder
- Uses `SimpleKGPipeline` from neo4j-graphrag-python
- Automatically extracts entities and relationships from text
- Creates embeddings for all text chunks
- Follows the exact schema from the semantic model

### 2. Hybrid Retrieval System
Two retriever types are implemented:

**HybridRetriever**: 
- Combines vector search (semantic) with fulltext search (keyword)
- Automatically fuses results for better accuracy
- Ideal for general business queries

**HybridCypherRetriever**:
- Adds graph traversal capabilities
- Explores entity relationships after initial retrieval
- Perfect for complex business questions requiring context

### 3. Indexes
- **Vector Index**: For semantic similarity search (1536 dimensions)
- **Fulltext Index**: For keyword-based search
- Both indexes work together in hybrid retrieval

## Sample Data

The implementation includes comprehensive sample data:
- 3 Products (SpyroCloud, SpyroAI, SpyroSecure)
- 3 Customers (TechCorp, GlobalBank, RetailMax)
- 3 Projects (Titan, Mercury, Apollo)
- Complete relationships including risks, subscriptions, ARR, etc.

## API Endpoints

### POST /query
Execute queries against the knowledge graph:
```json
{
  "question": "Which customers are at risk?",
  "use_cypher": true
}
```

Response:
```json
{
  "question": "Which customers are at risk?",
  "answer": "TechCorp has medium risk...",
  "context_items": 5,
  "retriever_type": "hybrid_cypher"
}
```

### GET /health
Check system status

## Running the System

1. **Start Neo4j** (already running in Docker)

2. **Run the API**:
   ```bash
   python3 run_spyro_api.py
   ```

3. **Test queries**:
   ```bash
   python3 test_spyro_queries.py
   ```

## Key Features

1. **No Custom Components**: Uses only neo4j-graphrag-python library components
2. **Automatic Schema Extraction**: The LLM understands and extracts based on provided schema
3. **Hybrid Search**: Combines the best of semantic and keyword search
4. **Graph-Aware**: Can traverse relationships for complex queries
5. **Production Ready**: Built on official Neo4j library with proper error handling

## Query Examples

### Simple Product Query
```
Q: "What products does SpyroSolutions offer?"
Retriever: HybridRetriever
Result: Finds products through semantic + keyword search
```

### Complex Relationship Query
```
Q: "Which customers are at risk and what is their ARR?"
Retriever: HybridCypherRetriever  
Result: Traverses Customer → Risk and Customer → Subscription → ARR relationships
```

### Financial Analysis
```
Q: "What is the total profitability impact of all projects?"
Retriever: HybridCypherRetriever
Result: Aggregates Project → Profitability relationships
```

## Benefits

1. **Semantic Understanding**: Natural language queries are understood contextually
2. **Keyword Precision**: Entity names and specific terms are matched exactly
3. **Relationship Awareness**: Complex business relationships are traversed
4. **Scalable**: Can handle large amounts of business data
5. **Maintainable**: Uses standard Neo4j and official libraries

This implementation provides SpyroSolutions with a powerful, production-ready RAG system that accurately reflects their business semantic model.