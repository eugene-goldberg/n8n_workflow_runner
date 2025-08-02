# Schema Compatibility Guide

## Overview

The SpyroSolutions Agentic RAG system now supports **dual-schema compatibility**, allowing it to query data from both:
1. **Spyro RAG format**: Original schema using labels like `:Customer`, `:Product`, `:Team`
2. **LlamaIndex format**: New schema using labels like `:__Entity__:CUSTOMER`, `:__Entity__:PRODUCT`, `:__Entity__:TEAM`

This ensures seamless integration between the existing Spyro RAG data and newly ingested documents via LlamaIndex.

## Why Dual Schema Support?

When using LlamaIndex for document ingestion, it creates entities with a different labeling convention:
- Spyro RAG: `(:Customer {name: "TechCorp"})`
- LlamaIndex: `(:__Entity__:CUSTOMER {name: "InnovateTech Solutions"})`

Both formats represent the same semantic model but with different Neo4j labels.

## How It Works

### 1. Compatible Cypher Queries

The system automatically transforms queries to check both label formats:

```cypher
-- Original query
MATCH (c:Customer) RETURN c.name

-- Compatible query
MATCH (c) 
WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
RETURN c.name
```

### 2. Label Mapping

| Spyro RAG Label | LlamaIndex Label |
|-----------------|------------------|
| Customer | CUSTOMER |
| Product | PRODUCT |
| Team | TEAM |
| Risk | RISK |
| SaaSSubscription | SUBSCRIPTION |
| AnnualRecurringRevenue | REVENUE |
| CustomerSuccessScore | CUSTOMER_SUCCESS_SCORE |
| Feature | FEATURE |
| Project | PROJECT |
| Objective | OBJECTIVE |

### 3. Unified Tools

The agent provides tools that automatically handle both schemas:

- **UnifiedSearch**: Primary tool that queries both formats automatically
- **GraphQuery**: Advanced Cypher queries with dual-schema support
- **HybridSearch**: Content search across all documents
- **VectorSearch**: Semantic similarity search

## Usage Examples

### Query for All Customers
```bash
curl -X POST "http://localhost:8001/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "question": "List all customers with their subscription values"
  }'
```

This will return customers from both schemas:
- Original: TechCorp, FinanceHub, CloudFirst
- LlamaIndex: InnovateTech Solutions, Global Manufacturing Corp

### Query Specific Customer
```bash
# Works for original customer
curl -X POST "http://localhost:8001/query" \
  -d '{"question": "Tell me about TechCorp"}'

# Works for LlamaIndex customer  
curl -X POST "http://localhost:8001/query" \
  -d '{"question": "Tell me about InnovateTech Solutions"}'
```

### Aggregations Across Both Schemas
```bash
curl -X POST "http://localhost:8001/query" \
  -d '{"question": "What is our total Annual Recurring Revenue?"}'
```

This calculates ARR from both data sources.

## Implementation Details

### Key Components

1. **`schema_compatibility.py`**: Provides label mapping and query transformation functions
2. **`cypher_examples_compatible.py`**: Examples using flexible label patterns
3. **`spyro_agent_compatible.py`**: Updated agent with dual-schema support
4. **Unified Schema**: Describes both labeling conventions for the LLM

### Query Transformation

The `get_compatible_cypher()` function automatically converts standard Cypher to dual-schema compatible queries:

```python
from utils.schema_compatibility import get_compatible_cypher

original = "MATCH (c:Customer) RETURN c.name"
compatible = get_compatible_cypher(original)
# Result: MATCH (c) WHERE ('Customer' IN labels(c) OR ...) RETURN c.name
```

## Benefits

1. **No Data Migration Required**: Both schemas coexist peacefully
2. **Seamless Integration**: Query both old and new data transparently
3. **Future-Proof**: Easy to add more schema variations if needed
4. **Backward Compatible**: All existing queries continue to work

## Testing

Run the compatibility test script:

```bash
# Check what schemas exist
./check_schemas.py

# Test compatible queries
./test_compatible_queries.sh

# Run comprehensive tests
./test_dual_schema.py
```

## Troubleshooting

### Query Returns No Results

If a query returns no results:
1. Check if the entity exists in either schema using `check_schemas.py`
2. Verify the UnifiedSearch tool is being used (check agent logs)
3. Try explicit label patterns in GraphQuery tool

### Performance Considerations

Dual-schema queries may be slightly slower due to checking multiple label patterns. For performance-critical queries, consider:
1. Creating unified views in Neo4j
2. Migrating data to a single schema format
3. Using indexes on common properties

## Future Enhancements

1. **Automatic Schema Detection**: Detect which schema to use based on query context
2. **Schema Migration Tools**: Utilities to convert between formats
3. **Performance Optimization**: Cached schema mappings and query plans
4. **Extended Compatibility**: Support for additional ingestion tools