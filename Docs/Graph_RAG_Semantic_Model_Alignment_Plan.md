# Graph RAG Semantic Model Alignment Plan

## Executive Summary

This plan outlines the steps to align our current Graph RAG implementation with the comprehensive semantic model for SpyroSolutions. The alignment will transform our basic entity-relationship structure into a rich SaaS business knowledge graph that captures customer lifecycle, product management, financial metrics, and operational data.

## Current State vs Target State

### Current Implementation
- **Entities**: Customer (5), Product (5), Risk (4), Tier (2), Metrics (1)
- **Relationships**: USES_PRODUCT, HAS_RISK, MITIGATED_BY
- **Scope**: Basic customer-product-risk associations

### Target Semantic Model
- **Core Entities**: Customer, Product, Risk, Subscription, Project, Team, Event, Metric
- **Financial Entities**: ARR, MRR, Profitability, Operational Cost
- **Operational Entities**: SLA, Roadmap, Customer Success Score, Company Objective
- **Relationships**: 15+ relationship types capturing complex business logic

## Implementation Phases

### Phase 1: Entity Model Enhancement (Week 1)

#### 1.1 Create New Entity Types
```cypher
// Subscription entities
CREATE CONSTRAINT subscription_id IF NOT EXISTS 
FOR (s:Subscription) REQUIRE s.id IS UNIQUE;

// Project entities  
CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE;

// Team entities
CREATE CONSTRAINT team_name IF NOT EXISTS
FOR (t:Team) REQUIRE t.name IS UNIQUE;

// Event entities
CREATE CONSTRAINT event_id IF NOT EXISTS
FOR (e:Event) REQUIRE e.id IS UNIQUE;

// SLA entities
CREATE CONSTRAINT sla_id IF NOT EXISTS
FOR (s:SLA) REQUIRE s.id IS UNIQUE;
```

#### 1.2 Entity Definitions

**Subscription Entity**
```json
{
  "id": "sub-001",
  "type": "SaaS",
  "customer_id": "Disney",
  "product_ids": ["SpyroSuite", "SpyroAnalytics"],
  "mrr": 125000,
  "arr": 1500000,
  "start_date": "2023-01-01",
  "renewal_date": "2025-01-01",
  "status": "active"
}
```

**Project Entity**
```json
{
  "id": "proj-001",
  "name": "Q1 2025 Feature Delivery",
  "customer_id": "Disney",
  "features": ["Advanced Analytics Dashboard", "API v3"],
  "status": "at_risk",
  "due_date": "2025-03-31",
  "team_id": "platform-team"
}
```

**Team Entity**
```json
{
  "name": "Platform Team",
  "size": 25,
  "products": ["SpyroSuite"],
  "lead": "John Smith",
  "capacity_utilization": 0.85
}
```

**Event Entity**
```json
{
  "id": "event-001",
  "type": "SLA_breach",
  "customer_id": "Disney",
  "timestamp": "2025-07-15T14:30:00Z",
  "impact": "high",
  "description": "Uptime fell below 99.5%",
  "affected_success_score": -10
}
```

### Phase 2: Relationship Model Enhancement (Week 1-2)

#### 2.1 New Relationship Types

1. **Customer Relationships**
   - Customer -[HAS_SUBSCRIPTION]-> Subscription
   - Customer -[HAS_SUCCESS_SCORE]-> Metric
   - Customer -[AFFECTED_BY]-> Event
   - Customer -[HAS_PROJECT]-> Project

2. **Product Relationships**
   - Product -[MANAGED_BY]-> Team
   - Product -[HAS_SLA]-> SLA
   - Product -[IN_ROADMAP]-> Roadmap
   - Product -[HAS_OPERATIONAL_COST]-> Cost

3. **Financial Relationships**
   - Subscription -[CONTRIBUTES_TO]-> ARR
   - Customer -[GENERATES]-> Profitability
   - Product -[INCURS]-> OperationalCost

4. **Operational Relationships**
   - Project -[DELIVERS_FEATURES]-> Customer
   - Event -[IMPACTS]-> CustomerSuccessScore
   - Risk -[THREATENS]-> CompanyObjective
   - Team -[WORKS_ON]-> Project

#### 2.2 Relationship Properties
```cypher
// Example: Customer-Subscription relationship with properties
MATCH (c:Customer {name: "Disney"})
MATCH (s:Subscription {id: "sub-001"})
CREATE (c)-[r:HAS_SUBSCRIPTION {
  since: date("2023-01-01"),
  value: 1500000,
  discount_percentage: 10,
  payment_terms: "NET-30"
}]->(s)
```

### Phase 3: Data Migration (Week 2)

#### 3.1 Create Migration Scripts
```python
# migration/create_subscriptions.py
def migrate_subscriptions():
    """Create subscription entities from existing customer data"""
    customers = get_all_customers()
    
    for customer in customers:
        subscription = {
            "id": f"sub-{customer.id}",
            "customer_id": customer.name,
            "mrr": customer.mrr,
            "arr": customer.mrr * 12,
            "products": get_customer_products(customer.name),
            "status": "active" if customer.revenue_at_risk == 0 else "at_risk"
        }
        create_subscription_entity(subscription)
```

#### 3.2 Create Events from Risk Data
```python
def create_risk_events():
    """Transform existing risks into event entities"""
    risk_mappings = {
        "SLA violations": "SLA_breach",
        "performance issues": "performance_degradation",
        "security concerns": "security_incident"
    }
    
    for customer in customers_with_risks:
        for risk in customer.risks:
            create_event({
                "type": risk_mappings[risk],
                "customer_id": customer.name,
                "impact": "high" if customer.risk_score > 7 else "medium"
            })
```

### Phase 4: Ingestion Pipeline Update (Week 2-3)

#### 4.1 Enhanced Entity Extraction
```python
# ingestion/entity_extractors.py
class EnhancedEntityExtractor:
    def extract_entities(self, text: str) -> List[Entity]:
        entities = []
        
        # Extract subscription mentions
        subscription_patterns = [
            r"(\$[\d,]+)\s*(?:ARR|annual)",
            r"subscription\s+(?:value|worth)\s+(\$[\d,]+)"
        ]
        
        # Extract project mentions
        project_patterns = [
            r"(Q\d\s+\d{4})\s+(?:features|deliverables)",
            r"project\s+(?:named?|called?)\s+([A-Z][\w\s]+)"
        ]
        
        # Extract team mentions
        team_patterns = [
            r"([A-Z][\w]+\s+[Tt]eam)",
            r"team\s+(?:of|with)\s+(\d+)\s+(?:people|members)"
        ]
        
        return entities
```

#### 4.2 Relationship Extraction Rules
```python
RELATIONSHIP_RULES = [
    {
        "pattern": r"(\w+) subscription worth \$?([\d,]+)",
        "rel_type": "HAS_SUBSCRIPTION",
        "source": "Customer",
        "target": "Subscription",
        "properties": ["value"]
    },
    {
        "pattern": r"(\w+ team) manages (\w+)",
        "rel_type": "MANAGES",
        "source": "Team",
        "target": "Product"
    },
    {
        "pattern": r"(\w+) affected by (\w+ event)",
        "rel_type": "AFFECTED_BY",
        "source": "Customer",
        "target": "Event"
    }
]
```

### Phase 5: Graph Queries Enhancement (Week 3)

#### 5.1 New Query Patterns
```python
# agent/graph_queries.py
async def get_customer_360_view(customer_name: str):
    """Complete customer view including all relationships"""
    query = """
    MATCH (c:Customer {name: $name})
    OPTIONAL MATCH (c)-[:HAS_SUBSCRIPTION]->(sub:Subscription)
    OPTIONAL MATCH (c)-[:HAS_PROJECT]->(proj:Project)
    OPTIONAL MATCH (c)-[:AFFECTED_BY]->(event:Event)
    OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(score:Metric)
    RETURN c, sub, collect(proj) as projects, 
           collect(event) as events, score
    """

async def get_product_operations(product_name: str):
    """Product operational view"""
    query = """
    MATCH (p:Product {name: $name})
    OPTIONAL MATCH (p)-[:MANAGED_BY]->(team:Team)
    OPTIONAL MATCH (p)-[:HAS_SLA]->(sla:SLA)
    OPTIONAL MATCH (p)-[:HAS_OPERATIONAL_COST]->(cost:Cost)
    RETURN p, team, sla, cost
    """

async def analyze_company_health():
    """Overall company health metrics"""
    query = """
    MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
    WITH sum(s.arr) as total_arr, count(c) as customer_count
    MATCH (r:Risk)<-[:HAS_RISK]-(c:Customer)
    WITH total_arr, customer_count, count(r) as active_risks
    MATCH (obj:CompanyObjective)
    RETURN total_arr, customer_count, active_risks, 
           collect(obj) as objectives
    """
```

### Phase 6: Testing and Validation (Week 3-4)

#### 6.1 Test Scenarios
1. **Customer 360 Query**: "Give me a complete view of Disney including subscription, projects, and recent events"
2. **Financial Analysis**: "What is our total ARR and which customers contribute most?"
3. **Risk Analysis**: "Which projects are at risk and how do they affect our company objectives?"
4. **Team Performance**: "Show me team utilization across all products"
5. **SLA Compliance**: "Which customers have SLA breaches in the last 30 days?"

#### 6.2 Validation Metrics
- Entity coverage: 100% of semantic model entities created
- Relationship coverage: All defined relationships implemented
- Query performance: <500ms for complex traversals
- Data quality: No orphaned nodes, all relationships bidirectional where appropriate

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| 1 | Entity Model | New entity types, constraints, sample data |
| 1-2 | Relationships | Relationship types, properties, connections |
| 2 | Data Migration | Migration scripts, data transformation |
| 2-3 | Pipeline Update | Enhanced extractors, ingestion rules |
| 3 | Query Enhancement | New query patterns, graph algorithms |
| 3-4 | Testing | Test execution, performance tuning |
| 4 | Documentation | Updated docs, query examples |

## Success Criteria

1. **Model Completeness**: All entities and relationships from semantic model implemented
2. **Data Quality**: 95%+ accuracy in entity extraction and relationship creation
3. **Query Coverage**: Support for all business-critical queries
4. **Performance**: Sub-second response for 90% of queries
5. **Tool Usage**: Graph search triggered appropriately for relationship queries

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data migration errors | High | Incremental migration with rollback capability |
| Performance degradation | Medium | Index optimization, query tuning |
| Extraction accuracy | Medium | ML model training, rule refinement |
| Breaking changes | High | Versioned API, backward compatibility |

## Next Steps

1. Review and approve plan
2. Set up development environment
3. Create entity type definitions
4. Begin Phase 1 implementation
5. Schedule weekly progress reviews

This alignment will transform our Graph RAG from a simple entity store to a comprehensive business intelligence knowledge graph.