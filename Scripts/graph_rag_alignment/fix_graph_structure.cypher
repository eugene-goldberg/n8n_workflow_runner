// SpyroSolutions Graph RAG Structure Fix
// This script creates properly typed entities and relationships

// Step 1: Clear existing data (optional - comment out to preserve)
// MATCH (n) DETACH DELETE n;

// Step 2: Create constraints and indexes
CREATE CONSTRAINT customer_name IF NOT EXISTS FOR (c:Customer) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE;
CREATE CONSTRAINT risk_name IF NOT EXISTS FOR (r:Risk) REQUIRE r.name IS UNIQUE;

CREATE INDEX customer_tier IF NOT EXISTS FOR (c:Customer) ON (c.tier);
CREATE INDEX customer_risk_score IF NOT EXISTS FOR (c:Customer) ON (c.risk_score);
CREATE INDEX risk_severity IF NOT EXISTS FOR (r:Risk) ON (r.severity);

// Step 3: Create Customer nodes
MERGE (c1:Customer:Entity {name: "Disney"})
SET c1.tier = "Enterprise",
    c1.mrr = 125000,
    c1.risk_score = 8,
    c1.revenue_at_risk = 1500000,
    c1.escalations = 3,
    c1.entity_type = "Customer",
    c1.created_at = datetime(),
    c1.updated_at = datetime();

MERGE (c2:Customer:Entity {name: "EA"})
SET c2.tier = "Enterprise",
    c2.mrr = 100000,
    c2.risk_score = 7,
    c2.revenue_at_risk = 1200000,
    c2.escalations = 2,
    c2.entity_type = "Customer",
    c2.created_at = datetime(),
    c2.updated_at = datetime();

MERGE (c3:Customer:Entity {name: "Netflix"})
SET c3.tier = "Enterprise",
    c3.mrr = 150000,
    c3.risk_score = 3,
    c3.revenue_at_risk = 0,
    c3.escalations = 0,
    c3.entity_type = "Customer",
    c3.created_at = datetime(),
    c3.updated_at = datetime();

MERGE (c4:Customer:Entity {name: "Nintendo"})
SET c4.tier = "Mid-Market",
    c4.mrr = 50000,
    c4.risk_score = 5,
    c4.revenue_at_risk = 600000,
    c4.escalations = 1,
    c4.entity_type = "Customer",
    c4.created_at = datetime(),
    c4.updated_at = datetime();

MERGE (c5:Customer:Entity {name: "Spotify"})
SET c5.tier = "Mid-Market",
    c5.mrr = 75000,
    c5.risk_score = 4,
    c5.revenue_at_risk = 0,
    c5.escalations = 0,
    c5.entity_type = "Customer",
    c5.created_at = datetime(),
    c5.updated_at = datetime();

// Step 4: Create Product nodes
MERGE (p1:Product:Entity {name: "SpyroSuite"})
SET p1.version = "4.2.1",
    p1.type = "Enterprise Platform",
    p1.price_per_month = 5000,
    p1.features = ["User management", "API access", "Advanced reporting", "24/7 support"],
    p1.entity_type = "Product",
    p1.created_at = datetime(),
    p1.updated_at = datetime();

MERGE (p2:Product:Entity {name: "SpyroAnalytics"})
SET p2.version = "2.8.5",
    p2.type = "Business Intelligence",
    p2.price_per_month = 1000,
    p2.features = ["Real-time dashboards", "Custom reports", "ML insights", "SSO"],
    p2.entity_type = "Product",
    p2.created_at = datetime(),
    p2.updated_at = datetime();

MERGE (p3:Product:Entity {name: "SpyroGuard"})
SET p3.version = "1.5.0",
    p3.type = "Security Suite",
    p3.price_per_month = 2000,
    p3.features = ["Threat detection", "Compliance monitoring", "Incident response"],
    p3.entity_type = "Product",
    p3.created_at = datetime(),
    p3.updated_at = datetime();

MERGE (p4:Product:Entity {name: "SpyroConnect"})
SET p4.version = "3.1.0",
    p4.type = "Integration Platform",
    p4.price_per_month = 1500,
    p4.features = ["API gateway", "Webhook management", "Event streaming"],
    p4.entity_type = "Product",
    p4.created_at = datetime(),
    p4.updated_at = datetime();

MERGE (p5:Product:Entity {name: "SpyroShield"})
SET p5.version = "2.0.0",
    p5.type = "Data Protection",
    p5.price_per_month = 2500,
    p5.features = ["Encryption", "Access control", "Audit logging", "DLP"],
    p5.entity_type = "Product",
    p5.created_at = datetime(),
    p5.updated_at = datetime();

// Step 5: Create Risk nodes
MERGE (r1:Risk:Entity {name: "SLA violations"})
SET r1.severity = "HIGH",
    r1.impact = "Revenue loss, contract penalties",
    r1.mitigation = "Dedicated support team, priority queue",
    r1.entity_type = "Risk",
    r1.created_at = datetime(),
    r1.updated_at = datetime();

MERGE (r2:Risk:Entity {name: "performance issues"})
SET r2.severity = "MEDIUM",
    r2.impact = "User dissatisfaction, potential churn",
    r2.mitigation = "Infrastructure scaling, optimization",
    r2.entity_type = "Risk",
    r2.created_at = datetime(),
    r2.updated_at = datetime();

MERGE (r3:Risk:Entity {name: "security concerns"})
SET r3.severity = "HIGH",
    r3.impact = "Data breach risk, compliance issues",
    r3.mitigation = "Security audits, SpyroGuard deployment",
    r3.entity_type = "Risk",
    r3.created_at = datetime(),
    r3.updated_at = datetime();

MERGE (r4:Risk:Entity {name: "operational challenges"})
SET r4.severity = "MEDIUM",
    r4.impact = "Efficiency loss, increased costs",
    r4.mitigation = "Process optimization, training",
    r4.entity_type = "Risk",
    r4.created_at = datetime(),
    r4.updated_at = datetime();

// Step 6: Create Customer -> Product relationships
MATCH (c:Customer {name: "Disney"}), (p:Product {name: "SpyroSuite"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Disney"}), (p:Product {name: "SpyroAnalytics"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "EA"}), (p:Product {name: "SpyroSuite"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "EA"}), (p:Product {name: "SpyroConnect"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Netflix"}), (p:Product {name: "SpyroSuite"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Netflix"}), (p:Product {name: "SpyroAnalytics"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Netflix"}), (p:Product {name: "SpyroShield"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Nintendo"}), (p:Product {name: "SpyroSuite"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Spotify"}), (p:Product {name: "SpyroAnalytics"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

MATCH (c:Customer {name: "Spotify"}), (p:Product {name: "SpyroConnect"})
MERGE (c)-[rel:USES_PRODUCT]->(p)
SET rel.created_at = datetime();

// Step 7: Create Customer -> Risk relationships
MATCH (c:Customer {name: "Disney"}), (r:Risk {name: "SLA violations"})
MERGE (c)-[rel:HAS_RISK]->(r)
SET rel.identified_date = datetime(),
    rel.active = true;

MATCH (c:Customer {name: "Disney"}), (r:Risk {name: "performance issues"})
MERGE (c)-[rel:HAS_RISK]->(r)
SET rel.identified_date = datetime(),
    rel.active = true;

MATCH (c:Customer {name: "EA"}), (r:Risk {name: "performance issues"})
MERGE (c)-[rel:HAS_RISK]->(r)
SET rel.identified_date = datetime(),
    rel.active = true;

MATCH (c:Customer {name: "EA"}), (r:Risk {name: "operational challenges"})
MERGE (c)-[rel:HAS_RISK]->(r)
SET rel.identified_date = datetime(),
    rel.active = true;

MATCH (c:Customer {name: "Nintendo"}), (r:Risk {name: "operational challenges"})
MERGE (c)-[rel:HAS_RISK]->(r)
SET rel.identified_date = datetime(),
    rel.active = true;

// Step 8: Create Risk -> Product mitigation relationships
MATCH (r:Risk {name: "security concerns"}), (p:Product {name: "SpyroGuard"})
MERGE (r)-[rel:MITIGATED_BY]->(p)
SET rel.effectiveness = "HIGH";

MATCH (r:Risk {name: "security concerns"}), (p:Product {name: "SpyroShield"})
MERGE (r)-[rel:MITIGATED_BY]->(p)
SET rel.effectiveness = "HIGH";

MATCH (r:Risk {name: "performance issues"}), (p:Product {name: "SpyroAnalytics"})
MERGE (r)-[rel:MITIGATED_BY]->(p)
SET rel.effectiveness = "MEDIUM";

MATCH (r:Risk {name: "operational challenges"}), (p:Product {name: "SpyroConnect"})
MERGE (r)-[rel:MITIGATED_BY]->(p)
SET rel.effectiveness = "HIGH";

MATCH (r:Risk {name: "operational challenges"}), (p:Product {name: "SpyroAnalytics"})
MERGE (r)-[rel:MITIGATED_BY]->(p)
SET rel.effectiveness = "MEDIUM";

// Step 9: Create aggregate tier nodes
MATCH (c:Customer)
WITH c.tier as tier, count(c) as count, sum(c.mrr) as total_mrr
MERGE (t:Tier:Entity {name: tier})
SET t.customer_count = count,
    t.total_mrr = total_mrr,
    t.entity_type = "Tier";

// Step 10: Create summary metrics node
MERGE (m:Metrics:Entity {name: "SpyroSolutions_Summary"})
SET m.total_customers = 5,
    m.total_mrr = 500000,
    m.total_revenue_at_risk = 3300000,
    m.avg_risk_score = 5.4,
    m.entity_type = "Metrics",
    m.updated_at = datetime();

// Return summary
MATCH (c:Customer)
RETURN "Customers created: " + count(c) as result
UNION ALL
MATCH (p:Product)
RETURN "Products created: " + count(p) as result
UNION ALL
MATCH (r:Risk)
RETURN "Risks created: " + count(r) as result
UNION ALL
MATCH ()-[rel]->()
RETURN "Relationships created: " + count(rel) as result;