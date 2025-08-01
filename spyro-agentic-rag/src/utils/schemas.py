"""Neo4j schema definitions for SpyroSolutions"""

SPYRO_SCHEMA = """
Node properties:
- **Product**: name (STRING), type (STRING), description (STRING), features (LIST), market_focus (STRING)
- **Customer**: name (STRING), industry (STRING), size (STRING), region (STRING)
- **SaaSSubscription**: product (STRING), value (STRING), start_date (DATE), end_date (DATE), status (STRING)
- **AnnualRecurringRevenue**: amount (FLOAT), currency (STRING), period (STRING)
- **Feature**: name (STRING), description (STRING), category (STRING)
- **RoadmapItem**: title (STRING), description (STRING), priority (STRING), estimated_completion (DATE), status (STRING)
- **Team**: name (STRING), department (STRING), size (INTEGER), focus_area (STRING), velocity (INTEGER), capacity (INTEGER), utilization (FLOAT), revenue_supported (FLOAT)
- **Project**: name (STRING), description (STRING), status (STRING), technologies (LIST), team_size (INTEGER), revenue_impact (FLOAT)
- **Risk**: type (STRING), description (STRING), severity (STRING), mitigation_strategy (STRING), status (STRING), probability (FLOAT)
- **Objective**: title (STRING), description (STRING), target_date (DATE), progress (FLOAT), status (STRING)
- **CustomerSuccessScore**: score (FLOAT), factors (LIST), trend (STRING), lastUpdated (DATETIME)
- **Event**: type (STRING), description (STRING), timestamp (DATETIME), impact (STRING), severity (STRING)
- **OperationalCost**: category (STRING), amount (FLOAT), frequency (STRING), department (STRING)
- **Profitability**: metric (STRING), value (FLOAT), period (STRING), trend (STRING)
- **FeaturePromise**: name (STRING), status (STRING), expected_date (DATE), delivery_date (DATE), created_date (DATE)
- **CustomerConcern**: type (STRING), description (STRING), priority (STRING), status (STRING), created_date (DATE), last_updated (DATETIME)
- **Region**: name (STRING), code (STRING), currency (STRING)
- **RegionalCost**: cost_multiplier (FLOAT), base_cost_per_customer (FLOAT), effective_date (DATE)
- **FeatureUsage**: adoption_rate (FLOAT), value_score (FLOAT), active_users (INTEGER), last_updated (DATE), released_date (DATE)
- **SLAPerformance**: month (DATE), metric (STRING), target (FLOAT), actual (FLOAT), met (BOOLEAN), penalty_applied (FLOAT)
- **CompetitiveAdvantage**: vs_industry (STRING), market_segment (STRING), created_date (DATE)
- **MarketSegment**: name (STRING)
- **IndustryBenchmark**: cloud_uptime_sla (FLOAT), ai_accuracy_target (FLOAT), security_mttr_hours (FLOAT), updated_date (DATE)

Relationship properties:
- **SUBSCRIBES_TO**: revenue (STRING), contract_length (INTEGER), renewal_probability (FLOAT)
- **HAS_FEATURE**: importance (STRING), usage_frequency (STRING)
- **SUPPORTS**: alignment_score (FLOAT), priority (STRING)
- **AT_RISK**: likelihood (FLOAT), impact (STRING), identified_date (DATE)
- **USES**: satisfaction_score (FLOAT), usage_level (STRING)
- **GENERATES**: monthly_value (FLOAT), growth_rate (FLOAT)
- **INFLUENCED_BY**: impact_level (STRING), sentiment (STRING)
- **AFFECTS**: correlation_strength (FLOAT), impact_type (STRING)
- **IMPACTS**: severity (STRING), recovery_time (STRING)

The relationships are:
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Product)-[:HAS_FEATURE]->(:Feature)
(:Team)-[:SUPPORTS]->(:Product)
(:Objective)-[:AT_RISK]->(:Risk)
(:Customer)-[:USES]->(:Product)
(:SaaSSubscription)-[:GENERATES]->(:AnnualRecurringRevenue)
(:Product)-[:HAS_ROADMAP]->(:RoadmapItem)
(:Team)-[:WORKS_ON]->(:Project)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:CustomerSuccessScore)-[:INFLUENCED_BY]->(:Event)
(:OperationalCost)-[:AFFECTS]->(:Profitability)
(:Risk)-[:IMPACTS]->(:Objective)
(:Customer)-[:HAS_FEATURE_PROMISE]->(:FeaturePromise)
(:Customer)-[:HAS_CONCERN]->(:CustomerConcern)
(:Customer)-[:LOCATED_IN]->(:Region)
(:Product)-[:HAS_REGIONAL_COST]->(:RegionalCost)
(:RegionalCost)-[:IN_REGION]->(:Region)
(:Feature)-[:HAS_USAGE]->(:FeatureUsage)
(:Customer)-[:VALUES_FEATURE]->(:Feature)
(:SLA)-[:HAS_PERFORMANCE]->(:SLAPerformance)
(:Feature)-[:PROVIDES_ADVANTAGE]->(:CompetitiveAdvantage)
(:CompetitiveAdvantage)-[:IN_SEGMENT]->(:MarketSegment)
(:Team)-[:RESPONSIBLE_FOR]->(:RoadmapItem)
(:Team)-[:ADDRESSING]->(:CustomerConcern)
(:Team)-[:IMPROVES_SUCCESS]->(:CustomerSuccessScore)
(:FeaturePromise)-[:DEPENDS_ON]->(:RoadmapItem)
(:Project)-[:DEPENDS_ON]->(:Project)
(:Team)-[:CREATES_RISK]->(:Risk)
(:CustomerConcern)-[:CREATES_RISK]->(:Risk)
(:Risk)-[:IMPACTS_SUCCESS]->(:CustomerSuccessScore)
"""