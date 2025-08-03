# Failing Queries Investigation

## Summary
- **Total Queries**: 60
- **Grounded**: 34 (56.7%)
- **Generic/Failed**: 26 (43.3%)

## Root Causes of Failures

### 1. Relationship Model Migration Issues (3 queries)
**Affected**: Q7 (projections), potentially Q52, Q53
- **Issue**: After migrating to relationship model, agent still queries for properties that are now in connected nodes
- **Example**: Q7 tries `p.quarter` and `p.projected_revenue` but these are now in connected QUARTER and METRIC nodes
- **Fix**: Agent needs updated examples showing relationship traversal patterns

### 2. Overly Broad Queries (8 queries)
**Affected**: Q4, Q29, Q48, etc.
- **Issue**: Agent returns counts that match all entities (58 customers, 107 features)
- **Example**: Q4 "customers at risk" returns 58 (all customers) because it counts ANY customer with active risks
- **Fix**: Need more specific filtering criteria

### 3. Missing Data (12 queries)
**Affected**: Q15, Q16, Q19, Q33, Q34, Q35, Q36, Q37, Q42, Q44, Q45, Q57
- **Issue**: No data exists for these queries in Neo4j
- **Examples**:
  - No support ticket data
  - No integration issue details
  - No external vendor dependencies
  - No project priorities
- **Fix**: Add missing data to Neo4j

### 4. Poor Data Modeling (3 queries)
**Affected**: Q25, Q51, Q60
- **Issue**: Data exists but not in queryable format
- **Example**: Q60 uses "segment" for lifecycle stage instead of proper lifecycle property
- **Fix**: Improve data model with proper properties

## Specific Query Analysis

### Q7: Projections (FIXABLE)
```cypher
# Current (failing):
MATCH (p:__Entity__ :PROJECTION)
WHERE p.quarter STARTS WITH 'Q'...

# Should be:
MATCH (p:__Entity__:PROJECTION)-[:FOR_PERIOD]->(q:QUARTER)
WHERE q.year = 2025
MATCH (p)-[:PROJECTS]->(m:METRIC)
RETURN q.name, m.value
```

### Q4: Customers at Risk (FIXABLE)
```cypher
# Current (too broad):
MATCH (c:CUSTOMER)
OPTIONAL MATCH (c)-[:HAS_RISK]->(r:RISK)
WHERE r.status = 'active'
RETURN COUNT(DISTINCT c)

# Should filter by multiple risk factors:
- Low success scores (<60)
- Active risks
- Declining trends
- Payment issues
```

### Q15: Integration Issues (NEEDS DATA)
- No INTEGRATION_ISSUE entities exist
- Need to create this entity type and relationships

## Recommendations

### Immediate Fixes (Can improve ~10 queries)
1. Update Cypher examples for relationship model
2. Add multi-criteria filtering for "at risk" queries
3. Fix lifecycle stage modeling

### Data Additions (Can improve ~12 queries)
1. Create INTEGRATION_ISSUE entities
2. Add SUPPORT_TICKET entities
3. Add executive sponsor relationships
4. Add project priority properties
5. Add external vendor dependencies

### Success Rate Projection
- Current: 56.7%
- With immediate fixes: ~73%
- With data additions: ~93%

## Priority Actions
1. **Fix Q7**: Update projection query for relationship model
2. **Fix Q4**: Add proper risk criteria
3. **Add critical missing data**: Support tickets, integration issues
4. **Update agent examples**: Show relationship traversal patterns