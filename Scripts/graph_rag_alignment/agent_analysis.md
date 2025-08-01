# RAG Agent Analysis: Tool Selection Logic

## Key Finding: Restrictive System Prompt

The current system prompt contains this critical instruction:
```
"Use the knowledge graph tool only when the user asks about two companies in the same question. Otherwise, use just the vector store tool."
```

This explains why 80% of our natural business questions defaulted to vector search only!

## Available Tools in the Agent

1. **vector_search**: Semantic similarity search
2. **graph_search**: Knowledge graph facts and relationships
3. **hybrid_search**: Vector + keyword search (NOT vector + graph)
4. **get_entity_relationships**: Direct entity relationship traversal
5. **get_entity_timeline**: Temporal entity data
6. **get_document**: Full document retrieval
7. **list_documents**: Document listing

## The Problem

The agent has several issues:

### 1. Overly Restrictive Graph Search Rule
The "two companies" rule means graph search is only triggered for queries like:
- "How do Disney and EA compare?"
- "What's the relationship between Netflix and Spotify?"

But NOT for equally important queries like:
- "How much revenue at risk if Disney misses SLA?" (only mentions one company)
- "What are risks to our $10M target?" (no specific companies)
- "Top 5 customer commitments?" (general query)

### 2. Misnamed "Hybrid" Search
The `hybrid_search` tool is actually vector + keyword search, not vector + graph search. This creates confusion about what true hybrid search means in this context.

### 3. Limited Business Context
The system prompt focuses on "big tech companies and their AI initiatives" rather than the actual SpyroSolutions SaaS business model with:
- Customers, subscriptions, ARR/MRR
- Projects, teams, capacity
- SLAs, risks, success scores
- Business objectives and operational costs

## Why Natural Queries Fail

For a query like "How much revenue will be at risk if Disney misses its SLA next month?", the agent:
1. Sees only one company mentioned (Disney)
2. Following the prompt rule, uses only vector search
3. Misses the need to traverse: Disney → SLA → Subscription → Revenue

## Recommended System Prompt Changes

Replace the restrictive rule with business-aware logic:

```
Use graph search or entity relationships when queries involve:
- Financial calculations (revenue, costs, ARR/MRR)
- Risk assessments linking entities to impacts
- Customer health or success scores
- Team capacity and project relationships
- SLA compliance and event impacts
- Questions with "if X then Y" patterns
- Ranking or comparing entities by metrics
- Understanding cascading effects

Use vector search for:
- General knowledge questions
- Document content retrieval
- Conceptual explanations

Combine both (true hybrid) when:
- Analyzing patterns across entities
- Predicting future impacts based on current state
- Complex business questions requiring both facts and analysis
```

## Tool Selection Logic Should Consider

1. **Entity Mentions**: Any named entity (customer, product, team) should consider graph
2. **Relationship Words**: "impact", "affect", "risk", "prevent", "cause"
3. **Metrics**: Revenue, cost, score, capacity, utilization
4. **Temporal**: "if X happens", "next month", "by Q1"
5. **Aggregations**: "total", "top 5", "across all"

## The Fix

1. Update the system prompt to understand SpyroSolutions business model
2. Remove the "two companies" restriction
3. Add pattern recognition for business questions
4. Clarify when to use each tool based on query intent
5. Enable true vector+graph hybrid search for complex queries

The current implementation is preventing the system from leveraging the rich graph structure we've built, defaulting to simple semantic search for queries that clearly need relationship traversal.