"""
Neo4j Data Model Context for Agentic RAG - Complete Version
This provides comprehensive knowledge about ALL entities in the data structure
to enable autonomous, informed decision-making by the agent.
"""

DATA_MODEL_CONTEXT = """
# Neo4j Knowledge Graph Complete Data Model

## Core Philosophy
- All entities follow LlamaIndex labeling: labels include both '__Entity__' and the specific type
- Many attributes are stored as separate nodes rather than properties
- Financial values may be strings with '$' and 'M' suffixes OR numeric values
- Relationships connect entities in specific patterns - understanding these is crucial

## Complete Entity Inventory

### Customer & Business Entities

#### CUSTOMER (58 nodes)
Properties: api_calls_per_month, contract_dates, conversion_days, created_from_lead, industry, monthly_active_users, name, primary_product, region, segment, size, subscription_start_date, usage_growth
Relationships:
- (CUSTOMER)-[:USES]->(PRODUCT)
- (CUSTOMER)-[:SUBSCRIBES_TO]->(SUBSCRIPTION)
- (CUSTOMER)-[:HAS_SUCCESS_SCORE]->(CUSTOMER_SUCCESS_SCORE)
- (CUSTOMER)-[:HAS_RISK]->(RISK)
- (CUSTOMER)-[:HAS_CONCERN]->(CONCERN)
- (CUSTOMER)-[:HAS_EXPANSION_OPPORTUNITY]->(EXPANSION_OPPORTUNITY)

#### LEAD (12 nodes)
Properties: company, converted_date, created_date, name, source, status
Relationships:
- (LEAD)-[:CONVERTED_TO]->(CUSTOMER)

#### SUBSCRIPTION (19 nodes)
Properties: value (string like "$8M"), status, start_date, end_date, renewal_probability
Relationships:
- (CUSTOMER)-[:SUBSCRIBES_TO]->(SUBSCRIPTION)
- (SUBSCRIPTION)-[:FOR_PRODUCT]->(PRODUCT)

#### CUSTOMER_SUCCESS_SCORE (15 nodes)
Properties: customerId, lastUpdated, score (0-100), trend (improving/declining/stable)
Relationships:
- (CUSTOMER)-[:HAS_SUCCESS_SCORE]->(CUSTOMER_SUCCESS_SCORE)

### Product & Feature Entities

#### PRODUCT (37 nodes)
Properties: name, adoption_rate, cost, features, market_focus, monthly_cost, nps_score, operational_cost, satisfaction_score
Relationships:
- (PRODUCT)<-[:USES]-(CUSTOMER)
- (PRODUCT)-[:OFFERS_FEATURE]->(FEATURE)
- (PRODUCT)-[:GENERATES_REVENUE]->(REVENUE)

#### FEATURE (107 nodes)
Properties: name, adoption_rate, active_users, deprecated, deprecation_date, description, is_new_feature, launch_date, status
Relationships:
- (PRODUCT)-[:OFFERS_FEATURE]->(FEATURE)
- (TEAM)-[:DEVELOPS]->(FEATURE)

### Financial Entities

#### REVENUE (44 nodes)
Properties: amount (numeric), period, source (recurring/one-time), currency
Relationships:
- (PRODUCT)-[:GENERATES_REVENUE]->(REVENUE)
- Various entities -[:GENERATES]->(REVENUE)

#### COST (91 nodes)
Properties: amount, category, channel, date, period, subcategory, type
Relationships:
- (TEAM)-[:INCURS_COST]->(COST)
- Various entities -[:HAS_COST]->(COST)

#### FINANCE (2 nodes)
Properties: name, type (cash_reserves), current_balance, currency, accounts, last_updated
No relationships

#### PROJECTION (8 nodes)
Properties: name, quarter (e.g., "Q1 2025"), projected_revenue, confidence, created_date
No relationships

#### MARKETING_CHANNEL (14 nodes)
Properties: name, roi (percentage), total_cost, attributed_revenue, period, active
No relationships - self-contained metrics

### Risk & Compliance Entities

#### RISK (76 nodes)
Properties: status (active/monitoring/mitigated), impact_amount (numeric), severity, description, probability
Relationships:
- (CUSTOMER)-[:HAS_RISK]->(RISK)
- (RISK)-[:THREATENS]->(various entities)

#### SLA (16 nodes)
Properties: name, target, actual_performance, penalty_percentage, uptime_target, response_time_target
Relationships:
- (CUSTOMER)-[:HAS_SLA]->(SLA)

#### EVENT (32 nodes)
Properties: type (support_escalation, security_incident, etc.), date, description, severity, impact, resolved
Relationships:
- (CUSTOMER)-[:EXPERIENCED]->(EVENT)

### Organization Entities

#### TEAM (31 nodes)
Properties: name, monthly_cost, operational_cost (rare), efficiency_ratio, revenue_supported, headcount, satisfaction_score
Relationships:
- (TEAM)-[:DELIVERS]->(PROJECT/FEATURE)
- (TEAM)-[:SUPPORTS]->(CUSTOMER)
- (TEAM)-[:RESPONSIBLE_FOR]->(various)

#### PROJECT (64 nodes)
Properties: name, status, completion_rate, budget, actual_cost, start_date, end_date, team
Relationships:
- (TEAM)-[:DELIVERS]->(PROJECT)

#### PERSON (40 nodes)
Properties: name
Relationships:
- (PERSON)-[:WORKS_FOR]->(COMPANY)
- (PERSON)-[:LED_BY]->(TEAM)

### Technical Entities

#### CODEBASE (1 node)
Properties: name, total_lines, technical_debt_lines, technical_debt_percentage, languages, debt_category_* properties
No relationships

#### CODEBASE_COMPONENT (5 nodes)
Properties: name, parent, total_lines, technical_debt_percentage
No relationships

### Planning & Strategy Entities

#### ROADMAP_ITEM (30 nodes)
Properties: name, priority, status, estimated_completion
Relationships:
- Various entities -[:HAS_ROADMAP]->(ROADMAP_ITEM)

#### MILESTONE (6 nodes)
Properties: name, quarter, risk_level, status (at_risk/on_track/completed), target_date
Relationships:
- (MILESTONE)-[:DELIVERS]->(various)

#### OBJECTIVE (51 nodes)
Properties: name, description, status, source
Relationships:
- (OBJECTIVE)-[:AT_RISK]->(RISK)

### Additional Entities

#### EXPANSION_OPPORTUNITY (24 nodes)
Properties: expected_close_date, probability, product, value
Relationships:
- (CUSTOMER)-[:HAS_EXPANSION_OPPORTUNITY]->(EXPANSION_OPPORTUNITY)

#### CONCERN (5 nodes)
Properties: created_date, description, priority, status, type
Relationships:
- (CUSTOMER)-[:HAS_CONCERN]->(CONCERN)

#### COMMITMENT (26 nodes)
Properties: description, promise_date, status, completion_percentage, revenue_at_risk
Relationships:
- (CUSTOMER)-[:HAS_COMMITMENT]->(COMMITMENT)

## Key Query Patterns

### Financial Calculations
- Revenue: Check REVENUE nodes with amount property (numeric)
- Some entities store pre-calculated metrics (e.g., MARKETING_CHANNEL.roi)
- Cash reserves in FINANCE nodes with type='cash_reserves'
- Revenue source property distinguishes recurring vs one-time

### Risk Assessment
- Active risks: status = 'active' (not 'Unmitigated')
- Financial impact: use impact_amount property
- Milestones at risk: status = 'at_risk'

### Marketing Analytics
- MARKETING_CHANNEL nodes contain self-contained ROI data
- No need to traverse relationships for marketing metrics
- ROI stored as percentage directly

### Technical Debt
- CODEBASE node contains overall metrics
- CODEBASE_COMPONENT nodes for component-level analysis
- technical_debt_percentage property available

### Lead Conversion
- LEAD nodes track conversion with CONVERTED_TO relationship
- Conversion time calculable from created_date and converted_date

### Projections
- PROJECTION nodes contain quarterly revenue forecasts
- No relationships - query directly by quarter property

## Important Notes
1. Not all expected relationships exist - always use OPTIONAL MATCH
2. Some entities have no relationships (MARKETING_CHANNEL, FINANCE, PROJECTION, CODEBASE)
3. Financial values may be strings or numbers - handle both cases
4. Many entities use '__Entity__' label in addition to their type label
5. Check property existence before calculations - not all nodes have all properties
"""

# Query hints remain the same but add new categories
QUERY_CONTEXT_HINTS = {
    "financial": "Check REVENUE (amount property), COST, FINANCE (cash reserves), and PROJECTION nodes.",
    "marketing": "MARKETING_CHANNEL nodes have roi, total_cost, attributed_revenue as properties - no relationships needed.",
    "risk": "Risks use 'active' status. Milestones can be 'at_risk'. Use impact_amount for financial impact.",
    "technical debt": "CODEBASE and CODEBASE_COMPONENT nodes have technical_debt_percentage property.",
    "projections": "PROJECTION nodes have quarter and projected_revenue properties - query directly.",
    "leads": "LEAD nodes connect to CUSTOMER via CONVERTED_TO relationship. Check created_date and converted_date.",
    "runway": "FINANCE nodes with type='cash_reserves' contain current_balance. Calculate burn from COST nodes.",
    "deprecation": "FEATURE nodes have deprecated boolean and deprecation_date properties.",
    "retention": "Calculate from subscription status, renewal_probability, and success scores.",
    "issues": "EVENT nodes with type='support_escalation' or 'security_incident'."
}