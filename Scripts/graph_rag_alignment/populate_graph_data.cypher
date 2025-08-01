// Comprehensive Data Population for SpyroSolutions Graph RAG
// This script populates the Neo4j database with realistic SaaS business data

// ========================================
// STEP 1: Create Additional Customers if needed
// ========================================

// Ensure we have all 5 customers with proper tiers
MERGE (c1:Customer:Entity {name: "Disney"})
ON CREATE SET 
    c1.entity_type = "Customer",
    c1.tier = "Enterprise",
    c1.industry = "Entertainment",
    c1.employee_count = 195000,
    c1.founded_year = 1923,
    c1.headquarters = "Burbank, CA",
    c1.created_at = datetime(),
    c1.updated_at = datetime();

MERGE (c2:Customer:Entity {name: "EA"})
ON CREATE SET 
    c2.entity_type = "Customer",
    c2.tier = "Enterprise",
    c2.industry = "Gaming",
    c2.employee_count = 12900,
    c2.founded_year = 1982,
    c2.headquarters = "Redwood City, CA",
    c2.created_at = datetime(),
    c2.updated_at = datetime();

MERGE (c3:Customer:Entity {name: "Netflix"})
ON CREATE SET 
    c3.entity_type = "Customer",
    c3.tier = "Enterprise",
    c3.industry = "Streaming",
    c3.employee_count = 13000,
    c3.founded_year = 1997,
    c3.headquarters = "Los Gatos, CA",
    c3.created_at = datetime(),
    c3.updated_at = datetime();

MERGE (c4:Customer:Entity {name: "Spotify"})
ON CREATE SET 
    c4.entity_type = "Customer",
    c4.tier = "Pro",
    c4.industry = "Music Streaming",
    c4.employee_count = 9000,
    c4.founded_year = 2006,
    c4.headquarters = "Stockholm, Sweden",
    c4.created_at = datetime(),
    c4.updated_at = datetime();

MERGE (c5:Customer:Entity {name: "Nintendo"})
ON CREATE SET 
    c5.entity_type = "Customer",
    c5.tier = "Pro",
    c5.industry = "Gaming",
    c5.employee_count = 7000,
    c5.founded_year = 1889,
    c5.headquarters = "Kyoto, Japan",
    c5.created_at = datetime(),
    c5.updated_at = datetime();

// ========================================
// STEP 2: Create More Events
// ========================================

// Disney Events
MERGE (e1:Event:Entity {id: "event-disney-outage-001"})
ON CREATE SET
    e1.entity_type = "Event",
    e1.type = "service_outage",
    e1.customer_id = "Disney",
    e1.timestamp = datetime("2025-07-28T03:15:00Z"),
    e1.impact = "CRITICAL",
    e1.description = "Complete service outage affecting Disney+ integration",
    e1.affected_metric = "availability",
    e1.metric_value = 0,
    e1.duration_minutes = 35,
    e1.affected_success_score = -15,
    e1.resolution_time_minutes = 45,
    e1.root_cause = "Database connection pool exhaustion",
    e1.created_at = datetime(),
    e1.updated_at = datetime();

MERGE (e2:Event:Entity {id: "event-disney-data-001"})
ON CREATE SET
    e2.entity_type = "Event",
    e2.type = "data_quality_issue",
    e2.customer_id = "Disney",
    e2.timestamp = datetime("2025-07-25T14:30:00Z"),
    e2.impact = "MEDIUM",
    e2.description = "Analytics data showing inconsistent metrics",
    e2.affected_metric = "data_accuracy",
    e2.metric_value = 92.5,
    e2.duration_minutes = 480,
    e2.affected_success_score = -5,
    e2.resolution_time_minutes = 720,
    e2.root_cause = "ETL pipeline configuration error",
    e2.created_at = datetime(),
    e2.updated_at = datetime();

// Netflix Events
MERGE (e3:Event:Entity {id: "event-netflix-feature-001"})
ON CREATE SET
    e3.entity_type = "Event",
    e3.type = "feature_success",
    e3.customer_id = "Netflix",
    e3.timestamp = datetime("2025-07-20T10:00:00Z"),
    e3.impact = "POSITIVE",
    e3.description = "Successfully deployed custom recommendation engine",
    e3.affected_metric = "feature_adoption",
    e3.metric_value = 95,
    e3.duration_minutes = 0,
    e3.affected_success_score = 10,
    e3.resolution_time_minutes = 0,
    e3.created_at = datetime(),
    e3.updated_at = datetime();

// EA Events
MERGE (e4:Event:Entity {id: "event-ea-security-001"})
ON CREATE SET
    e4.entity_type = "Event",
    e4.type = "security_alert",
    e4.customer_id = "EA",
    e4.timestamp = datetime("2025-07-22T18:45:00Z"),
    e4.impact = "HIGH",
    e4.description = "Unusual API access pattern detected",
    e4.affected_metric = "security_score",
    e4.metric_value = 75,
    e4.duration_minutes = 120,
    e4.affected_success_score = -7,
    e4.resolution_time_minutes = 180,
    e4.root_cause = "Misconfigured API rate limits",
    e4.created_at = datetime(),
    e4.updated_at = datetime();

// ========================================
// STEP 3: Create More Projects
// ========================================

MERGE (p1:Project:Entity {id: "proj-netflix-ml-2025"})
ON CREATE SET
    p1.entity_type = "Project",
    p1.name = "ML Pipeline Enhancement - Netflix",
    p1.customer_id = "Netflix",
    p1.features = ["Real-time ML scoring", "A/B testing framework", "Model versioning"],
    p1.status = "on_track",
    p1.start_date = date("2025-01-15"),
    p1.due_date = date("2025-04-15"),
    p1.completion_percentage = 65,
    p1.team_id = "analytics-team",
    p1.priority = "HIGH",
    p1.estimated_hours = 3200,
    p1.actual_hours = 2080,
    p1.budget = 450000,
    p1.actual_cost = 290000,
    p1.created_at = datetime(),
    p1.updated_at = datetime();

MERGE (p2:Project:Entity {id: "proj-spotify-api-2025"})
ON CREATE SET
    p2.entity_type = "Project",
    p2.name = "API v3 Migration - Spotify",
    p2.customer_id = "Spotify",
    p2.features = ["GraphQL support", "Webhook enhancements", "Rate limiting improvements"],
    p2.status = "on_track",
    p2.start_date = date("2025-02-01"),
    p2.due_date = date("2025-05-01"),
    p2.completion_percentage = 40,
    p2.team_id = "integration-team",
    p2.priority = "MEDIUM",
    p2.estimated_hours = 1600,
    p2.actual_hours = 640,
    p2.budget = 200000,
    p2.actual_cost = 80000,
    p2.created_at = datetime(),
    p2.updated_at = datetime();

MERGE (p3:Project:Entity {id: "proj-nintendo-security-2025"})
ON CREATE SET
    p3.entity_type = "Project",
    p3.name = "Security Enhancement - Nintendo",
    p3.customer_id = "Nintendo",
    p3.features = ["Zero-trust architecture", "Enhanced encryption", "Compliance automation"],
    p3.status = "planning",
    p3.start_date = date("2025-03-01"),
    p3.due_date = date("2025-06-30"),
    p3.completion_percentage = 10,
    p3.team_id = "platform-team",
    p3.priority = "HIGH",
    p3.estimated_hours = 2400,
    p3.actual_hours = 240,
    p3.budget = 350000,
    p3.actual_cost = 35000,
    p3.created_at = datetime(),
    p3.updated_at = datetime();

// ========================================
// STEP 4: Create More Teams
// ========================================

MERGE (t1:Team:Entity {name: "Customer Success Team"})
ON CREATE SET
    t1.entity_type = "Team",
    t1.size = 12,
    t1.lead = "Emily Chen",
    t1.capacity_utilization = 0.95,
    t1.specialization = "Customer Success Management",
    t1.location = "New York",
    t1.avg_tenure_years = 2.5,
    t1.skills = ["Account Management", "Technical Support", "Business Analysis"],
    t1.created_at = datetime(),
    t1.updated_at = datetime();

MERGE (t2:Team:Entity {name: "DevOps Team"})
ON CREATE SET
    t2.entity_type = "Team",
    t2.size = 18,
    t2.lead = "Marcus Johnson",
    t2.capacity_utilization = 0.88,
    t2.specialization = "Infrastructure and Operations",
    t2.location = "Seattle",
    t2.avg_tenure_years = 3.8,
    t2.skills = ["Kubernetes", "AWS", "Monitoring", "CI/CD"],
    t2.created_at = datetime(),
    t2.updated_at = datetime();

// ========================================
// STEP 5: Create More SLA Templates
// ========================================

MERGE (sla1:SLA:Entity {id: "sla-pro-standard"})
ON CREATE SET
    sla1.entity_type = "SLA",
    sla1.name = "Pro Standard SLA",
    sla1.uptime_percentage = 99.0,
    sla1.response_time_ms = 1000,
    sla1.support_response_hours = 8,
    sla1.severity_levels = ["High", "Medium", "Low"],
    sla1.penalty_uptime_breach = "5% monthly credit",
    sla1.penalty_response_time_breach = "2.5% monthly credit",
    sla1.measurement_period = "monthly",
    sla1.created_at = datetime(),
    sla1.updated_at = datetime();

MERGE (sla2:SLA:Entity {id: "sla-enterprise-premium"})
ON CREATE SET
    sla2.entity_type = "SLA",
    sla2.name = "Enterprise Premium SLA",
    sla2.uptime_percentage = 99.99,
    sla2.response_time_ms = 200,
    sla2.support_response_hours = 1,
    sla2.severity_levels = ["Critical", "High", "Medium", "Low"],
    sla2.penalty_uptime_breach = "25% monthly credit",
    sla2.penalty_response_time_breach = "15% monthly credit",
    sla2.measurement_period = "monthly",
    sla2.created_at = datetime(),
    sla2.updated_at = datetime();

// ========================================
// STEP 6: Create Quarterly Objectives
// ========================================

MERGE (obj1:CompanyObjective:Entity {id: "obj-2025-q1-nps"})
ON CREATE SET
    obj1.entity_type = "CompanyObjective",
    obj1.name = "Q1 NPS Improvement",
    obj1.description = "Improve Net Promoter Score to 75+",
    obj1.target_value = 75,
    obj1.current_value = 68,
    obj1.unit = "score",
    obj1.due_date = date("2025-03-31"),
    obj1.status = "at_risk",
    obj1.priority = "HIGH",
    obj1.owner = "VP Customer Success",
    obj1.created_at = datetime(),
    obj1.updated_at = datetime();

MERGE (obj2:CompanyObjective:Entity {id: "obj-2025-q1-churn"})
ON CREATE SET
    obj2.entity_type = "CompanyObjective",
    obj2.name = "Q1 Churn Reduction",
    obj2.description = "Reduce customer churn to below 5%",
    obj2.target_value = 5,
    obj2.current_value = 7.2,
    obj2.unit = "percentage",
    obj2.due_date = date("2025-03-31"),
    obj2.status = "at_risk",
    obj2.priority = "CRITICAL",
    obj2.owner = "Chief Revenue Officer",
    obj2.created_at = datetime(),
    obj2.updated_at = datetime();

// ========================================
// STEP 7: Create Product Operational Costs
// ========================================

MERGE (cost1:OperationalCost:Entity {id: "cost-spyroapi-2025"})
ON CREATE SET
    cost1.entity_type = "OperationalCost",
    cost1.product_name = "SpyroAPI",
    cost1.cost_type = "infrastructure",
    cost1.monthly_cost = 25000,
    cost1.annual_cost = 300000,
    cost1.cost_compute = 15000,
    cost1.cost_storage = 3000,
    cost1.cost_network = 5000,
    cost1.cost_licenses = 2000,
    cost1.currency = "USD",
    cost1.budget_allocated = 320000,
    cost1.variance_percentage = -6.25,
    cost1.created_at = datetime(),
    cost1.updated_at = datetime();

MERGE (cost2:OperationalCost:Entity {id: "cost-spyrocloud-2025"})
ON CREATE SET
    cost2.entity_type = "OperationalCost",
    cost2.product_name = "SpyroCloud",
    cost2.cost_type = "infrastructure",
    cost2.monthly_cost = 18000,
    cost2.annual_cost = 216000,
    cost2.cost_compute = 10000,
    cost2.cost_storage = 4000,
    cost2.cost_network = 2000,
    cost2.cost_licenses = 2000,
    cost2.currency = "USD",
    cost2.budget_allocated = 220000,
    cost2.variance_percentage = -1.8,
    cost2.created_at = datetime(),
    cost2.updated_at = datetime();

// ========================================
// STEP 8: Create Q2 2025 Roadmap
// ========================================

MERGE (r1:Roadmap:Entity {id: "roadmap-2025-q2"})
ON CREATE SET
    r1.entity_type = "Roadmap",
    r1.quarter = "Q2 2025",
    r1.year = 2025,
    r1.themes = ["AI/ML Capabilities", "Platform Scalability", "Customer Experience"],
    r1.planned_features = ["AutoML Framework", "Multi-region deployment", "Self-service portal", "Advanced analytics"],
    r1.feature_statuses = ["planning", "planning", "design", "planning"],
    r1.resource_platform_team = 0.5,
    r1.resource_analytics_team = 0.6,
    r1.resource_integration_team = 0.2,
    r1.resource_devops_team = 0.3,
    r1.created_at = datetime(),
    r1.updated_at = datetime();

// ========================================
// STEP 9: Establish All Relationships
// ========================================

// Connect new events to customers
MATCH (c:Customer {name: "Disney"})
MATCH (e:Event {customer_id: "Disney"})
WHERE NOT EXISTS((c)-[:AFFECTED_BY]->(e))
CREATE (c)-[r:AFFECTED_BY {
    severity: e.impact,
    business_impact: CASE 
        WHEN e.impact = "CRITICAL" THEN "Revenue at risk"
        WHEN e.impact = "HIGH" THEN "Service degradation"
        ELSE "Minor disruption"
    END,
    created_at: datetime()
}]->(e);

MATCH (c:Customer {name: "Netflix"})
MATCH (e:Event {customer_id: "Netflix"})
WHERE NOT EXISTS((c)-[:AFFECTED_BY]->(e))
CREATE (c)-[r:AFFECTED_BY {
    severity: e.impact,
    business_impact: "Positive outcome",
    created_at: datetime()
}]->(e);

MATCH (c:Customer {name: "EA"})
MATCH (e:Event {customer_id: "EA"})
WHERE NOT EXISTS((c)-[:AFFECTED_BY]->(e))
CREATE (c)-[r:AFFECTED_BY {
    severity: e.impact,
    business_impact: "Security concern",
    created_at: datetime()
}]->(e);

// Connect new projects to customers
MATCH (c:Customer)
MATCH (p:Project {customer_id: c.name})
WHERE NOT EXISTS((c)-[:HAS_PROJECT]->(p))
CREATE (c)-[r:HAS_PROJECT {
    priority: p.priority,
    business_impact: CASE 
        WHEN p.priority = "HIGH" THEN "Strategic"
        ELSE "Operational"
    END,
    created_at: datetime()
}]->(p);

// Connect teams to new projects
MATCH (t:Team {name: "Analytics Team"})
MATCH (p:Project {team_id: "analytics-team"})
WHERE NOT EXISTS((t)-[:WORKS_ON]->(p))
CREATE (t)-[r:WORKS_ON {
    allocation_percentage: 65,
    start_date: p.start_date,
    created_at: datetime()
}]->(p);

MATCH (t:Team {name: "Integration Team"})
MATCH (p:Project {team_id: "integration-team"})
WHERE NOT EXISTS((t)-[:WORKS_ON]->(p))
CREATE (t)-[r:WORKS_ON {
    allocation_percentage: 40,
    start_date: p.start_date,
    created_at: datetime()
}]->(p);

MATCH (t:Team {name: "Platform Team"})
MATCH (p:Project {team_id: "platform-team"})
WHERE NOT EXISTS((t)-[:WORKS_ON]->(p))
CREATE (t)-[r:WORKS_ON {
    allocation_percentage: 30,
    start_date: p.start_date,
    created_at: datetime()
}]->(p);

// Connect products to new SLAs
MATCH (p:Product {name: "SpyroCloud"})
MATCH (sla:SLA {id: "sla-pro-standard"})
WHERE NOT EXISTS((p)-[:HAS_SLA]->(sla))
CREATE (p)-[r:HAS_SLA {
    tier: "Pro",
    effective_date: date("2023-01-01"),
    created_at: datetime()
}]->(sla);

MATCH (p:Product)
WHERE p.name IN ["SpyroSuite", "SpyroAnalytics", "SpyroAPI"]
MATCH (sla:SLA {id: "sla-enterprise-premium"})
WHERE NOT EXISTS((p)-[:HAS_SLA]->(sla))
CREATE (p)-[r:HAS_SLA {
    tier: "Enterprise Premium",
    effective_date: date("2023-01-01"),
    created_at: datetime()
}]->(sla);

// Connect products to operational costs
MATCH (p:Product {name: "SpyroAPI"})
MATCH (cost:OperationalCost {product_name: "SpyroAPI"})
WHERE NOT EXISTS((p)-[:INCURS]->(cost))
CREATE (p)-[r:INCURS {
    cost_type: "infrastructure",
    allocation: 1.0,
    created_at: datetime()
}]->(cost);

MATCH (p:Product {name: "SpyroCloud"})
MATCH (cost:OperationalCost {product_name: "SpyroCloud"})
WHERE NOT EXISTS((p)-[:INCURS]->(cost))
CREATE (p)-[r:INCURS {
    cost_type: "infrastructure",
    allocation: 1.0,
    created_at: datetime()
}]->(cost);

// Connect events to success scores
MATCH (e:Event)
MATCH (css:CustomerSuccessScore {customer_id: e.customer_id})
WHERE NOT EXISTS((e)-[:IMPACTS]->(css))
CREATE (e)-[r:IMPACTS {
    score_change: e.affected_success_score,
    impact_type: CASE 
        WHEN e.affected_success_score < 0 THEN "negative"
        ELSE "positive"
    END,
    created_at: datetime()
}]->(css);

// Connect Customer Success Team to customers
MATCH (t:Team {name: "Customer Success Team"})
MATCH (c:Customer)
WHERE c.tier = "Enterprise"
CREATE (t)-[r:MANAGES_ACCOUNT {
    account_type: "Strategic",
    assigned_csm: CASE 
        WHEN c.name = "Disney" THEN "Alice Johnson"
        WHEN c.name = "Netflix" THEN "Bob Williams"
        WHEN c.name = "EA" THEN "Carol Davis"
        ELSE "Team Pool"
    END,
    created_at: datetime()
}]->(c);

// Connect DevOps Team to infrastructure
MATCH (t:Team {name: "DevOps Team"})
MATCH (p:Product)
WHERE p.name IN ["SpyroSuite", "SpyroAnalytics", "SpyroAPI"]
CREATE (t)-[r:MAINTAINS_INFRASTRUCTURE {
    sla_commitment: "99.9% uptime",
    on_call_rotation: "24/7",
    created_at: datetime()
}]->(p);

// Connect risks to new objectives
MATCH (r:Risk {name: "data privacy"})
MATCH (obj:CompanyObjective {id: "obj-2025-q1-nps"})
WHERE NOT EXISTS((r)-[:THREATENS]->(obj))
CREATE (r)-[rel:THREATENS {
    impact_level: "MEDIUM",
    mitigation_priority: "High",
    created_at: datetime()
}]->(obj);

MATCH (r:Risk {description: "SLA violations"})
MATCH (obj:CompanyObjective {id: "obj-2025-q1-churn"})
WHERE NOT EXISTS((r)-[:THREATENS]->(obj))
CREATE (r)-[rel:THREATENS {
    impact_level: "HIGH",
    mitigation_priority: "Critical",
    created_at: datetime()
}]->(obj);

// Connect all products to Q2 roadmap
MATCH (p:Product)
MATCH (r:Roadmap {quarter: "Q2 2025"})
WHERE NOT EXISTS((p)-[:IN_ROADMAP]->(r))
CREATE (p)-[rel:IN_ROADMAP {
    priority: CASE 
        WHEN p.name CONTAINS "Analytics" THEN "HIGH"
        ELSE "MEDIUM"
    END,
    feature_count: CASE 
        WHEN p.name CONTAINS "Analytics" THEN 2
        ELSE 1
    END,
    created_at: datetime()
}]->(r);

// Connect projects to roadmaps
MATCH (p:Project)
WHERE p.due_date > date("2025-03-31") AND p.due_date <= date("2025-06-30")
MATCH (r:Roadmap {quarter: "Q2 2025"})
WHERE NOT EXISTS((p)-[:DELIVERS_FEATURES_FOR]->(r))
CREATE (p)-[rel:DELIVERS_FEATURES_FOR {
    alignment: "Direct",
    created_at: datetime()
}]->(r);

// Update total metrics
MATCH (arr:Metric {name: "Annual Recurring Revenue"})
MATCH (s:Subscription)
WITH arr, sum(s.arr) as total_arr, count(s) as subscription_count
SET arr.current_value = total_arr,
    arr.subscription_count = subscription_count,
    arr.avg_contract_value = total_arr / subscription_count,
    arr.updated_at = datetime();

// ========================================
// STEP 10: Create Cross-Entity Analytics
// ========================================

// Create revenue by product metric
MERGE (rpm:Metric:Entity {name: "Revenue by Product"})
ON CREATE SET
    rpm.entity_type = "Metric",
    rpm.type = "financial",
    rpm.unit = "USD",
    rpm.created_at = datetime();

MATCH (s:Subscription)-[r:INCLUDES_PRODUCT]->(p:Product)
WITH p, sum(r.units * r.price_per_unit * 12) as product_arr
MATCH (rpm:Metric {name: "Revenue by Product"})
CREATE (p)-[rel:CONTRIBUTES_REVENUE {
    amount: product_arr,
    created_at: datetime()
}]->(rpm);

// Create team utilization metric
MERGE (tum:Metric:Entity {name: "Team Utilization"})
ON CREATE SET
    tum.entity_type = "Metric",
    tum.type = "operational",
    tum.unit = "percentage",
    tum.created_at = datetime();

MATCH (t:Team)
WITH t, avg(t.capacity_utilization) as avg_utilization
MATCH (tum:Metric {name: "Team Utilization"})
SET tum.current_value = avg_utilization * 100,
    tum.updated_at = datetime();

// ========================================
// Summary Report
// ========================================

CALL {
    MATCH (n)
    RETURN "Total Nodes" as Category, count(n) as Count
    UNION
    MATCH ()-[r]->()
    RETURN "Total Relationships" as Category, count(r) as Count
    UNION
    MATCH (c:Customer)
    RETURN "Customers" as Category, count(c) as Count
    UNION
    MATCH (s:Subscription)
    RETURN "Subscriptions" as Category, count(s) as Count
    UNION
    MATCH (p:Project)
    RETURN "Projects" as Category, count(p) as Count
    UNION
    MATCH (e:Event)
    RETURN "Events" as Category, count(e) as Count
    UNION
    MATCH (t:Team)
    RETURN "Teams" as Category, count(t) as Count
    UNION
    MATCH (arr:Metric {name: "Annual Recurring Revenue"})
    RETURN "Total ARR" as Category, arr.current_value as Count
}
RETURN Category, Count
ORDER BY Category;