// Phase 3: Data Migration for SpyroSolutions Graph RAG
// Transform existing data to work with new semantic model

// ========================================
// STEP 1: Create Risk Events from existing Risks
// ========================================

// Transform SLA violation risks into events
MATCH (c:Customer)-[:HAS_RISK]->(r:Risk)
WHERE r.description CONTAINS "SLA" OR r.name CONTAINS "SLA"
CREATE (e:Event:Entity {
    id: "event-" + c.name + "-sla-" + toString(timestamp()),
    entity_type: "Event",
    type: "SLA_breach",
    customer_id: c.name,
    timestamp: datetime() - duration({days: toInteger(rand() * 30)}),
    impact: CASE WHEN r.impact = "high" THEN "HIGH" ELSE "MEDIUM" END,
    description: r.description,
    affected_metric: "uptime",
    metric_value: 99.2 - (rand() * 0.5),
    duration_minutes: toInteger(rand() * 120 + 30),
    affected_success_score: CASE WHEN r.severity > 5 THEN -10 ELSE -5 END,
    resolution_time_minutes: toInteger(rand() * 240 + 60),
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (c)-[rel:AFFECTED_BY {
    severity: r.impact,
    business_impact: "Service disruption",
    created_at: datetime()
}]->(e);

// Transform performance risks into events
MATCH (c:Customer)-[:HAS_RISK]->(r:Risk)
WHERE r.description CONTAINS "performance" OR r.name CONTAINS "performance"
CREATE (e:Event:Entity {
    id: "event-" + c.name + "-perf-" + toString(timestamp()),
    entity_type: "Event",
    type: "performance_degradation",
    customer_id: c.name,
    timestamp: datetime() - duration({days: toInteger(rand() * 30)}),
    impact: CASE WHEN r.impact = "high" THEN "HIGH" ELSE "MEDIUM" END,
    description: r.description,
    affected_metric: "response_time",
    metric_value: 500 + toInteger(rand() * 500),
    duration_minutes: toInteger(rand() * 180 + 60),
    affected_success_score: CASE WHEN r.severity > 5 THEN -8 ELSE -4 END,
    resolution_time_minutes: toInteger(rand() * 360 + 120),
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (c)-[rel:AFFECTED_BY {
    severity: r.impact,
    business_impact: "User experience impact",
    created_at: datetime()
}]->(e);

// ========================================
// STEP 2: Generate Customer Success Scores for remaining customers
// ========================================

// Create scores for customers without them
MATCH (c:Customer)
WHERE NOT EXISTS((c)-[:HAS_SUCCESS_SCORE]->())
WITH c, 
     CASE 
         WHEN c.tier = "Enterprise" THEN 85 + toInteger(rand() * 10)
         WHEN c.tier = "Pro" THEN 75 + toInteger(rand() * 15)
         ELSE 65 + toInteger(rand() * 20)
     END as base_score,
     CASE
         WHEN EXISTS((c)-[:HAS_RISK]->()) THEN -10
         ELSE 0
     END as risk_penalty
CREATE (css:CustomerSuccessScore:Entity {
    id: "css-" + c.name + "-2025-07",
    entity_type: "CustomerSuccessScore",
    customer_id: c.name,
    score: base_score + risk_penalty,
    previous_score: base_score + risk_penalty + toInteger(rand() * 10 - 5),
    trend: CASE 
        WHEN rand() > 0.5 THEN "improving" 
        WHEN rand() > 0.3 THEN "stable"
        ELSE "declining" 
    END,
    factor_product_usage: 70 + toInteger(rand() * 30),
    factor_support_tickets: 60 + toInteger(rand() * 40),
    factor_feature_adoption: 65 + toInteger(rand() * 35),
    factor_sla_compliance: 80 + toInteger(rand() * 20),
    factor_payment_history: 90 + toInteger(rand() * 10),
    calculated_date: date("2025-07-31"),
    risk_level: CASE 
        WHEN base_score + risk_penalty < 70 THEN "HIGH"
        WHEN base_score + risk_penalty < 85 THEN "MEDIUM"
        ELSE "LOW"
    END,
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (c)-[r:HAS_SUCCESS_SCORE {
    current: true,
    calculated_date: date("2025-07-31"),
    created_at: datetime()
}]->(css);

// ========================================
// STEP 3: Create Subscriptions for remaining customers
// ========================================

MATCH (c:Customer)
WHERE NOT EXISTS((c)-[:HAS_SUBSCRIPTION]->())
WITH c,
     CASE 
         WHEN c.tier = "Enterprise" THEN 50000 + toInteger(rand() * 50000)
         WHEN c.tier = "Pro" THEN 20000 + toInteger(rand() * 30000)
         ELSE 5000 + toInteger(rand() * 15000)
     END as monthly_revenue
CREATE (s:Subscription:Entity {
    id: "sub-" + c.name + "-001",
    entity_type: "Subscription",
    type: "SaaS " + c.tier,
    customer_id: c.name,
    mrr: monthly_revenue,
    arr: monthly_revenue * 12,
    start_date: date("2023-01-01") + duration({months: toInteger(rand() * 24)}),
    renewal_date: date("2025-01-01") + duration({months: toInteger(rand() * 12)}),
    contract_length_months: CASE WHEN c.tier = "Enterprise" THEN 24 ELSE 12 END,
    status: CASE 
        WHEN EXISTS((c)-[:HAS_RISK]->()) THEN "at_risk"
        ELSE "active"
    END,
    discount_percentage: CASE 
        WHEN c.tier = "Enterprise" THEN toInteger(rand() * 20)
        ELSE toInteger(rand() * 10)
    END,
    payment_terms: CASE 
        WHEN c.tier = "Enterprise" THEN "NET-30"
        ELSE "NET-15"
    END,
    auto_renewal: c.tier = "Enterprise",
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (c)-[r:HAS_SUBSCRIPTION {
    since: s.start_date,
    value: s.arr,
    discount_percentage: s.discount_percentage,
    payment_terms: s.payment_terms,
    created_at: datetime()
}]->(s);

// ========================================
// STEP 4: Connect Subscriptions to Products
// ========================================

// Connect new subscriptions to products based on customer tier
MATCH (s:Subscription)
WHERE NOT EXISTS((s)-[:INCLUDES_PRODUCT]->())
WITH s
MATCH (c:Customer {name: s.customer_id})
MATCH (p:Product)
WHERE (c.tier = "Enterprise" AND p.name IN ["SpyroSuite", "SpyroAnalytics"]) OR
      (c.tier = "Pro" AND p.name = "SpyroSuite") OR
      (c.tier <> "Enterprise" AND c.tier <> "Pro" AND p.name = "SpyroCloud")
CREATE (s)-[r:INCLUDES_PRODUCT {
    units: CASE 
        WHEN c.tier = "Enterprise" THEN 100 + toInteger(rand() * 400)
        WHEN c.tier = "Pro" THEN 50 + toInteger(rand() * 150)
        ELSE 10 + toInteger(rand() * 40)
    END,
    price_per_unit: CASE 
        WHEN p.name = "SpyroAnalytics" THEN 200
        WHEN p.name = "SpyroSuite" THEN 150
        ELSE 100
    END,
    created_at: datetime()
}]->(p);

// ========================================
// STEP 5: Create Projects for high-value customers
// ========================================

MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(s:Subscription)
WHERE s.arr > 500000 AND NOT EXISTS((c)-[:HAS_PROJECT]->())
CREATE (p:Project:Entity {
    id: "proj-" + c.name + "-2025-q1",
    entity_type: "Project",
    name: "Q1 2025 Enhancement - " + c.name,
    customer_id: c.name,
    features: ["Custom Dashboard", "API Enhancement", "Performance Optimization"],
    status: CASE 
        WHEN rand() > 0.7 THEN "at_risk"
        WHEN rand() > 0.3 THEN "on_track"
        ELSE "ahead"
    END,
    start_date: date("2025-01-01"),
    due_date: date("2025-03-31"),
    completion_percentage: toInteger(rand() * 70 + 10),
    team_id: CASE 
        WHEN rand() > 0.5 THEN "platform-team"
        ELSE "analytics-team"
    END,
    priority: CASE 
        WHEN s.arr > 1000000 THEN "HIGH"
        ELSE "MEDIUM"
    END,
    estimated_hours: 800 + toInteger(rand() * 1600),
    actual_hours: toInteger(rand() * 800),
    created_at: datetime(),
    updated_at: datetime()
})
CREATE (c)-[r:HAS_PROJECT {
    priority: p.priority,
    business_impact: "Strategic",
    created_at: datetime()
}]->(p);

// ========================================
// STEP 6: Update ARR metric with all subscriptions
// ========================================

MATCH (arr:Metric {name: "Annual Recurring Revenue"})
MATCH (s:Subscription)
WITH arr, sum(s.arr) as total_arr
SET arr.current_value = total_arr,
    arr.updated_at = datetime();

// Re-create contribution relationships with updated percentages
MATCH (s:Subscription)
MATCH (arr:Metric {name: "Annual Recurring Revenue"})
MATCH (s)-[old:CONTRIBUTES_TO]->(arr)
DELETE old;

MATCH (s:Subscription)
MATCH (arr:Metric {name: "Annual Recurring Revenue"})
CREATE (s)-[r:CONTRIBUTES_TO {
    amount: s.arr,
    percentage: toFloat(s.arr) / toFloat(arr.current_value) * 100,
    created_at: datetime()
}]->(arr);

// ========================================
// STEP 7: Summary of migration
// ========================================

MATCH (n)
WHERE n.created_at > datetime() - duration('PT10M')
RETURN labels(n)[0] as EntityType, count(n) as NewEntities
ORDER BY NewEntities DESC
UNION
MATCH ()-[r]->()
WHERE r.created_at > datetime() - duration('PT10M')
RETURN type(r) as EntityType, count(r) as NewEntities
ORDER BY NewEntities DESC;