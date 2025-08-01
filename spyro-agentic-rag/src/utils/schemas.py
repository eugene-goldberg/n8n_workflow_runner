"""Neo4j schema definitions for SpyroSolutions"""

SPYRO_SCHEMA = """
Node properties:
- **Product**: name (STRING), type (STRING), description (STRING), features (LIST), market_focus (STRING)
- **Customer**: name (STRING), industry (STRING), size (STRING), region (STRING)
- **SaaSSubscription**: product (STRING), value (STRING), start_date (DATE), end_date (DATE), status (STRING)
- **AnnualRecurringRevenue**: amount (FLOAT), currency (STRING), period (STRING)
- **Feature**: name (STRING), description (STRING), category (STRING)
- **RoadmapItem**: title (STRING), description (STRING), priority (STRING), estimated_completion (DATE), status (STRING)
- **Team**: name (STRING), department (STRING), size (INTEGER), focus_area (STRING)
- **Project**: name (STRING), description (STRING), status (STRING), technologies (LIST), team_size (INTEGER)
- **Risk**: type (STRING), description (STRING), severity (STRING), mitigation_strategy (STRING), status (STRING)
- **Objective**: title (STRING), description (STRING), target_date (DATE), progress (FLOAT), status (STRING)
- **CustomerSuccessScore**: score (FLOAT), factors (LIST), trend (STRING)
- **Event**: type (STRING), description (STRING), timestamp (DATETIME), impact (STRING)
- **OperationalCost**: category (STRING), amount (FLOAT), frequency (STRING), department (STRING)
- **Profitability**: metric (STRING), value (FLOAT), period (STRING), trend (STRING)

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
"""