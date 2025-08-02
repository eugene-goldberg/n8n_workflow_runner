# Custom Property Graph Retriever Implementation Plan

## Overview
This plan details the implementation of a custom property graph retriever for SpyroSolutions based on the LlamaIndex custom retriever pattern. The goal is to replace the problematic Text2CypherRetriever-in-agent architecture with a more robust and controllable retrieval system.

## Current State Analysis

### Existing Components
- **Neo4j Database**: Contains extracted data with LlamaIndex schema (`:__Entity__:TYPE`)
- **Entities**: PRODUCT, CUSTOMER, OPERATIONAL_COST, COMMITMENT, TEAM, etc.
- **Vector Indexes**: `spyro_vector_index` and `spyro_fulltext_index`
- **LLM**: GPT-4o for query generation
- **Embeddings**: OpenAI embeddings

### Current Issues
1. Text2CypherRetriever fails frequently due to complex schema
2. Agent hits iteration limits when retrying failed queries
3. No fallback mechanism when Cypher generation fails
4. Generic error messages instead of specific data

## Implementation Architecture

### 1. Custom Retriever Class Structure

```python
class SpyroCustomPropertyGraphRetriever:
    """
    Custom retriever that combines multiple retrieval strategies:
    - Vector similarity search (fallback)
    - Text2Cypher for structured queries (primary)
    - Direct Cypher for known patterns (optimization)
    """
    
    def __init__(self):
        - vector_retriever: For semantic search
        - text2cypher_retriever: For dynamic queries
        - direct_cypher_patterns: Pre-defined query templates
        - reranker: Optional Cohere reranker
        - error_handler: Sophisticated error recovery
```

### 2. Retrieval Strategy Layers

#### Layer 1: Pattern Matching
- Match incoming queries against known patterns
- Use pre-defined, tested Cypher queries
- Examples:
  - "cost.*product.*region" → Direct cost aggregation query
  - "commitment.*risk" → Direct commitment risk query

#### Layer 2: Text2Cypher with Error Handling
- Attempt Text2Cypher generation
- Catch Text2CypherRetrievalError specifically
- Extract partial information from error messages
- Retry with simplified queries

#### Layer 3: Vector Fallback
- Use vector similarity when structured queries fail
- Search for relevant documents/nodes
- Extract entities mentioned in results

#### Layer 4: Hybrid Combination
- Combine results from successful strategies
- Apply reranking for relevance
- Format unified response

### 3. Error Recovery Mechanisms

```python
def retrieve_with_fallback(self, query: str):
    results = []
    
    # Try direct pattern match
    if pattern_result := self.try_pattern_match(query):
        results.extend(pattern_result)
    
    # Try Text2Cypher with recovery
    try:
        cypher_result = self.text2cypher_retriever.retrieve(query)
        results.extend(cypher_result)
    except Text2CypherRetrievalError as e:
        # Parse error for clues
        simplified_query = self.simplify_query(query, e)
        if fallback_result := self.try_simplified_cypher(simplified_query):
            results.extend(fallback_result)
    
    # Always include vector results
    vector_results = self.vector_retriever.retrieve(query)
    results.extend(vector_results)
    
    # Rerank and return
    return self.rerank_results(results)
```

### 4. Query Simplification Strategy

When Text2Cypher fails, progressively simplify:
1. Remove aggregations → Get raw data
2. Remove multiple hops → Query single relationship
3. Extract entity names → Query by entity
4. Fall back to entity type listing

### 5. Pre-defined Query Templates

Create templates for common business questions:

```python
QUERY_TEMPLATES = {
    "product_costs": {
        "pattern": r"cost.*product.*region",
        "cypher": """
            MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
            RETURN p.name as product, r.name as region, c.total_monthly_cost as cost, 
                   c.cost_per_customer as cost_per_customer
        """,
        "description": "Product costs by region"
    },
    "high_risk_commitments": {
        "pattern": r"commitment.*risk|risk.*commitment",
        "cypher": """
            MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
            WHERE com.risk_level IN ['High', 'Critical']
            RETURN c.name as customer, com.feature_name as feature, 
                   com.risk_level as risk, com.revenue_at_risk as revenue_at_risk
        """,
        "description": "High-risk customer commitments"
    },
    # ... more templates
}
```

### 6. Integration with Existing System

#### Option A: Direct GraphRAG Integration
```python
# Replace agent-based approach
custom_retriever = SpyroCustomPropertyGraphRetriever(
    driver=neo4j_driver,
    embed_model=embed_model,
    llm=llm
)

rag_pipeline = GraphRAG(
    retriever=custom_retriever,
    llm=llm
)

# Direct query without agent
response = rag_pipeline.query("What are the product costs by region?")
```

#### Option B: LangChain Tool Integration
```python
# Create a single, robust tool
def enhanced_graph_query(query: str) -> str:
    retriever = get_custom_retriever()
    results = retriever.retrieve_with_fallback(query)
    return format_results(results)

tools = [
    Tool(
        name="EnhancedGraphQuery",
        func=enhanced_graph_query,
        description="Robust graph query with automatic fallback"
    )
]
```

## Implementation Steps

### Phase 1: Core Retriever Development (Week 1)
1. Create `SpyroCustomPropertyGraphRetriever` class
2. Implement pattern matching layer
3. Integrate existing Text2CypherRetriever with error handling
4. Add vector retrieval fallback
5. Create result combination logic

### Phase 2: Query Templates (Week 1)
1. Analyze business questions to identify patterns
2. Create Cypher templates for top 20 queries
3. Implement pattern matching logic
4. Test templates against current data

### Phase 3: Error Recovery (Week 2)
1. Implement query simplification algorithms
2. Create error parsing logic
3. Add retry mechanisms with backoff
4. Implement partial result handling

### Phase 4: Integration (Week 2)
1. Create GraphRAG pipeline with custom retriever
2. Update API endpoints
3. Remove agent-based approach
4. Implement caching layer

### Phase 5: Optimization (Week 3)
1. Add Cohere reranking (optional)
2. Implement result caching
3. Add query performance monitoring
4. Create feedback loop for pattern learning

## Testing Strategy

### Unit Tests
- Test each retrieval layer independently
- Mock Text2CypherRetriever failures
- Verify fallback mechanisms
- Test query simplification

### Integration Tests
- Test with real Neo4j data
- Verify all business questions get meaningful answers
- Test error scenarios
- Benchmark performance

### Business Question Coverage
Create test suite covering all 60 business questions:
- Verify each gets substantive answer
- No "Agent stopped due to iteration limit"
- Specific data returned where available

## Success Metrics

1. **Query Success Rate**: >95% of queries return meaningful data
2. **Response Time**: <5 seconds average
3. **Error Recovery**: 100% of Text2Cypher failures handled gracefully
4. **Data Quality**: Specific values returned for cost/commitment queries
5. **No Agent Limits**: Zero "iteration limit" errors

## Configuration Management

### Environment Variables
```
CUSTOM_RETRIEVER_MODE=hybrid|cypher_first|vector_first
PATTERN_MATCH_ENABLED=true
TEXT2CYPHER_TIMEOUT=10
VECTOR_FALLBACK_ENABLED=true
RERANKING_ENABLED=false
CACHE_TTL=300
```

### Logging Strategy
- Log all Text2Cypher attempts and failures
- Track which retrieval strategy succeeded
- Monitor pattern match hit rate
- Record query simplification steps

## Migration Path

1. **Parallel Development**: Build custom retriever alongside existing system
2. **A/B Testing**: Route subset of queries to new retriever
3. **Gradual Rollout**: Increase traffic to custom retriever
4. **Full Migration**: Replace agent-based system
5. **Cleanup**: Remove old agent code

## Risk Mitigation

1. **Fallback to Original**: Keep agent system available during transition
2. **Monitoring**: Comprehensive logging and alerting
3. **Rollback Plan**: One-command rollback to agent system
4. **Data Validation**: Ensure results match or exceed current quality

## Future Enhancements

1. **Learning System**: Track successful patterns and auto-generate templates
2. **Multi-Stage Retrieval**: Chain multiple queries for complex questions
3. **Explanation Generation**: Explain how answer was derived
4. **Confidence Scoring**: Rate answer quality
5. **User Feedback Loop**: Improve patterns based on user satisfaction

## Conclusion

This custom retriever approach addresses all current issues:
- Eliminates agent iteration limits
- Provides graceful Text2Cypher failure handling
- Ensures all queries get meaningful responses
- Maintains query flexibility while adding robustness

The implementation prioritizes reliability and user experience while maintaining the sophisticated query capabilities needed for business intelligence questions.