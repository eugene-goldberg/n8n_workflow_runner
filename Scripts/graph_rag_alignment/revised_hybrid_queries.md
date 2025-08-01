# Revised Hybrid Search Queries

After testing, here are revised queries that reliably trigger both vector AND graph search:

## ✅ Confirmed Working Hybrid Queries

### 1. Revenue Impact Analysis (Original Query 1 - Working)
```
How much revenue will be at risk if Disney's current SLA violations continue for another quarter, and which teams need to be allocated to prevent this?
```

### 2. Cross-Customer Risk Correlation (Original Query 2 - Working)
```
Analyze the correlation between customer success scores and project delays across Disney, EA, and Netflix, and identify which operational costs could be reduced to improve profitability while maintaining service quality.
```

## 🔄 Revised Queries (to ensure graph search triggers)

### 3. Strategic Objective with Entity Relationships
```
Show me the relationship between our $10M ARR target and the specific risks from Disney's at-risk projects and EA's feature delays, including which teams are involved
```
**Key change**: Added "Show me the relationship between" and specified entity names

### 4. Entity-to-Entity Impact Chain
```
Trace how Disney's service outage event connects to their declining success score and then show which other customers like Netflix and EA have similar event patterns
```
**Key change**: Used "trace" and "connects to" with multiple entity names

### 5. Multi-Entity Cascade Analysis
```
Map the connections between EA's security alert, Disney's SLA breach, and Netflix's project status, showing how these impact our customer retention objectives
```
**Key change**: Used "map the connections between" and listed multiple specific entities

## Why These Work Better

The revised queries explicitly:
1. Use relationship words: "relationship between", "connects to", "map the connections"
2. Name multiple specific entities: Disney, EA, Netflix
3. Request traversal between entities: "trace how X connects to Y"
4. Ask for multi-hop analysis: event → score → other customers

## Testing Protocol

To verify a query triggers true hybrid search:
1. Look for BOTH in the tools used:
   - `vector_search` (for semantic understanding)
   - `graph_search` OR `get_entity_relationships` (for graph traversal)
2. Don't rely solely on `metadata.search_type` as it may show "HYBRID" even with only vector searches
3. Check the actual tool names in the response

## Alternative Formulations

If a query isn't triggering graph search, try adding:
- "Show me the relationship between [Entity1] and [Entity2]"
- "How does [Entity1] connect to [Entity2]"
- "Trace the path from [Entity1] to [Entity2]"
- "Map the connections between [Entity1], [Entity2], and [Entity3]"

Always include at least 2 specific entity names (customers, products, teams, etc.) to increase the likelihood of graph search activation.