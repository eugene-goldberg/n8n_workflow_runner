"""Enhanced Cypher examples for better Text2Cypher results - Version 2"""

ENHANCED_CYPHER_EXAMPLES = [
    # Revenue and ARR queries
    {
        "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
WITH c, coalesce(s.score, s.value, 100) as score,
CASE 
    WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'M' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
    WHEN sub.value CONTAINS '$' THEN toFloat(replace(sub.value, '$', ''))
    ELSE coalesce(toFloat(sub.value), 0)
END as revenue
WITH sum(revenue) as total_arr,
     sum(CASE WHEN score < 70 THEN revenue ELSE 0 END) as low_score_arr
RETURN round((low_score_arr / total_arr) * 100, 1) as percentage, low_score_arr, total_arr"""
    },
    
    # Customer risk queries
    {
        "question": "How much revenue will be at risk if TechCorp misses their SLA next month?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
AND toLower(c.name) = 'techcorp'
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
OPTIONAL MATCH (c)-[:HAS_SLA]->(sla)
WITH c, sub,
CASE 
    WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
    ELSE coalesce(toFloat(sub.value), 0)
END as revenue,
coalesce(sla.penalty_percentage, 10) as penalty
RETURN c.name as customer, sub.value as subscription, revenue * (penalty / 100) as revenue_at_risk"""
    },
    
    # Top customers query
    {
        "question": "Who are the top 5 customers by revenue?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
WITH c, sub, coalesce(s.score, s.value, 'N/A') as success_score,
CASE 
    WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
    ELSE coalesce(toFloat(sub.value), 0)
END as revenue_value
ORDER BY revenue_value DESC
LIMIT 5
RETURN c.name as customer, sub.value as revenue, success_score"""
    },
    
    # NEW: Feature promises and delivery status
    {
        "question": "Which features were promised to customers, and what is their delivery status?",
        "cypher": """MATCH (c)-[p:PROMISED_FEATURE]->(f)
WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
AND ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f))
RETURN c.name as customer, f.name as feature, 
       p.delivery_date as promised_date, 
       f.delivery_status as status,
       CASE 
           WHEN f.delivery_status = 'DELAYED' THEN 'High Risk'
           WHEN f.delivery_status = 'AT_RISK' THEN 'Medium Risk'
           ELSE 'On Track'
       END as risk_level
ORDER BY c.name, f.name"""
    },
    
    # NEW: Feature adoption rate
    {
        "question": "What is the adoption rate of new features released in the last 6 months?",
        "cypher": """MATCH (f)
WHERE ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f))
AND f.is_new_feature = true AND exists(f.adoption_rate)
RETURN f.name as feature, 
       f.adoption_rate as adoption_percentage,
       f.active_users as active_users,
       f.released_timeframe as released
ORDER BY f.adoption_rate DESC"""
    },
    
    # NEW: Risks related to objectives
    {
        "question": "What are the top risks related to achieving Market Expansion objective?",
        "cypher": """MATCH (o) WHERE ('__Entity__' IN labels(o) AND 'OBJECTIVE' IN labels(o))
AND o.name = 'Market Expansion'
MATCH (r)-[:AFFECTS]->(o)
WHERE ('__Entity__' IN labels(r) AND 'RISK' IN labels(r))
RETURN r.name as risk, r.severity as severity, 
       r.description as description,
       r.revenue_impact as potential_impact
ORDER BY 
    CASE r.severity 
        WHEN 'CRITICAL' THEN 1 
        WHEN 'Critical' THEN 1
        WHEN 'HIGH' THEN 2
        WHEN 'High' THEN 2
        WHEN 'MEDIUM' THEN 3
        WHEN 'Medium' THEN 3
        ELSE 4 
    END,
    r.revenue_impact DESC"""
    },
    
    # NEW: Objectives with risk counts
    {
        "question": "Which company objectives have the highest number of associated risks?",
        "cypher": """MATCH (o) WHERE ('__Entity__' IN labels(o) AND 'OBJECTIVE' IN labels(o))
MATCH (r)-[:AFFECTS]->(o)
WHERE ('__Entity__' IN labels(r) AND 'RISK' IN labels(r))
WITH o, count(r) as risk_count, 
     collect({name: r.name, severity: r.severity}) as risks
RETURN o.name as objective, o.priority as priority, 
       risk_count, risks
ORDER BY risk_count DESC"""
    },
    
    # NEW: Customer concerns with actions
    {
        "question": "What are the top customer concerns, and what is currently being done to address them?",
        "cypher": """MATCH (c)-[:HAS_CONCERN]->(concern)
WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
AND exists(concern.severity)
RETURN c.name as customer,
       concern.description as concern,
       concern.severity as severity,
       coalesce(concern.action_taken, 'No action recorded') as action_being_taken,
       coalesce(concern.action_status, 'Not Started') as action_status
ORDER BY 
    CASE concern.severity
        WHEN 'Critical' THEN 1
        WHEN 'High' THEN 2
        WHEN 'Medium' THEN 3
        ELSE 4
    END"""
    },
    
    # NEW: Critical roadmap items
    {
        "question": "Which roadmap items are critical for customer retention?",
        "cypher": """MATCH (r:RoadmapItem)
WHERE r.priority IN ['CRITICAL', 'HIGH']
OPTIONAL MATCH (r)-[:IMPLEMENTS]->(f)<-[:PROMISED_FEATURE]-(c)
WHERE ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f))
AND ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
WITH r, count(DISTINCT c) as affected_customers, 
     collect(DISTINCT c.name) as customer_names
WHERE affected_customers > 0 OR r.name CONTAINS 'customer' OR r.name CONTAINS 'retention'
RETURN r.name as roadmap_item, 
       r.status as status,
       r.target_delivery as delivery_date,
       r.priority as priority,
       affected_customers,
       customer_names[0..3] as sample_customers
ORDER BY 
    CASE r.priority
        WHEN 'CRITICAL' THEN 1
        WHEN 'HIGH' THEN 2
        ELSE 3
    END,
    affected_customers DESC"""
    },
    
    # NEW: Roadmap delays
    {
        "question": "What percentage of roadmap items are currently behind schedule?",
        "cypher": """MATCH (r:RoadmapItem)
WITH count(*) as total_items,
     sum(CASE WHEN r.status IN ['BEHIND_SCHEDULE', 'DELAYED', 'AT_RISK'] THEN 1 ELSE 0 END) as behind_items
RETURN round((toFloat(behind_items) / toFloat(total_items)) * 100, 1) as percentage_behind,
       behind_items as items_behind_schedule,
       total_items as total_roadmap_items"""
    },
    
    # NEW: Teams with delays
    {
        "question": "Which teams are responsible for delayed roadmap items?",
        "cypher": """MATCH (t)-[:RESPONSIBLE_FOR]->(r:RoadmapItem)
WHERE ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t))
AND r.status IN ['BEHIND_SCHEDULE', 'DELAYED', 'AT_RISK']
WITH t, collect({item: r.name, status: r.status, priority: r.priority}) as delayed_items
RETURN t.name as team,
       size(delayed_items) as delayed_count,
       delayed_items
ORDER BY delayed_count DESC"""
    },
    
    # Risk profile queries
    {
        "question": "Which customers have high-severity risks?",
        "cypher": """MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
MATCH (c)-[:HAS_RISK]->(r)
WHERE r.severity IN ['High', 'Critical', 'high', 'critical']
RETURN c.name as customer, collect({type: r.type, severity: r.severity, description: r.description}) as risks"""
    },
    
    # Team cost queries
    {
        "question": "Which teams have the highest operational costs?",
        "cypher": """MATCH (t) WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t)))
WHERE t.monthly_cost > 0 OR t.operational_cost > 0
RETURN t.name as team, 
       coalesce(t.monthly_cost, t.operational_cost, 0) as cost,
       t.revenue_supported as revenue,
       t.efficiency_ratio as efficiency
ORDER BY cost DESC
LIMIT 5"""
    },
    
    # Product satisfaction queries
    {
        "question": "What are the satisfaction scores for each product?",
        "cypher": """MATCH (p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
WHERE p.satisfaction_score IS NOT NULL OR p.nps_score IS NOT NULL
RETURN p.name as product, p.satisfaction_score as satisfaction, p.nps_score as nps
ORDER BY p.satisfaction_score DESC"""
    },
    
    # Commitment queries
    {
        "question": "Which customer commitments are at risk?",
        "cypher": """MATCH (cm) WHERE ('Commitment' IN labels(cm) OR ('__Entity__' IN labels(cm) AND 'COMMITMENT' IN labels(cm)))
WHERE cm.status IN ['at_risk', 'At Risk', 'Not Met'] OR cm.risk_level = 'High'
RETURN cm.description as commitment, cm.status as status, 
       coalesce(cm.risk_level, 'High') as risk_level,
       cm.due_date as due_date"""
    }
]

# Instructions for the LLM
ENHANCED_CYPHER_INSTRUCTIONS = """
When generating Cypher queries, follow these patterns:

1. ALWAYS use the LlamaIndex label format:
   - LlamaIndex: (c) WHERE ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))
   - This is the only format in the database

2. Handle monetary values stored as strings:
   - Values might be stored as '$8M', '$500K', etc.
   - Convert using: toFloat(replace(replace(value, '$', ''), 'M', '')) * 1000000

3. Common entity types in LlamaIndex format:
   - CUSTOMER
   - PRODUCT
   - TEAM
   - RISK
   - COMMITMENT
   - FEATURE
   - OBJECTIVE
   - ROADMAP_ITEM

4. Handle optional relationships with OPTIONAL MATCH

5. Use coalesce() for fields that might be null

6. Common properties:
   - Success scores: score or value property
   - Subscriptions: value property (string format like '$8M')
   - Teams: monthly_cost, operational_cost, revenue_supported
   - Risks: severity, type, description
   - Features: delivery_status, adoption_rate, is_new_feature
   - Objectives: priority, status
   - RoadmapItem: status, priority, target_delivery

7. Common relationships:
   - Customer -[:PROMISED_FEATURE]-> Feature
   - Risk -[:AFFECTS]-> Objective
   - Team -[:RESPONSIBLE_FOR]-> RoadmapItem
   - RoadmapItem -[:IMPLEMENTS]-> Feature
   - Customer -[:HAS_CONCERN]-> Concern

Return only the Cypher query without any explanation.
"""