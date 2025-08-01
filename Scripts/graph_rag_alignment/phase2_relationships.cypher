// Phase 2: Relationship Model Enhancement for SpyroSolutions Graph RAG
// This script creates relationships between the new entities

// ========================================
// STEP 1: Customer-Subscription Relationships
// ========================================

// Connect customers to their subscriptions
MATCH (c:Customer {name: "Disney"})
MATCH (s:Subscription {customer_id: "Disney"})
CREATE (c)-[r:HAS_SUBSCRIPTION {
    since: date("2023-01-01"),
    value: 1500000,
    discount_percentage: 10,
    payment_terms: "NET-30",
    created_at: datetime()
}]->(s);

MATCH (c:Customer {name: "EA"})
MATCH (s:Subscription {customer_id: "EA"})
CREATE (c)-[r:HAS_SUBSCRIPTION {
    since: date("2023-03-01"),
    value: 1200000,
    discount_percentage: 15,
    payment_terms: "NET-45",
    created_at: datetime()
}]->(s);

MATCH (c:Customer {name: "Netflix"})
MATCH (s:Subscription {customer_id: "Netflix"})
CREATE (c)-[r:HAS_SUBSCRIPTION {
    since: date("2022-06-01"),
    value: 1800000,
    discount_percentage: 5,
    payment_terms: "NET-30",
    created_at: datetime()
}]->(s);

// ========================================
// STEP 2: Subscription-Product Relationships
// ========================================

// Connect subscriptions to products they include
MATCH (s:Subscription {customer_id: "Disney"})
MATCH (p:Product {name: "SpyroSuite"})
CREATE (s)-[r:INCLUDES_PRODUCT {
    units: 500,
    price_per_unit: 200,
    created_at: datetime()
}]->(p);

MATCH (s:Subscription {customer_id: "Disney"})
MATCH (p:Product {name: "SpyroAnalytics"})
CREATE (s)-[r:INCLUDES_PRODUCT {
    units: 300,
    price_per_unit: 100,
    created_at: datetime()
}]->(p);

MATCH (s:Subscription {customer_id: "EA"})
MATCH (p:Product {name: "SpyroSuite"})
CREATE (s)-[r:INCLUDES_PRODUCT {
    units: 400,
    price_per_unit: 200,
    created_at: datetime()
}]->(p);

MATCH (s:Subscription {customer_id: "Netflix"})
MATCH (p:Product {name: "SpyroAnalytics"})
CREATE (s)-[r:INCLUDES_PRODUCT {
    units: 600,
    price_per_unit: 250,
    created_at: datetime()
}]->(p);

// ========================================
// STEP 3: Customer-Project Relationships
// ========================================

MATCH (c:Customer {name: "Disney"})
MATCH (p:Project {customer_id: "Disney"})
CREATE (c)-[r:HAS_PROJECT {
    priority: "HIGH",
    business_impact: "Critical",
    created_at: datetime()
}]->(p);

MATCH (c:Customer {name: "EA"})
MATCH (p:Project {customer_id: "EA"})
CREATE (c)-[r:HAS_PROJECT {
    priority: "MEDIUM",
    business_impact: "Moderate",
    created_at: datetime()
}]->(p);

// ========================================
// STEP 4: Team-Project Relationships
// ========================================

MATCH (t:Team {name: "Platform Team"})
MATCH (p:Project {team_id: "platform-team"})
CREATE (t)-[r:WORKS_ON {
    allocation_percentage: 60,
    start_date: date("2025-01-01"),
    created_at: datetime()
}]->(p);

MATCH (t:Team {name: "Integration Team"})
MATCH (p:Project {team_id: "integration-team"})
CREATE (t)-[r:WORKS_ON {
    allocation_percentage: 75,
    start_date: date("2025-02-01"),
    created_at: datetime()
}]->(p);

// ========================================
// STEP 5: Product-Team Relationships
// ========================================

MATCH (p:Product {name: "SpyroSuite"})
MATCH (t:Team {name: "Platform Team"})
CREATE (p)-[r:MANAGED_BY {
    since: date("2022-01-01"),
    ownership_percentage: 100,
    created_at: datetime()
}]->(t);

MATCH (p:Product {name: "SpyroAnalytics"})
MATCH (t:Team {name: "Analytics Team"})
CREATE (p)-[r:MANAGED_BY {
    since: date("2022-06-01"),
    ownership_percentage: 100,
    created_at: datetime()
}]->(t);

MATCH (p:Product {name: "SpyroAPI"})
MATCH (t:Team {name: "Integration Team"})
CREATE (p)-[r:MANAGED_BY {
    since: date("2023-01-01"),
    ownership_percentage: 100,
    created_at: datetime()
}]->(t);

// ========================================
// STEP 6: Customer-Event Relationships
// ========================================

MATCH (c:Customer {name: "Disney"})
MATCH (e:Event {customer_id: "Disney"})
CREATE (c)-[r:AFFECTED_BY {
    severity: "HIGH",
    business_impact: "Revenue at risk",
    created_at: datetime()
}]->(e);

MATCH (c:Customer {name: "EA"})
MATCH (e:Event {customer_id: "EA"})
CREATE (c)-[r:AFFECTED_BY {
    severity: "MEDIUM",
    business_impact: "User experience degraded",
    created_at: datetime()
}]->(e);

// ========================================
// STEP 7: Event-CustomerSuccessScore Relationships
// ========================================

MATCH (e:Event {customer_id: "Disney"})
MATCH (css:CustomerSuccessScore {customer_id: "Disney"})
CREATE (e)-[r:IMPACTS {
    score_change: -10,
    impact_type: "negative",
    created_at: datetime()
}]->(css);

MATCH (e:Event {customer_id: "EA"})
MATCH (css:CustomerSuccessScore)
WHERE NOT EXISTS((css)<-[:IMPACTS]-(:Event))
CREATE (e)-[r:IMPACTS {
    score_change: -5,
    impact_type: "negative",
    created_at: datetime()
}]->(css);

// ========================================
// STEP 8: Product-SLA Relationships
// ========================================

MATCH (p:Product)
WHERE p.name IN ["SpyroSuite", "SpyroAnalytics"]
MATCH (sla:SLA {id: "sla-enterprise-standard"})
CREATE (p)-[r:HAS_SLA {
    tier: "Enterprise",
    effective_date: date("2023-01-01"),
    created_at: datetime()
}]->(sla);

// ========================================
// STEP 9: Product-OperationalCost Relationships
// ========================================

MATCH (p:Product {name: "SpyroSuite"})
MATCH (cost:OperationalCost {product_name: "SpyroSuite"})
CREATE (p)-[r:INCURS {
    cost_type: "infrastructure",
    allocation: 1.0,
    created_at: datetime()
}]->(cost);

MATCH (p:Product {name: "SpyroAnalytics"})
MATCH (cost:OperationalCost {product_name: "SpyroAnalytics"})
CREATE (p)-[r:INCURS {
    cost_type: "infrastructure",
    allocation: 1.0,
    created_at: datetime()
}]->(cost);

// ========================================
// STEP 10: Customer-CustomerSuccessScore Relationships
// ========================================

MATCH (c:Customer {name: "Disney"})
MATCH (css:CustomerSuccessScore {customer_id: "Disney"})
CREATE (c)-[r:HAS_SUCCESS_SCORE {
    current: true,
    calculated_date: date("2025-07-31"),
    created_at: datetime()
}]->(css);

MATCH (c:Customer {name: "Netflix"})
MATCH (css:CustomerSuccessScore {customer_id: "Netflix"})
CREATE (c)-[r:HAS_SUCCESS_SCORE {
    current: true,
    calculated_date: date("2025-07-31"),
    created_at: datetime()
}]->(css);

// ========================================
// STEP 11: Risk-CompanyObjective Relationships
// ========================================

MATCH (r:Risk {description: "SLA violations"})
MATCH (obj:CompanyObjective {id: "obj-2025-customer-retention"})
CREATE (r)-[rel:THREATENS {
    impact_level: "HIGH",
    mitigation_priority: "Critical",
    created_at: datetime()
}]->(obj);

MATCH (r:Risk {name: "customer churn"})
MATCH (obj:CompanyObjective {id: "obj-2025-arr-growth"})
CREATE (r)-[rel:THREATENS {
    impact_level: "CRITICAL",
    mitigation_priority: "Critical",
    created_at: datetime()
}]->(obj);

// ========================================
// STEP 12: Product-Roadmap Relationships
// ========================================

MATCH (p:Product)
WHERE p.name IN ["SpyroSuite", "SpyroAnalytics"]
MATCH (r:Roadmap {quarter: "Q1 2025"})
CREATE (p)-[rel:IN_ROADMAP {
    priority: "HIGH",
    feature_count: 2,
    created_at: datetime()
}]->(r);

// ========================================
// STEP 13: Project-Roadmap Relationships
// ========================================

MATCH (p:Project)
MATCH (r:Roadmap {quarter: "Q1 2025"})
CREATE (p)-[rel:DELIVERS_FEATURES_FOR {
    alignment: "Direct",
    created_at: datetime()
}]->(r);

// ========================================
// STEP 14: Subscription-ARR Relationship (Virtual)
// ========================================

// Create ARR node if not exists
MERGE (arr:Metric:Entity {name: "Annual Recurring Revenue"})
ON CREATE SET 
    arr.entity_type = "Metric",
    arr.type = "financial",
    arr.unit = "USD",
    arr.current_value = 4500000,
    arr.target_value = 10000000,
    arr.created_at = datetime(),
    arr.updated_at = datetime();

MATCH (s:Subscription)
MATCH (arr:Metric {name: "Annual Recurring Revenue"})
CREATE (s)-[r:CONTRIBUTES_TO {
    amount: s.arr,
    percentage: toFloat(s.arr) / 4500000.0 * 100,
    created_at: datetime()
}]->(arr);

// ========================================
// Summary of created relationships
// ========================================

MATCH ()-[r]->()
WHERE r.created_at > datetime() - duration('PT5M')
RETURN type(r) as RelationshipType, count(r) as Count
ORDER BY Count DESC;