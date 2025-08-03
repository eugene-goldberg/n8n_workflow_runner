"""
Query Simplification Hints for Agentic RAG
These hints guide the LLM toward simpler query patterns without being prescriptive
"""

SIMPLICITY_FIRST_PROMPT = """
QUERY GENERATION PRINCIPLES:
1. ALWAYS start with the simplest possible query
2. Direct property access is preferred over relationship traversal
3. If a property exists on a node, use it directly
4. Avoid parsing or transforming data unless absolutely necessary

ANTI-PATTERNS TO AVOID:
❌ Complex string parsing: toInteger(SUBSTRING(field, x, y))
❌ Unnecessary traversals: Going through relationships when properties exist
❌ Over-aggregation: Multiple levels of WITH clauses for simple calculations
❌ Type assumptions: {type: 'ENTITY_NAME'} when you can use labels

PREFERRED PATTERNS:
✓ Direct matches: WHERE field = value or field IN [...]
✓ Simple aggregations: WITH sum(amount) as total
✓ Direct property access: node.property
✓ Label-based filtering: MATCH (n:Label) not {type: 'Label'}
"""

# Intent-based query hints
QUERY_INTENT_HINTS = {
    "projection": {
        "keywords": ["projected", "forecast", "future", "trend", "next year", "fiscal year"],
        "hint": "PROJECTION nodes contain quarter and projected_revenue as direct properties. Match directly on quarter values."
    },
    
    "percentage": {
        "keywords": ["percentage", "percent", "%", "proportion", "split"],
        "hint": "For percentages, aggregate the property directly and calculate. Don't traverse relationships unless necessary."
    },
    
    "comparison": {
        "keywords": ["vs", "versus", "compare", "between", "recurring", "one-time"],
        "hint": "When comparing categories, GROUP BY the category property directly."
    },
    
    "ranking": {
        "keywords": ["highest", "lowest", "top", "best", "worst", "most", "least"],
        "hint": "For rankings, ORDER BY the metric property directly. Many entities store calculated metrics."
    },
    
    "temporal": {
        "keywords": ["quarter", "month", "year", "date", "time", "period", "when"],
        "hint": "Temporal data is often stored as strings. Match exact values rather than parsing."
    },
    
    "metrics": {
        "keywords": ["roi", "cost", "revenue", "rate", "score", "metric"],
        "hint": "Many metrics are pre-calculated and stored as properties. Check if the metric exists before calculating."
    }
}

# Simplification patterns for query rewriting
SIMPLIFICATION_PATTERNS = [
    {
        "pattern": r"toInteger\(SUBSTRING\((\w+\.quarter),\s*\d+,\s*\d+\)\)",
        "replacement": "Simple quarter matching",
        "example": "WHERE p.quarter IN ['Q1 2025', 'Q2 2025', 'Q3 2025', 'Q4 2025']"
    },
    {
        "pattern": r"\{type:\s*['\"](\w+)['\"]\}",
        "replacement": "Label-based matching",
        "example": "MATCH (n:EntityType)"
    },
    {
        "pattern": r"CASE.*?WHEN.*?THEN.*?toFloat.*?REPLACE.*?END",
        "replacement": "Direct numeric property access",
        "example": "Use numeric properties directly when available"
    }
]

def get_intent_hint(query: str) -> str:
    """Get a hint based on query intent"""
    query_lower = query.lower()
    
    for intent, config in QUERY_INTENT_HINTS.items():
        if any(keyword in query_lower for keyword in config["keywords"]):
            return config["hint"]
    
    return ""

def suggest_simplification(cypher_query: str) -> list:
    """Suggest simplifications for a Cypher query"""
    suggestions = []
    
    for pattern in SIMPLIFICATION_PATTERNS:
        if pattern["pattern"] in cypher_query:
            suggestions.append({
                "issue": f"Complex pattern detected: {pattern['pattern']}",
                "suggestion": pattern["replacement"],
                "example": pattern["example"]
            })
    
    return suggestions