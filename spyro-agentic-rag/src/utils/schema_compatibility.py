"""Schema compatibility utilities for handling both Spyro RAG and LlamaIndex formats"""

# Mapping between Spyro RAG labels and LlamaIndex labels
LABEL_MAPPING = {
    # Spyro format -> LlamaIndex format
    "Customer": "CUSTOMER",
    "Product": "PRODUCT",
    "Team": "TEAM",
    "Project": "PROJECT",
    "Risk": "RISK",
    "SaaSSubscription": "SUBSCRIPTION",
    "AnnualRecurringRevenue": "REVENUE",
    "Feature": "FEATURE",
    "RoadmapItem": "ROADMAP_ITEM",
    "CustomerSuccessScore": "CUSTOMER_SUCCESS_SCORE",
    "Event": "EVENT",
    "OperationalCost": "COST",
    "Profitability": "PROFITABILITY",
    "Objective": "OBJECTIVE",
    "FeaturePromise": "FEATURE_PROMISE",
    "CustomerConcern": "CONCERN",
    "Region": "REGION",
    "RegionalCost": "REGIONAL_COST",
    "FeatureUsage": "FEATURE_USAGE",
    "SLAPerformance": "SLA_PERFORMANCE",
    "CompetitiveAdvantage": "COMPETITIVE_ADVANTAGE",
    "MarketSegment": "MARKET_SEGMENT",
    "IndustryBenchmark": "INDUSTRY_BENCHMARK",
    "SLA": "SLA"
}

def get_compatible_cypher(original_cypher: str) -> str:
    """
    Convert a Cypher query to work with both Spyro RAG and LlamaIndex label formats.
    
    This function modifies MATCH patterns to look for both label formats:
    - Original: (c:Customer)
    - Compatible: (c) WHERE 'Customer' IN labels(c) OR 'CUSTOMER' IN labels(c)
    
    Args:
        original_cypher: The original Cypher query
        
    Returns:
        Modified Cypher query that works with both schemas
    """
    import re
    
    # Pattern to match node patterns like (c:Customer) or (p:Product)
    node_pattern = r'\((\w+):(\w+)\)'
    
    def replace_node_pattern(match):
        var_name = match.group(1)
        label = match.group(2)
        
        # Get the LlamaIndex equivalent
        llama_label = LABEL_MAPPING.get(label, label.upper())
        
        # Create a pattern that matches both formats
        # For LlamaIndex entities, we need to check for __Entity__ AND the specific label
        return f"({var_name}) WHERE ('{label}' IN labels({var_name}) OR ('__Entity__' IN labels({var_name}) AND '{llama_label}' IN labels({var_name})))"
    
    # Replace all node patterns
    modified_cypher = re.sub(node_pattern, replace_node_pattern, original_cypher)
    
    # Handle cases where we have chained patterns like (c:Customer)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
    # We need to adjust the WHERE clauses to work properly
    lines = modified_cypher.split('\n')
    processed_lines = []
    
    for i, line in enumerate(lines):
        # If this line has multiple WHERE clauses from our replacements, combine them
        if line.count('WHERE') > 1:
            # Extract all WHERE conditions
            parts = line.split('WHERE')
            base = parts[0]
            conditions = []
            
            for j in range(1, len(parts)):
                # Extract the condition part
                cond_match = re.search(r'\((.*?)\)\)', parts[j])
                if cond_match:
                    conditions.append(cond_match.group(1))
            
            # Combine all conditions with AND
            if conditions:
                combined = base + 'WHERE ' + ' AND '.join(f'({cond})' for cond in conditions)
                # Add back any remaining part after the last condition
                last_part = parts[-1].split('))')[-1]
                processed_lines.append(combined + last_part)
            else:
                processed_lines.append(line)
        else:
            processed_lines.append(line)
    
    return '\n'.join(processed_lines)


def get_unified_schema() -> str:
    """
    Get a schema description that includes both Spyro RAG and LlamaIndex formats.
    
    Returns:
        Schema string that describes both labeling conventions
    """
    unified_schema = """
Node properties (supports both Spyro RAG and LlamaIndex formats):

SPYRO RAG FORMAT:
- **Customer**: name, industry, size, region
- **Product**: name, type, description, features, market_focus
- **Team**: name, department, size, focus_area, velocity, capacity, utilization, revenue_supported
- **Risk**: type, description, severity, mitigation_strategy, status, probability

LLAMAINDEX FORMAT (stored as :__Entity__:LABEL):
- **CUSTOMER**: name, industry, size, region  
- **PRODUCT**: name, type, description, features, market_focus
- **TEAM**: name, department, size, focus_area
- **RISK**: type, description, severity

Common properties for both formats:
- **SaaSSubscription/SUBSCRIPTION**: product, value, start_date, end_date, status
- **AnnualRecurringRevenue/REVENUE**: amount, currency, period
- **Feature/FEATURE**: name, description, category
- **RoadmapItem/ROADMAP_ITEM**: title, description, priority, estimated_completion, status
- **Project/PROJECT**: name, description, status, technologies, team_size, revenue_impact
- **Objective/OBJECTIVE**: title, description, target_date, progress, status
- **CustomerSuccessScore/CUSTOMER_SUCCESS_SCORE**: score, factors, trend, lastUpdated
- **Event/EVENT**: type, description, timestamp, impact, severity

Relationships (same for both formats):
(:Customer/:CUSTOMER)-[:SUBSCRIBES_TO]->(:SaaSSubscription/:SUBSCRIPTION)
(:Customer/:CUSTOMER)-[:HAS_RISK]->(:Risk/:RISK)
(:Team/:TEAM)-[:SUPPORTS]->(:Product/:PRODUCT)
(:Team/:TEAM)-[:WORKS_ON]->(:Project/:PROJECT)

Note: When querying, the system will automatically check for both label formats.
"""
    return unified_schema