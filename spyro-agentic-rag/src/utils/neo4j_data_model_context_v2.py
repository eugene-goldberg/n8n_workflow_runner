"""
Neo4j Data Model Context v2 - Relationship-Centric Model
This version emphasizes relationships over properties to align with LLM strengths
"""

DATA_MODEL_CONTEXT = """
# Neo4j Knowledge Graph Data Model - Relationship-Centric Version

## Core Philosophy
- Relationships are primary - they carry semantic meaning
- Properties are minimal - complex data lives in connected nodes
- LLMs excel at traversal - leverage this strength
- All entities use '__Entity__' label for LlamaIndex compatibility

## Updated Entity Patterns (Relationship-Centric)

### MARKETING_CHANNEL (Updated)
**Properties**: name (identifier only)
**Key Relationships**:
- (MARKETING_CHANNEL)-[:HAS_COST]->(COST) - Marketing spend
- (MARKETING_CHANNEL)-[:GENERATES]->(REVENUE) - Attributed revenue
- (MARKETING_CHANNEL)-[:ACHIEVES]->(PERFORMANCE_METRIC) - ROI and other metrics

**Query Pattern**: Traverse to metrics, don't look for properties
Example: To find ROI, follow ACHIEVES relationship to PERFORMANCE_METRIC

### PROJECTION (Updated)
**Properties**: name (identifier only)
**Key Relationships**:
- (PROJECTION)-[:FOR_PERIOD]->(QUARTER) - Time period
- (PROJECTION)-[:PROJECTS]->(METRIC) - Projected values with confidence

**Query Pattern**: Navigate to QUARTER for time, METRIC for values
Example: Match projections through FOR_PERIOD to find specific quarters

### REVENUE (Updated)
**Properties**: amount, period (kept for aggregation)
**Key Relationships**:
- (REVENUE)-[:HAS_TYPE]->(REVENUE_TYPE) - Recurring vs one-time
- Various entities -[:GENERATES]->(REVENUE)

**Query Pattern**: Join with REVENUE_TYPE for categorization
Example: Sum revenue by type through HAS_TYPE relationship

### New Support Entities

#### PERFORMANCE_METRIC
**Properties**: type (e.g., 'ROI'), value, unit
**Purpose**: Store calculated metrics for any entity
**Connected From**: MARKETING_CHANNEL, TEAM, PRODUCT via ACHIEVES

#### QUARTER
**Properties**: name (e.g., 'Q1'), year, full_name
**Purpose**: Standardized time periods
**Connected From**: PROJECTION, MILESTONE via FOR_PERIOD

#### REVENUE_TYPE
**Properties**: name ('recurring' or 'one-time')
**Purpose**: Categorize revenue streams
**Connected From**: REVENUE via HAS_TYPE

#### METRIC
**Properties**: type, value, confidence, unit
**Purpose**: Store any measurable value
**Connected From**: PROJECTION via PROJECTS

## Relationship-First Query Patterns

### Finding Metrics
Instead of: `WHERE node.roi = ?`
Use: `MATCH (node)-[:ACHIEVES]->(metric:PERFORMANCE_METRIC {type: 'ROI'})`

### Time-Based Queries
Instead of: `WHERE node.quarter = 'Q1 2025'`
Use: `MATCH (node)-[:FOR_PERIOD]->(q:QUARTER {name: 'Q1', year: 2025})`

### Categorization
Instead of: `WHERE node.source = 'recurring'`
Use: `MATCH (node)-[:HAS_TYPE]->(type:REVENUE_TYPE {name: 'recurring'})`

### Aggregations
Instead of: Complex property parsing
Use: Follow relationships and aggregate connected nodes

## Complete Entity Inventory (Partial Update)

### Customer & Business Entities
[Previous content remains for non-migrated entities...]

### Financial Entities (Updated)

#### REVENUE
Properties: amount, period
Relationships:
- (REVENUE)-[:HAS_TYPE]->(REVENUE_TYPE)
- Various entities -[:GENERATES]->(REVENUE)

#### COST
Properties: amount, type, period
Relationships:
- Various entities -[:HAS_COST]->(COST)
- (COST)-[:INCURRED_BY]->(various entities)

#### MARKETING_CHANNEL
Properties: name
Relationships:
- (MARKETING_CHANNEL)-[:HAS_COST]->(COST)
- (MARKETING_CHANNEL)-[:GENERATES]->(REVENUE)
- (MARKETING_CHANNEL)-[:ACHIEVES]->(PERFORMANCE_METRIC)

#### PROJECTION
Properties: name
Relationships:
- (PROJECTION)-[:FOR_PERIOD]->(QUARTER)
- (PROJECTION)-[:PROJECTS]->(METRIC)

## Query Generation Guidelines

1. **Think in Paths**: Every question is a graph traversal
2. **Follow Relationships**: Data lives at the end of edges
3. **Simple Matches**: Start with entity, traverse to data
4. **Avoid Property Assumptions**: Properties are minimal identifiers

## Common Anti-Patterns to Avoid
❌ Looking for complex properties on nodes
❌ String parsing for temporal data
❌ Assuming calculated values are properties
❌ Trying to filter on non-existent properties

## Preferred Patterns
✓ Traverse relationships to find data
✓ Match on relationship types
✓ Aggregate across connected nodes
✓ Use relationship properties for context

## Migration Status
- ✅ MARKETING_CHANNEL: Fully relationship-centric
- ✅ PROJECTION: Fully relationship-centric  
- ✅ REVENUE: Type moved to relationships
- 🔄 Other entities: Property-centric (for now)

Note: System is in transition. Some entities use properties, others use relationships. Check migration status when querying.
"""

# Enhanced query hints for relationship model
QUERY_CONTEXT_HINTS = {
    "marketing": "MARKETING_CHANNEL connects to metrics via relationships. Use -[:ACHIEVES]->PERFORMANCE_METRIC for ROI.",
    "roi": "ROI is stored in PERFORMANCE_METRIC nodes. Traverse via ACHIEVES relationship.",
    "projection": "PROJECTION connects to QUARTER via FOR_PERIOD and to values via PROJECTS relationships.",
    "quarter": "Quarters are separate QUARTER nodes. Match through FOR_PERIOD relationship.",
    "revenue type": "Revenue types are REVENUE_TYPE nodes connected via HAS_TYPE relationship.",
    "percentage": "For percentages, aggregate connected nodes rather than looking for properties.",
    "cost": "Costs are separate COST nodes. Follow HAS_COST relationships.",
    "metric": "Metrics are in METRIC or PERFORMANCE_METRIC nodes. Follow ACHIEVES or PROJECTS relationships."
}