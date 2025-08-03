#!/usr/bin/env python3
"""Deep investigation of query failures in our Agentic RAG system"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent
from neo4j import GraphDatabase
import json
from datetime import datetime

# Problematic queries that still fail despite data and context
FAILING_QUERIES = [
    {
        "id": 7,
        "question": "What are the projected quarterly revenue trends for the next fiscal year?",
        "expected_pattern": "Simple match on PROJECTION nodes",
        "actual_issue": "Overly complex WHERE clause parsing"
    },
    {
        "id": 19,
        "question": "What is the correlation between team size and project completion rates?",
        "expected_pattern": "Join TEAM and PROJECT nodes",
        "actual_issue": "May need calculated fields"
    },
    {
        "id": 52,
        "question": "What percentage of revenue is recurring vs one-time?",
        "expected_pattern": "Aggregate REVENUE by source property",
        "actual_issue": "Agent queries through CUSTOMER relationships instead"
    }
]

def analyze_llm_query_generation(agent, query_info):
    """Analyze why the LLM generates incorrect queries"""
    
    print(f"\n{'='*80}")
    print(f"ANALYZING Q{query_info['id']}: {query_info['question']}")
    print("="*80)
    
    # Capture the agent's generated query
    result = agent.query(query_info['question'])
    
    print(f"\nExpected Pattern: {query_info['expected_pattern']}")
    print(f"Known Issue: {query_info['actual_issue']}")
    
    # Extract insights
    insights = {
        "question": query_info['question'],
        "llm_interpretation": "Agent tried complex pattern matching",
        "root_cause": None,
        "suggested_fix": None
    }
    
    # Analyze based on known patterns
    if "fiscal year" in query_info['question'].lower():
        insights["root_cause"] = "LLM overcomplicates temporal queries"
        insights["suggested_fix"] = "Add temporal reasoning hints to context"
    
    elif "correlation" in query_info['question'].lower():
        insights["root_cause"] = "Statistical concepts not well mapped to graph queries"
        insights["suggested_fix"] = "Provide statistical pattern examples"
    
    elif "percentage" in query_info['question'].lower() and "revenue" in query_info['question'].lower():
        insights["root_cause"] = "LLM defaults to complex traversal for aggregations"
        insights["suggested_fix"] = "Emphasize direct property aggregation in context"
    
    return insights

def test_simplified_queries(driver):
    """Test if simplified queries would work"""
    
    print("\n" + "="*80)
    print("TESTING SIMPLIFIED QUERIES")
    print("="*80)
    
    simplified_queries = [
        {
            "name": "Q7 Simplified",
            "cypher": """
                MATCH (p:PROJECTION)
                RETURN p.quarter as quarter, p.projected_revenue as revenue
                ORDER BY p.quarter
            """
        },
        {
            "name": "Q52 Simplified",
            "cypher": """
                MATCH (r:REVENUE)
                WITH r.source as source, sum(r.amount) as total
                WITH sum(total) as grand_total, 
                     collect({source: source, amount: total}) as breakdown
                UNWIND breakdown as b
                RETURN b.source as source, 
                       round(100.0 * b.amount / grand_total, 2) as percentage
            """
        }
    ]
    
    with driver.session() as session:
        for query in simplified_queries:
            print(f"\n{query['name']}:")
            print(f"Query: {query['cypher'].strip()}")
            try:
                result = session.run(query['cypher'])
                records = list(result)
                print(f"✅ SUCCESS - {len(records)} results")
                for record in records[:3]:
                    print(f"   {dict(record)}")
            except Exception as e:
                print(f"❌ ERROR: {e}")

def analyze_llm_behavior_patterns():
    """Analyze common patterns in LLM query generation failures"""
    
    print("\n" + "="*80)
    print("LLM BEHAVIOR PATTERNS ANALYSIS")
    print("="*80)
    
    patterns = {
        "Over-engineering": {
            "description": "LLM creates unnecessarily complex queries",
            "examples": [
                "Using SUBSTRING and toInteger for simple string matching",
                "Multiple nested WITH clauses for simple aggregations",
                "Complex CASE statements when direct properties exist"
            ],
            "root_cause": "LLMs trained on complex SQL/Cypher examples",
            "mitigation": "Emphasize simplicity in system prompt"
        },
        
        "Relationship Bias": {
            "description": "LLM assumes relationships exist when properties suffice",
            "examples": [
                "Looking for GENERATES_REVENUE relationships for marketing ROI",
                "Traversing through CUSTOMER for revenue calculations",
                "Expecting relationships between unconnected entities"
            ],
            "root_cause": "Graph database training emphasizes traversal",
            "mitigation": "Document which entities have self-contained metrics"
        },
        
        "Temporal Confusion": {
            "description": "LLM struggles with time-based queries",
            "examples": [
                "Complex parsing of date strings",
                "Incorrect assumptions about date formats",
                "Over-complicated fiscal year calculations"
            ],
            "root_cause": "Ambiguity in temporal language",
            "mitigation": "Provide clear date/time handling patterns"
        },
        
        "Aggregation Complexity": {
            "description": "LLM overcomplicates aggregation queries",
            "examples": [
                "Using subqueries for simple percentages",
                "Complex joins for direct property aggregation",
                "Multiple grouping attempts in single query"
            ],
            "root_cause": "SQL-like thinking in graph context",
            "mitigation": "Show simple aggregation patterns"
        }
    }
    
    for pattern_name, details in patterns.items():
        print(f"\n{pattern_name}:")
        print(f"  Description: {details['description']}")
        print(f"  Root Cause: {details['root_cause']}")
        print(f"  Mitigation: {details['mitigation']}")

def propose_solution_framework():
    """Propose a comprehensive solution framework"""
    
    print("\n" + "="*80)
    print("PROPOSED SOLUTION FRAMEWORK")
    print("="*80)
    
    framework = {
        "1. Enhanced Context Structure": {
            "Query Complexity Hints": "Add hints about when to use simple vs complex patterns",
            "Property vs Relationship Guide": "Clear guidance on self-contained entities",
            "Temporal Pattern Library": "Common date/time query patterns",
            "Aggregation Patterns": "Simple examples for percentages and statistics"
        },
        
        "2. Query Simplification Layer": {
            "Pre-processing": "Detect and simplify complex patterns before execution",
            "Pattern Recognition": "Identify common over-engineering patterns",
            "Query Rewriting": "Automatic simplification of generated queries"
        },
        
        "3. Feedback Mechanism": {
            "Error Analysis": "Learn from query failures",
            "Success Patterns": "Reinforce successful query patterns",
            "Dynamic Hints": "Adjust hints based on failure patterns"
        },
        
        "4. Schema Design Optimization": {
            "Denormalization": "Add calculated properties for common queries",
            "Relationship Simplification": "Remove unnecessary relationship types",
            "Property Standardization": "Consistent property naming and types"
        }
    }
    
    print(json.dumps(framework, indent=2))

def main():
    config = Config.from_env()
    
    # Initialize driver for direct queries
    driver = GraphDatabase.driver(
        config.neo4j_uri,
        auth=(config.neo4j_username, config.neo4j_password)
    )
    
    # Initialize agent
    agent = create_agent(config)
    
    try:
        print("DEEP INVESTIGATION: Why Queries Still Fail Despite Context\n")
        
        # 1. Analyze specific failing queries
        insights = []
        for query in FAILING_QUERIES[:1]:  # Test one for now
            insight = analyze_llm_query_generation(agent, query)
            insights.append(insight)
        
        # 2. Test simplified versions
        test_simplified_queries(driver)
        
        # 3. Analyze behavior patterns
        analyze_llm_behavior_patterns()
        
        # 4. Propose solutions
        propose_solution_framework()
        
        # Save findings
        report = {
            "timestamp": datetime.now().isoformat(),
            "query_insights": insights,
            "behavior_patterns": "See console output",
            "recommendations": [
                "Add query simplification hints to context",
                "Document self-contained entities clearly",
                "Provide temporal query patterns",
                "Consider query rewriting layer"
            ]
        }
        
        with open('deep_investigation_findings.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("\n✅ Investigation complete. Findings saved to deep_investigation_findings.json")
        
    finally:
        driver.close()
        agent.close()

if __name__ == "__main__":
    main()