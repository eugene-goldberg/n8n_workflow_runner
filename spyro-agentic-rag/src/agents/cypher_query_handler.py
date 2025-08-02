"""
Comprehensive Cypher query handler for SpyroSolutions business questions
"""

import re
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json

class CypherQueryHandler:
    """Handles direct Cypher queries for specific business questions"""
    
    @staticmethod
    def serialize_value(value):
        """Convert Neo4j values to JSON-serializable format"""
        if hasattr(value, 'isoformat'):
            return value.isoformat()
        elif hasattr(value, 'to_native'):
            return str(value.to_native())
        elif isinstance(value, (list, tuple)):
            return [CypherQueryHandler.serialize_value(v) for v in value]
        elif isinstance(value, dict):
            return {k: CypherQueryHandler.serialize_value(v) for k, v in value.items()}
        return value
    
    @staticmethod
    def parse_monetary_value(value_str):
        """Parse monetary strings like '$8M' to numeric values"""
        if not value_str or value_str == 'None':
            return 0
        if isinstance(value_str, (int, float)):
            return float(value_str)
        # Remove $ and convert M to millions
        value_str = str(value_str).replace('$', '').replace(',', '')
        if 'M' in value_str:
            return float(value_str.replace('M', '')) * 1000000
        elif 'K' in value_str:
            return float(value_str.replace('K', '')) * 1000
        return float(value_str) if value_str else 0
    
    def get_query_for_question(self, question: str) -> Dict[str, Any]:
        """Return appropriate Cypher query and formatter based on question"""
        question_lower = question.lower()
        
        # Customer success score queries
        if "percentage" in question_lower and "arr" in question_lower and "success scores below" in question_lower:
            threshold = 70
            match = re.search(r'below (\d+)', question_lower)
            if match:
                threshold = int(match.group(1))
            
            return {
                "query": f"""
                // Get customers with their scores and subscription values
                MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
                OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
                OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
                WITH c, 
                     coalesce(s.score, s.value, 100) as score,
                     CASE 
                         WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'M' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
                         WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'K' THEN toFloat(replace(replace(sub.value, '$', ''), 'K', '')) * 1000
                         WHEN sub.value CONTAINS '$' THEN toFloat(replace(sub.value, '$', ''))
                         WHEN sub.value IS NOT NULL THEN toFloat(sub.value)
                         ELSE 0
                     END as revenue
                WITH sum(revenue) as total_arr,
                     sum(CASE WHEN score < {threshold} THEN revenue ELSE 0 END) as low_score_arr
                RETURN CASE 
                    WHEN total_arr > 0 THEN round((low_score_arr / total_arr) * 100, 1)
                    ELSE 0
                END as percentage, 
                low_score_arr as arr_at_risk,
                total_arr as total_arr
                """,
                "formatter": lambda records: f"{records[0]['percentage']}% of our ARR (${records[0]['arr_at_risk']/1000000:.1f}M out of ${records[0]['total_arr']/1000000:.1f}M) is dependent on customers with success scores below {threshold}."
            }
        
        # Top 5 customers by revenue
        elif "top 5 customers by revenue" in question_lower:
            return {
                "query": """
                MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
                OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
                OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
                WITH c, sub, coalesce(s.score, s.value, 'N/A') as success_score,
                CASE 
                    WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
                    WHEN sub.value IS NOT NULL THEN toFloat(sub.value)
                    ELSE 0
                END as revenue_value
                ORDER BY revenue_value DESC
                LIMIT 5
                RETURN c.name as customer, sub.value as revenue, success_score
                """,
                "formatter": lambda records: "Top 5 customers by revenue:\n" + "\n".join([
                    f"{i+1}. {r['customer']}: {r['revenue']} (Success Score: {r['success_score']})"
                    for i, r in enumerate(records)
                ])
            }
        
        # Revenue at risk for specific customer (TechCorp)
        elif "revenue at risk" in question_lower and "techcorp" in question_lower:
            return {
                "query": """
                MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
                AND (toLower(c.name) = 'techcorp' OR toLower(c.name) CONTAINS 'techcorp')
                OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
                OPTIONAL MATCH (c)-[:HAS_RISK]->(r)
                OPTIONAL MATCH (c)-[:HAS_SLA]->(sla)
                OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(score)
                RETURN c.name as customer, 
                       sub.value as subscription_value,
                       collect(DISTINCT {type: r.type, severity: r.severity, description: r.description}) as risks,
                       coalesce(sla.penalty_percentage, 10) as sla_penalty,
                       coalesce(score.score, score.value, 85) as success_score
                """,
                "formatter": lambda records: self._format_techcorp_risk(records)
            }
        
        # Customers generating 80% of revenue
        elif "80%" in question_lower and "revenue" in question_lower:
            return {
                "query": """
                MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
                OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub)
                WITH c, sub,
                CASE 
                    WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'M' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
                    WHEN sub.value CONTAINS '$' AND sub.value CONTAINS 'K' THEN toFloat(replace(replace(sub.value, '$', ''), 'K', '')) * 1000
                    WHEN sub.value CONTAINS '$' THEN toFloat(replace(sub.value, '$', ''))
                    ELSE coalesce(toFloat(sub.value), 0)
                END as revenue_value
                ORDER BY revenue_value DESC
                WITH collect({customer: c, revenue: sub.value, revenue_value: revenue_value}) as all_customers,
                     sum(revenue_value) as total_revenue
                WITH all_customers, total_revenue, total_revenue * 0.8 as target_revenue
                UNWIND range(0, size(all_customers)-1) as idx
                WITH all_customers[idx] as cust, total_revenue, target_revenue,
                     reduce(s = 0, i IN range(0, idx) | s + all_customers[i].revenue_value) as running_total
                WHERE running_total <= target_revenue
                WITH cust
                MATCH (c) WHERE c = cust.customer
                OPTIONAL MATCH (c)-[:HAS_RISK]->(r)
                RETURN c.name as customer, cust.revenue as revenue, 
                       collect(DISTINCT {type: r.type, severity: r.severity, description: r.description}) as risks
                """,
                "formatter": lambda records: self._format_80_percent_revenue(records)
            }
        
        # Customer concerns
        elif "customer concerns" in question_lower:
            return {
                "query": """
                MATCH (concern) WHERE ('Concern' IN labels(concern) OR ('__Entity__' IN labels(concern) AND 'CONCERN' IN labels(concern)))
                OPTIONAL MATCH (c)-[:HAS_CONCERN]->(concern)
                WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
                WITH concern, collect(DISTINCT c.name) as customers
                ORDER BY concern.priority DESC, size(customers) DESC
                LIMIT 10
                RETURN concern.type as concern_type, 
                       concern.description as description,
                       concern.priority as priority,
                       concern.status as status,
                       customers
                """,
                "formatter": lambda records: "Top customer concerns:\n" + "\n".join([
                    f"{i+1}. {r['concern_type']}: {r['description']}\n   Priority: {r['priority']} | Status: {r['status']} | Customers: {', '.join(r['customers'][:3])}"
                    for i, r in enumerate(records)
                ])
            }
        
        # Customer commitments at risk
        elif "commitments" in question_lower and ("risk" in question_lower or "high risk" in question_lower):
            return {
                "query": """MATCH (cm) WHERE ('Commitment' IN labels(cm) OR ('__Entity__' IN labels(cm) AND 'COMMITMENT' IN labels(cm))) AND (cm.risk_level = 'High' OR cm.status IN ['Not Met', 'At Risk', 'at_risk'])
RETURN coalesce(cm.type, cm.commitmentId, 'Commitment') as commitment_type, cm.description as description, coalesce(cm.target, 'TBD') as target, coalesce(cm.current_performance, cm.current, 'N/A') as current, cm.status as status, coalesce(cm.risk_level, 'High') as risk_level
ORDER BY CASE coalesce(cm.risk_level, 'High') WHEN 'High' THEN 1 WHEN 'Medium' THEN 2 ELSE 3 END, cm.status""",
                "formatter": lambda records: "Customer commitments at high risk:\n" + "\n".join([
                    f"\n{i+1}. {r['commitment_type']}: {r['description']}\n   Status: {r['status']} | Risk: {r['risk_level']}"
                    for i, r in enumerate(records) if r['description']
                ])
            }
        
        # Product satisfaction scores
        elif "satisfaction" in question_lower and "product" in question_lower:
            return {
                "query": """MATCH (p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p))) AND (p.satisfaction_score IS NOT NULL OR p.nps_score IS NOT NULL)
RETURN p.name as product, coalesce(p.satisfaction_score, 'N/A') as satisfaction_score, coalesce(p.nps_score, 'N/A') as nps_score
ORDER BY p.satisfaction_score DESC""",
                "formatter": lambda records: "Product satisfaction scores:\n" + "\n".join([
                    f"- {r['product']}: Satisfaction Score: {r['satisfaction_score']}/5.0 | NPS: {r['nps_score']}"
                    for r in records
                ])
            }
        
        # Promised features and delivery status
        elif "features" in question_lower and "promised" in question_lower:
            return {
                "query": """
                MATCH (f) 
                WHERE ('Feature' IN labels(f) OR ('__Entity__' IN labels(f) AND 'FEATURE' IN labels(f)))
                AND (f.promised = true OR exists(f.commitment_date))
                OPTIONAL MATCH (c)-[:WAITING_FOR|PROMISED]->(f)
                WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
                RETURN f.name as feature,
                       f.status as status,
                       f.expected_date as expected_date,
                       f.actual_date as actual_date,
                       collect(DISTINCT c.name) as waiting_customers
                ORDER BY f.expected_date
                """,
                "formatter": lambda records: "Promised features and delivery status:\n" + "\n".join([
                    f"- {r['feature']}: {r['status']} (Expected: {r['expected_date'] or 'TBD'}) | Customers waiting: {', '.join(r['waiting_customers'][:3])}"
                    for r in records
                ])
            }
        
        # Teams with high costs relative to revenue
        elif "teams" in question_lower and ("costs" in question_lower or "operational costs" in question_lower) and "revenue" in question_lower:
            return {
                "query": """MATCH (t) WHERE ('Team' IN labels(t) OR ('__Entity__' IN labels(t) AND 'TEAM' IN labels(t))) AND t.monthly_cost > 0 AND t.revenue_supported > 0
WITH t.name as team, t.monthly_cost as team_cost, t.revenue_supported as supported_revenue, t.efficiency_ratio as efficiency_ratio
ORDER BY efficiency_ratio ASC
LIMIT 5
RETURN team, team_cost, supported_revenue, round(team_cost / supported_revenue * 100, 2) as cost_to_revenue_ratio""",
                "formatter": lambda records: "Teams with highest operational costs relative to revenue:\n" + "\n".join([
                    f"{i+1}. {r['team']}: ${r['team_cost']:,.0f} monthly cost / ${r['supported_revenue']/1000000:.1f}M revenue = {r['cost_to_revenue_ratio']}% ratio"
                    for i, r in enumerate(records)
                ])
            }
        
        # Product profitability margins
        elif "profitability margin" in question_lower and "product" in question_lower:
            return {
                "query": """
                MATCH (p) WHERE ('Product' IN labels(p) OR ('__Entity__' IN labels(p) AND 'PRODUCT' IN labels(p)))
                OPTIONAL MATCH (p)<-[:SUBSCRIBES_TO]-(sub)
                OPTIONAL MATCH (p)-[:HAS_COST]->(c)
                WITH p.name as product,
                     sum(CASE 
                         WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
                         ELSE coalesce(toFloat(sub.value), 0)
                     END) as revenue,
                     sum(coalesce(c.amount, 0)) as costs
                WHERE revenue > 0
                RETURN product,
                       revenue,
                       costs,
                       round((revenue - costs) / revenue * 100, 1) as profit_margin
                ORDER BY profit_margin DESC
                """,
                "formatter": lambda records: "Profitability margin by product:\n" + "\n".join([
                    f"- {r['product']}: {r['profit_margin']}% margin (${r['revenue']/1000000:.1f}M revenue - ${r['costs']/1000000:.1f}M costs)"
                    for r in records
                ])
            }
        
        # Default: return general entities
        else:
            return {
                "query": """
                MATCH (n)
                WHERE any(label in labels(n) WHERE label IN ['Customer', 'Product', 'Team', 'Risk', 'CUSTOMER', 'PRODUCT', 'TEAM', 'RISK'])
                RETURN labels(n) as entity_type, n.name as name, properties(n) as properties
                LIMIT 10
                """,
                "formatter": lambda records: json.dumps([self.serialize_value(dict(r)) for r in records], indent=2)
            }
    
    def _format_techcorp_risk(self, records):
        """Format TechCorp risk assessment"""
        if not records:
            return "TechCorp data not found in the system."
        
        record = records[0]
        customer = record['customer']
        subscription = record['subscription_value']
        risks = [r for r in record.get('risks', []) if r.get('type')]  # Filter out empty risks
        sla_penalty = record.get('sla_penalty', 10)
        success_score = record.get('success_score', 85)
        
        # Parse subscription value
        sub_value = self.parse_monetary_value(subscription)
        risk_amount = sub_value * (sla_penalty / 100)
        
        response = f"TechCorp Risk Assessment:\n"
        response += f"- Customer: {customer}\n"
        response += f"- Current subscription: {subscription}\n"
        response += f"- Success Score: {success_score}\n"
        response += f"- SLA miss penalty: {sla_penalty}% of subscription value\n"
        response += f"- Revenue at risk if SLA missed: ${risk_amount/1000000:.1f}M\n"
        
        if risks:
            response += f"\nCurrent risks:\n"
            for risk in risks:
                response += f"  - {risk['type']} ({risk['severity']}): {risk.get('description', 'No description')}\n"
        else:
            response += f"\n- No specific risks currently identified\n"
        
        return response
    
    def _format_80_percent_revenue(self, records):
        """Format customers generating 80% of revenue with risk profiles"""
        if not records:
            return "No customer revenue data found."
        
        response = "Customers generating 80% of revenue:\n"
        for r in records:
            risks = [risk for risk in r.get('risks', []) if risk.get('type')]
            risk_str = ""
            if risks:
                risk_str = ", ".join([f"{risk['type']} ({risk['severity']})" for risk in risks])
            else:
                risk_str = "No identified risks"
            
            response += f"- {r['customer']}: {r['revenue']} | Risks: {risk_str}\n"
        
        return response