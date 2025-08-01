#!/usr/bin/env python3
"""
Demonstrate Text2CypherRetriever capabilities with SpyroSolutions data
This retriever converts natural language to Cypher queries and returns actual graph data
"""

import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import Text2CypherRetriever
import os
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# Define the SpyroSolutions Neo4j schema
SPYRO_SCHEMA = """
Node properties:
Customer {name: STRING}
Product {name: STRING, description: STRING}
Project {name: STRING, status: STRING}
Team {name: STRING, size: INTEGER}
SaaSSubscription {plan: STRING, ARR: STRING}
CustomerSuccessScore {score: FLOAT, health_status: STRING}
Risk {type: STRING, level: STRING, description: STRING}
Event {type: STRING, date: STRING, impact: STRING}
SLA {metric: STRING, guarantee: STRING}
OperationalStatistics {metric: STRING, value: STRING}
CompanyObjective {name: STRING, description: STRING}
OperationalCost {amount: STRING}
Profitability {impact: STRING}
Roadmap {timeline: STRING, description: STRING}
Feature {name: STRING, status: STRING}

Relationship properties:
SUBSCRIBES_TO {}
HAS_SUCCESS_SCORE {}
HAS_RISK {}
AFFECTED_BY_EVENT {}
USED_BY {}
ASSIGNED_TO_TEAM {}
DELIVERS_FEATURE {}
SUPPORTS_OBJECTIVE {}
HAS_OPERATIONAL_COST {}
CONTRIBUTES_TO_PROFITABILITY {}
HAS_SLA {}
HAS_OPERATIONAL_STATS {}
HAS_ROADMAP {}
IMPACTS_RISK {}

The relationships:
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:Customer)-[:HAS_RISK]->(:Risk)
(:Customer)-[:AFFECTED_BY_EVENT]->(:Event)
(:Product)-[:USED_BY]->(:Customer)
(:Product)-[:ASSIGNED_TO_TEAM]->(:Team)
(:Product)-[:HAS_SLA]->(:SLA)
(:Product)-[:HAS_OPERATIONAL_STATS]->(:OperationalStatistics)
(:Product)-[:HAS_ROADMAP]->(:Roadmap)
(:Project)-[:DELIVERS_FEATURE]->(:Feature)
(:Project)-[:SUPPORTS_OBJECTIVE]->(:CompanyObjective)
(:Project)-[:HAS_OPERATIONAL_COST]->(:OperationalCost)
(:Project)-[:CONTRIBUTES_TO_PROFITABILITY]->(:Profitability)
(:Risk)-[:IMPACTS_RISK]->(:CompanyObjective)
"""

# Example queries to help the LLM understand the patterns
EXAMPLES = [
    "USER INPUT: 'What is the ARR for each customer?' QUERY: MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription) RETURN c.name as customer, s.ARR as revenue",
    "USER INPUT: 'Which teams manage which products?' QUERY: MATCH (p:Product)<-[:ASSIGNED_TO_TEAM]-(t:Team) RETURN p.name as product, t.name as team, t.size as team_size",
    "USER INPUT: 'Show me customer health scores' QUERY: MATCH (c:Customer)-[:HAS_SUCCESS_SCORE]->(s:CustomerSuccessScore) RETURN c.name as customer, s.score as score, s.health_status as status",
    "USER INPUT: 'What are the risks for each customer?' QUERY: MATCH (c:Customer)-[:HAS_RISK]->(r:Risk) RETURN c.name as customer, r.type as risk_type, r.level as risk_level, r.description as description",
    "USER INPUT: 'Show project costs and profitability' QUERY: MATCH (p:Project)-[:HAS_OPERATIONAL_COST]->(c:OperationalCost), (p)-[:CONTRIBUTES_TO_PROFITABILITY]->(prof:Profitability) RETURN p.name as project, c.amount as cost, prof.impact as profitability_impact"
]

def main():
    # Create LLM object
    llm = OpenAILLM(
        model_name="gpt-4o", 
        model_params={"temperature": 0}
    )
    
    # Test queries
    test_queries = [
        "What is the total ARR across all customers?",
        "Which customers are using which products?",
        "Show me all customers and their subscription values",
        "What are the operational costs for each project?",
        "Which teams are responsible for which products?",
        "List all risks and their impact levels",
        "What are the customer success scores?",
        "Show me the SLA guarantees for each product",
        "Which projects support which company objectives?",
        "What events have affected our customers?"
    ]
    
    print("🚀 SpyroSolutions Text2Cypher Retriever Demo")
    print("=" * 80)
    print("This demo shows direct graph querying using natural language\n")
    
    with neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        # Initialize the Text2CypherRetriever
        retriever = Text2CypherRetriever(
            driver=driver,
            llm=llm,
            neo4j_schema=SPYRO_SCHEMA,
            examples=EXAMPLES
        )
        
        # Run test queries
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Query {i}: {query}")
            print("-" * 60)
            
            try:
                # Get results from Text2Cypher
                results = retriever.search(query_text=query)
                
                if results.items:
                    print(f"✅ Found {len(results.items)} results:")
                    
                    # Display first few results
                    for j, item in enumerate(results.items[:5]):
                        print(f"\n   Result {j+1}:")
                        # The content is a dictionary of the Cypher query results
                        content = item.content
                        if isinstance(content, dict):
                            for key, value in content.items():
                                print(f"   - {key}: {value}")
                        else:
                            print(f"   {content}")
                    
                    if len(results.items) > 5:
                        print(f"\n   ... and {len(results.items) - 5} more results")
                    
                    # Show the generated Cypher query if available
                    if hasattr(results, 'metadata') and results.metadata:
                        if 'cypher_query' in results.metadata:
                            print(f"\n💻 Generated Cypher:")
                            print(f"   {results.metadata['cypher_query']}")
                else:
                    print("❌ No results found")
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Query failed: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print("✨ Demo Complete!")
    print("\nKey Insights:")
    print("- Text2CypherRetriever converts natural language to Cypher queries")
    print("- Returns actual graph data, not just text chunks")
    print("- Perfect for structured queries about entities and relationships")
    print("- Requires a well-defined schema and examples for best results")

if __name__ == "__main__":
    main()