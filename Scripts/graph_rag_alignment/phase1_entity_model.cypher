// Phase 1: Entity Model Enhancement for SpyroSolutions Graph RAG
// This script creates new entity types and constraints to align with the semantic model

// ========================================
// STEP 1: Create Constraints and Indexes
// ========================================

// Subscription entities
CREATE CONSTRAINT subscription_id IF NOT EXISTS 
FOR (s:Subscription) REQUIRE s.id IS UNIQUE;

CREATE INDEX subscription_customer IF NOT EXISTS
FOR (s:Subscription) ON (s.customer_id);

CREATE INDEX subscription_status IF NOT EXISTS
FOR (s:Subscription) ON (s.status);

// Project entities  
CREATE CONSTRAINT project_id IF NOT EXISTS
FOR (p:Project) REQUIRE p.id IS UNIQUE;

CREATE INDEX project_status IF NOT EXISTS
FOR (p:Project) ON (p.status);

CREATE INDEX project_customer IF NOT EXISTS
FOR (p:Project) ON (p.customer_id);

// Team entities
CREATE CONSTRAINT team_name IF NOT EXISTS
FOR (t:Team) REQUIRE t.name IS UNIQUE;

// Event entities
CREATE CONSTRAINT event_id IF NOT EXISTS
FOR (e:Event) REQUIRE e.id IS UNIQUE;

CREATE INDEX event_type IF NOT EXISTS
FOR (e:Event) ON (e.type);

CREATE INDEX event_customer IF NOT EXISTS
FOR (e:Event) ON (e.customer_id);

CREATE INDEX event_timestamp IF NOT EXISTS
FOR (e:Event) ON (e.timestamp);

// SLA entities
CREATE CONSTRAINT sla_id IF NOT EXISTS
FOR (s:SLA) REQUIRE s.id IS UNIQUE;

// Roadmap entities
CREATE CONSTRAINT roadmap_id IF NOT EXISTS
FOR (r:Roadmap) REQUIRE r.id IS UNIQUE;

// CustomerSuccessScore entities
CREATE CONSTRAINT css_id IF NOT EXISTS
FOR (c:CustomerSuccessScore) REQUIRE c.id IS UNIQUE;

// CompanyObjective entities
CREATE CONSTRAINT objective_id IF NOT EXISTS
FOR (o:CompanyObjective) REQUIRE o.id IS UNIQUE;

// OperationalCost entities
CREATE CONSTRAINT cost_id IF NOT EXISTS
FOR (c:OperationalCost) REQUIRE c.id IS UNIQUE;

// ========================================
// STEP 2: Create Sample Entities
// ========================================

// Create Subscription entities for existing customers
MATCH (c:Customer {name: "Disney"})
CREATE (s:Subscription:Entity {
    id: "sub-disney-001",
    entity_type: "Subscription",
    type: "SaaS Enterprise",
    customer_id: "Disney",
    mrr: 125000,
    arr: 1500000,
    start_date: date("2023-01-01"),
    renewal_date: date("2025-01-01"),
    contract_length_months: 24,
    status: "active",
    discount_percentage: 10,
    payment_terms: "NET-30",
    auto_renewal: true,
    created_at: datetime(),
    updated_at: datetime()
});

MATCH (c:Customer {name: "EA"})
CREATE (s:Subscription:Entity {
    id: "sub-ea-001",
    entity_type: "Subscription",
    type: "SaaS Enterprise",
    customer_id: "EA",
    mrr: 100000,
    arr: 1200000,
    start_date: date("2023-03-01"),
    renewal_date: date("2025-03-01"),
    contract_length_months: 24,
    status: "at_risk",
    discount_percentage: 15,
    payment_terms: "NET-45",
    auto_renewal: false,
    created_at: datetime(),
    updated_at: datetime()
});

MATCH (c:Customer {name: "Netflix"})
CREATE (s:Subscription:Entity {
    id: "sub-netflix-001",
    entity_type: "Subscription",
    type: "SaaS Enterprise",
    customer_id: "Netflix",
    mrr: 150000,
    arr: 1800000,
    start_date: date("2022-06-01"),
    renewal_date: date("2024-06-01"),
    contract_length_months: 24,
    status: "active",
    discount_percentage: 5,
    payment_terms: "NET-30",
    auto_renewal: true,
    created_at: datetime(),
    updated_at: datetime()
});

// Create Project entities
CREATE (p1:Project:Entity {
    id: "proj-disney-q1-2025",
    entity_type: "Project",
    name: "Q1 2025 Feature Delivery - Disney",
    customer_id: "Disney",
    features: ["Advanced Analytics Dashboard", "API v3", "Real-time Alerts"],
    status: "at_risk",
    start_date: date("2025-01-01"),
    due_date: date("2025-03-31"),
    completion_percentage: 45,
    team_id: "platform-team",
    priority: "HIGH",
    estimated_hours: 2400,
    actual_hours: 1100,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (p2:Project:Entity {
    id: "proj-ea-integration-2025",
    entity_type: "Project",
    name: "EA Custom Integration",
    customer_id: "EA",
    features: ["Game Analytics Integration", "Custom Reporting"],
    status: "on_track",
    start_date: date("2025-02-01"),
    due_date: date("2025-04-30"),
    completion_percentage: 30,
    team_id: "integration-team",
    priority: "MEDIUM",
    estimated_hours: 1200,
    actual_hours: 360,
    created_at: datetime(),
    updated_at: datetime()
});

// Create Team entities
CREATE (t1:Team:Entity {
    name: "Platform Team",
    entity_type: "Team",
    size: 25,
    lead: "John Smith",
    capacity_utilization: 0.85,
    specialization: "Core Platform Development",
    location: "San Francisco",
    avg_tenure_years: 3.5,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (t2:Team:Entity {
    name: "Integration Team",
    entity_type: "Team",
    size: 15,
    lead: "Sarah Johnson",
    capacity_utilization: 0.75,
    specialization: "Customer Integrations",
    location: "Austin",
    avg_tenure_years: 2.8,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (t3:Team:Entity {
    name: "Analytics Team",
    entity_type: "Team",
    size: 20,
    lead: "Mike Chen",
    capacity_utilization: 0.90,
    specialization: "Analytics and ML",
    location: "Seattle",
    avg_tenure_years: 4.2,
    created_at: datetime(),
    updated_at: datetime()
});

// Create Event entities
CREATE (e1:Event:Entity {
    id: "event-disney-sla-001",
    entity_type: "Event",
    type: "SLA_breach",
    customer_id: "Disney",
    timestamp: datetime("2025-07-15T14:30:00Z"),
    impact: "HIGH",
    description: "Uptime fell below 99.5% SLA requirement",
    affected_metric: "uptime",
    metric_value: 99.2,
    duration_minutes: 45,
    affected_success_score: -10,
    resolution_time_minutes: 120,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (e2:Event:Entity {
    id: "event-ea-perf-001",
    entity_type: "Event",
    type: "performance_degradation",
    customer_id: "EA",
    timestamp: datetime("2025-07-20T08:15:00Z"),
    impact: "MEDIUM",
    description: "API response times increased during peak hours",
    affected_metric: "response_time",
    metric_value: 850,
    duration_minutes: 180,
    affected_success_score: -5,
    resolution_time_minutes: 240,
    created_at: datetime(),
    updated_at: datetime()
});

// Create SLA entities
CREATE (sla1:SLA:Entity {
    id: "sla-enterprise-standard",
    entity_type: "SLA",
    name: "Enterprise Standard SLA",
    uptime_percentage: 99.5,
    response_time_ms: 500,
    support_response_hours: 4,
    severity_levels: ["Critical", "High", "Medium", "Low"],
    penalty_uptime_breach: "10% monthly credit",
    penalty_response_time_breach: "5% monthly credit",
    measurement_period: "monthly",
    created_at: datetime(),
    updated_at: datetime()
});

// Create CustomerSuccessScore entities
CREATE (css1:CustomerSuccessScore:Entity {
    id: "css-disney-2025-07",
    entity_type: "CustomerSuccessScore",
    customer_id: "Disney",
    score: 78,
    previous_score: 88,
    trend: "declining",
    factor_product_usage: 85,
    factor_support_tickets: 60,
    factor_feature_adoption: 90,
    factor_sla_compliance: 70,
    factor_payment_history: 100,
    calculated_date: date("2025-07-31"),
    risk_level: "HIGH",
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (css2:CustomerSuccessScore:Entity {
    id: "css-netflix-2025-07",
    entity_type: "CustomerSuccessScore",
    customer_id: "Netflix",
    score: 92,
    previous_score: 90,
    trend: "improving",
    factor_product_usage: 95,
    factor_support_tickets: 90,
    factor_feature_adoption: 88,
    factor_sla_compliance: 100,
    factor_payment_history: 100,
    calculated_date: date("2025-07-31"),
    risk_level: "LOW",
    created_at: datetime(),
    updated_at: datetime()
});

// Create CompanyObjective entities
CREATE (obj1:CompanyObjective:Entity {
    id: "obj-2025-arr-growth",
    entity_type: "CompanyObjective",
    name: "ARR Growth Target",
    description: "Achieve $10M ARR by end of 2025",
    target_value: 10000000,
    current_value: 7500000,
    unit: "USD",
    due_date: date("2025-12-31"),
    status: "on_track",
    priority: "CRITICAL",
    owner: "CEO",
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (obj2:CompanyObjective:Entity {
    id: "obj-2025-customer-retention",
    entity_type: "CompanyObjective",
    name: "Customer Retention",
    description: "Maintain 95% customer retention rate",
    target_value: 95,
    current_value: 92,
    unit: "percentage",
    due_date: date("2025-12-31"),
    status: "at_risk",
    priority: "HIGH",
    owner: "VP Customer Success",
    created_at: datetime(),
    updated_at: datetime()
});

// Create OperationalCost entities
CREATE (cost1:OperationalCost:Entity {
    id: "cost-spyrosuite-2025",
    entity_type: "OperationalCost",
    product_name: "SpyroSuite",
    cost_type: "infrastructure",
    monthly_cost: 50000,
    annual_cost: 600000,
    cost_compute: 30000,
    cost_storage: 10000,
    cost_network: 5000,
    cost_licenses: 5000,
    currency: "USD",
    budget_allocated: 650000,
    variance_percentage: -7.7,
    created_at: datetime(),
    updated_at: datetime()
});

CREATE (cost2:OperationalCost:Entity {
    id: "cost-spyroanalytics-2025",
    entity_type: "OperationalCost",
    product_name: "SpyroAnalytics",
    cost_type: "infrastructure",
    monthly_cost: 35000,
    annual_cost: 420000,
    cost_compute: 25000,
    cost_storage: 5000,
    cost_network: 3000,
    cost_licenses: 2000,
    currency: "USD",
    budget_allocated: 400000,
    variance_percentage: 5.0,
    created_at: datetime(),
    updated_at: datetime()
});

// Create Roadmap entities
CREATE (r1:Roadmap:Entity {
    id: "roadmap-2025-q1",
    entity_type: "Roadmap",
    quarter: "Q1 2025",
    year: 2025,
    themes: ["Performance Optimization", "Enterprise Features", "Security Enhancements"],
    planned_features: ["Advanced Analytics Dashboard", "API v3", "Zero-downtime deployments", "Enhanced encryption"],
    feature_statuses: ["in_progress", "in_progress", "planned", "completed"],
    resource_platform_team: 0.6,
    resource_analytics_team: 0.3,
    resource_integration_team: 0.1,
    created_at: datetime(),
    updated_at: datetime()
});

// Summary
MATCH (n:Entity)
WHERE n.created_at > datetime() - duration('PT1M')
RETURN 
    n.entity_type as EntityType, 
    count(n) as Count
ORDER BY Count DESC;