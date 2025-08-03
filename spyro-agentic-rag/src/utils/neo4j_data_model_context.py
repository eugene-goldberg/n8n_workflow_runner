"""
Neo4j Data Model Context for Agentic RAG
This provides comprehensive knowledge about the actual data structure
to enable autonomous, informed decision-making by the agent.
"""

DATA_MODEL_CONTEXT = """
# Neo4j Knowledge Graph Data Model

## Core Philosophy
- All entities follow LlamaIndex labeling: labels include both '__Entity__' and the specific type (e.g., 'CUSTOMER')
- Many attributes are stored as separate nodes rather than properties (e.g., SUBSCRIPTION, CUSTOMER_SUCCESS_SCORE)
- Financial values often stored as strings with '$' and 'M' suffixes requiring parsing
- Relationships connect entities in specific patterns - understanding these is crucial

## Primary Entity Types

### CUSTOMER (46 nodes)
Key Properties:
- name: Customer name (e.g., "TechCorp", "FinanceHub")
- industry: Industry sector
- size: Company size category
- region: Geographic location

Common Relationships:
- (CUSTOMER)-[:USES]->(PRODUCT) - Products the customer uses
- (CUSTOMER)-[:SUBSCRIBES_TO]->(SUBSCRIPTION) - Active subscriptions
- (CUSTOMER)-[:HAS_SUCCESS_SCORE]->(CUSTOMER_SUCCESS_SCORE) - Success metrics
- (CUSTOMER)-[:HAS_RISK]->(RISK) - Associated risks
- (CUSTOMER)-[:HAS_CONCERN]->(CONCERN) - Customer concerns

### SUBSCRIPTION (19 nodes)
Key Properties:
- value: Subscription value as string (e.g., "$8M", "$2.5M")
- status: Subscription status (e.g., "Active")
- start_date, end_date: Contract dates
- renewal_probability: Likelihood of renewal (0.0-1.0)

Note: Subscription values are separate nodes, not customer properties

### PRODUCT (37 nodes)
Key Properties:
- name: Product name (e.g., "SpyroCloud", "SpyroAI", "SpyroSecure")
- category: Product category
- version: Product version

Common Relationships:
- (PRODUCT)<-[:USES]-(CUSTOMER) - Customers using this product
- (PRODUCT)-[:OFFERS_FEATURE]->(FEATURE) - Product features
- (PRODUCT)-[:GENERATES_REVENUE]->(REVENUE) - Revenue generation

### RISK (76 nodes)
Key Properties:
- status: Risk status ("active", "monitoring", "mitigated") - NOT "Unmitigated"
- impact_amount: Financial impact as number (e.g., 2000000.0) - NOT "potential_impact"
- severity: Risk severity level ("high", "critical", "medium")
- description: Risk description
- probability: Risk probability

### TEAM (31 nodes)
Key Properties:
- name: Team name
- operational_cost: Only some teams have this (notably Security Team)
- monthly_cost: More common cost metric
- efficiency_ratio: Team efficiency metric
- revenue_supported: Revenue the team supports
Note: No "output" property - use efficiency_ratio or revenue_supported

### FEATURE (105 nodes)
Key Properties:
- name: Feature name
- adoption_rate: Percentage adoption (e.g., 85.5)
- is_new_feature: Boolean flag
- active_users: Number of active users
Note: Satisfaction scores are separate SATISFACTION_SCORE nodes, not feature properties

### CUSTOMER_SUCCESS_SCORE (15 nodes)
Key Properties:
- score: Success score value (0-100)
- trend: Score trend ("improving", "declining", "stable")
- customerId: Associated customer ID

### REVENUE (44 nodes)
Key Properties:
- amount: Revenue amount
- period: Time period
- source: Revenue source

### COST (67 nodes)
Key Properties:
- amount: Cost amount
- category: Cost category
- period: Time period

### EVENT (22 nodes)
Key Properties:
- type: Event type (e.g., "support_escalation", "payment_delay")
- date: Event date (Note: Many events lack dates)
- description: Event description

## Key Patterns for Calculations

### Calculating ARR (Annual Recurring Revenue)
- Sum subscription values from (CUSTOMER)-[:SUBSCRIBES_TO]->(SUBSCRIPTION)
- Parse string values: "$8M" = 8000000

### Finding At-Risk Revenue
- Active risks: status = 'active' (not 'Unmitigated')
- Financial impact: use impact_amount property

### Customer Retention
- No direct "retained" property on relationships
- Calculate from subscription status and renewal_probability
- Consider customer success scores and trends

### Product Adoption vs Satisfaction
- Features have adoption_rate property
- Satisfaction is in separate SATISFACTION_SCORE nodes
- No direct link between features and satisfaction

## Common Query Patterns

1. When looking for financial metrics, check both direct properties and separate nodes
2. Always use OPTIONAL MATCH for relationships that might not exist
3. Parse string financial values with CASE statements
4. Use property IS NOT NULL instead of EXISTS(property) syntax
5. Entity labels are usually uppercase (CUSTOMER not Customer)
6. For time-based queries, check if date properties actually exist

## Data Coverage Notes
- Not all customers have success scores
- Not all events have dates
- Only Security Team has operational_cost; others use monthly_cost
- Features have adoption rates but satisfaction scores are separate
- Many expected relationships don't exist - always verify with OPTIONAL MATCH
"""

# Additional context for specific query types
QUERY_CONTEXT_HINTS = {
    "financial": "Financial values are often strings with '$' and 'M' - parse them. Check REVENUE, COST, SUBSCRIPTION nodes.",
    "risk": "Risks use 'active' status, not 'Unmitigated'. Use impact_amount, not potential_impact.",
    "retention": "No direct retention data. Calculate from subscription status, renewal_probability, and success scores.",
    "features": "Feature satisfaction is in separate SATISFACTION_SCORE nodes, not feature properties.",
    "projections": "No pre-calculated projections. Calculate from current values and trends.",
    "issues": "Check EVENT nodes with type='support_escalation'. Many lack resolution dates.",
    "teams": "Most teams use monthly_cost, not operational_cost. Use efficiency_ratio for productivity."
}