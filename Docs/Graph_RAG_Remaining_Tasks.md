# Graph RAG Remaining Tasks & Enhancement Opportunities

## Current State Analysis

### What's Working
1. **Neo4j Integration**: Successfully connected and operational
2. **Graphiti Integration**: Creating entities and relationships from documents
3. **Basic Graph Search**: Tool available and functional
4. **Entity Extraction**: 30 entities created from 3 documents
5. **Relationship Creation**: MENTIONS and RELATES_TO relationships established

### Issues Identified

#### 1. Entity Type Classification
**Problem**: Entity types are NULL in the database
```
"SpyroSolutions},{", NULL
"EA},{", NULL
```
**Impact**: Cannot filter entities by type (Customer, Product, Risk, etc.)
**Priority**: HIGH

#### 2. Data Quality Issues
**Problem**: Malformed entity names with special characters ("},{"")
**Impact**: Affects search accuracy and display
**Priority**: HIGH

#### 3. Limited Relationship Types
**Current**: Only MENTIONS and RELATES_TO
**Missing**: 
- HAS_RISK
- USES_PRODUCT
- MITIGATES_WITH
- HAS_CONTRACT_VALUE
- AT_RISK_AMOUNT
**Priority**: MEDIUM

## Recommended Tasks

### Task 1: Fix Entity Extraction Pipeline
```python
# Update ingestion/ingest.py to properly set entity types
entity_types = {
    "customer": ["Disney", "EA", "Netflix", "Spotify", "Nintendo"],
    "product": ["SpyroSuite", "SpyroAnalytics", "SpyroGuard"],
    "risk": ["SLA violations", "performance issues", "security concerns"],
    "metric": ["MRR", "revenue at risk", "escalations"]
}
```

### Task 2: Create Proper Graph Schema
```cypher
// Define constraints and indexes
CREATE CONSTRAINT customer_name IF NOT EXISTS 
FOR (c:Customer) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT product_name IF NOT EXISTS 
FOR (p:Product) REQUIRE p.name IS UNIQUE;

CREATE INDEX customer_risk_score IF NOT EXISTS 
FOR (c:Customer) ON (c.risk_score);
```

### Task 3: Implement Structured Entity Ingestion
```python
# Better approach for structured data
def ingest_structured_data():
    # Customers with properties
    customers = [
        {
            "name": "Disney",
            "tier": "Enterprise",
            "mrr": 125000,
            "risk_score": 8,
            "contract_value": 1500000
        },
        # ... more customers
    ]
    
    # Create typed nodes
    for customer in customers:
        graph.add_node(
            name=customer["name"],
            node_type="Customer",
            properties=customer
        )
```

### Task 4: Enhance Relationship Extraction
```python
# Define relationship patterns
relationship_patterns = [
    {
        "pattern": r"(\w+) uses (\w+)",
        "rel_type": "USES_PRODUCT",
        "source_type": "Customer",
        "target_type": "Product"
    },
    {
        "pattern": r"(\w+) has risk score of (\d+)",
        "rel_type": "HAS_RISK_SCORE",
        "source_type": "Customer",
        "property": "score"
    }
]
```

### Task 5: Implement Advanced Graph Queries
```python
# Add to tools/graph_tools.py
async def get_customer_360(customer_name: str):
    """Get complete view of a customer"""
    query = """
    MATCH (c:Customer {name: $name})
    OPTIONAL MATCH (c)-[:USES_PRODUCT]->(p:Product)
    OPTIONAL MATCH (c)-[:HAS_RISK]->(r:Risk)
    OPTIONAL MATCH (c)-[:MITIGATES_WITH]->(m:Mitigation)
    RETURN c, collect(DISTINCT p) as products, 
           collect(DISTINCT r) as risks,
           collect(DISTINCT m) as mitigations
    """
    return await graph.query(query, {"name": customer_name})
```

### Task 6: Add Graph Analytics
```cypher
// PageRank for most influential entities
CALL gds.pageRank.stream('customer-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS name, score
ORDER BY score DESC

// Community detection for customer segments
CALL gds.louvain.stream('customer-graph')
YIELD nodeId, communityId
```

### Task 7: Improve Graph Visualization
- Add graph visualization endpoint
- Return Cypher query results in vis.js format
- Enable interactive exploration in n8n

## Quick Fixes (Immediate Priority)

### 1. Clean Existing Data
```bash
# Remove malformed entities
docker exec spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' \
  "MATCH (n:Entity) WHERE n.name CONTAINS '},{' DELETE n"
```

### 2. Re-run Ingestion with Fixes
```python
# Update entity extraction regex
entity_pattern = r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b'
```

### 3. Add Entity Type Mapping
```python
# In ingestion pipeline
def classify_entity(entity_name):
    if entity_name in ["Disney", "EA", "Netflix", "Nintendo", "Spotify"]:
        return "Customer"
    elif "Spyro" in entity_name:
        return "Product"
    elif any(word in entity_name.lower() for word in ["risk", "issue", "violation"]):
        return "Risk"
    return "General"
```

## Testing Checklist

- [ ] Verify entity types are properly set
- [ ] Test relationship extraction accuracy
- [ ] Validate graph traversal queries
- [ ] Check performance with larger datasets
- [ ] Test complex multi-hop queries
- [ ] Verify tool selection for graph vs vector

## Expected Outcomes

After implementing these tasks:
1. **Rich Graph Structure**: Typed entities with meaningful relationships
2. **Better Query Results**: More accurate answers for relationship questions
3. **Analytics Capabilities**: Insights into customer networks and risk patterns
4. **Improved Tool Selection**: Clear separation between graph and vector use cases

## Time Estimate

- Quick Fixes: 1-2 hours
- Full Enhancement: 4-6 hours
- Testing & Validation: 2 hours

## Next Steps

1. Start with quick fixes to clean data
2. Implement proper entity typing
3. Enhance relationship extraction
4. Add advanced graph queries
5. Test with real-world scenarios