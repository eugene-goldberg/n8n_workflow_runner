#!/usr/bin/env python3
"""
Demonstrate HybridCypherRetriever with proper retrieval queries for SpyroSolutions data
This shows how to enhance chunk retrieval with graph context
"""

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import HybridCypherRetriever
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
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

def main():
    # Initialize components
    embedder = OpenAIEmbeddings()
    llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
    
    print("🚀 SpyroSolutions HybridCypherRetriever Demo")
    print("=" * 80)
    print("This demo shows how to enhance chunk retrieval with graph context\n")
    
    with neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        # First, let's verify our chunk structure
        with driver.session() as session:
            result = session.run("""
                MATCH (chunk:__Chunk__)-[r]->(entity)
                RETURN type(r) as rel_type, labels(entity) as entity_labels, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            print("Chunk relationships in database:")
            for record in result:
                print(f"  {record['rel_type']} -> {record['entity_labels']}: {record['count']}")
            print()
        
        # Define different retrieval queries for different use cases
        retrieval_queries = {
            "business_context": """
            // For each chunk, find all related business entities
            WITH node, score
            OPTIONAL MATCH (node)<-[:FROM_CHUNK]-(entity)
            WHERE entity:Customer OR entity:Product OR entity:Project 
               OR entity:Team OR entity:Risk OR entity:SaaSSubscription
            WITH node, score, collect(DISTINCT {
                type: labels(entity)[0],
                name: entity.name,
                properties: properties(entity)
            }) as entities
            
            // Find relationships between entities mentioned in this chunk
            OPTIONAL MATCH (node)<-[:FROM_CHUNK]-(e1)-[rel]-(e2)
            WHERE e1 <> e2 AND (e1:Customer OR e1:Product OR e1:Project OR e1:Team)
            WITH node, score, entities, collect(DISTINCT {
                from: e1.name,
                to: e2.name,
                type: type(rel)
            }) as relationships
            
            RETURN node.text as text,
                   score,
                   entities,
                   relationships
            """,
            
            "customer_360": """
            // Enhanced retrieval for customer-related queries
            WITH node, score
            OPTIONAL MATCH (node)<-[:FROM_CHUNK]-(c:Customer)
            OPTIONAL MATCH (c)-[:SUBSCRIBES_TO]->(sub:SaaSSubscription)
            OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(css:CustomerSuccessScore)
            OPTIONAL MATCH (c)-[:HAS_RISK]->(risk:Risk)
            OPTIONAL MATCH (c)<-[:USED_BY]-(prod:Product)
            
            RETURN node.text as text,
                   score,
                   c.name as customer_name,
                   collect(DISTINCT {plan: sub.plan, arr: sub.ARR}) as subscriptions,
                   collect(DISTINCT {score: css.score, status: css.health_status}) as success_scores,
                   collect(DISTINCT {level: risk.level, type: risk.type}) as risks,
                   collect(DISTINCT prod.name) as products_used
            """,
            
            "product_insights": """
            // Enhanced retrieval for product-related queries
            WITH node, score
            OPTIONAL MATCH (node)<-[:FROM_CHUNK]-(p:Product)
            OPTIONAL MATCH (p)-[:ASSIGNED_TO_TEAM]->(t:Team)
            OPTIONAL MATCH (p)-[:HAS_SLA]->(sla:SLA)
            OPTIONAL MATCH (p)-[:HAS_OPERATIONAL_STATS]->(stats:OperationalStatistics)
            OPTIONAL MATCH (p)<-[:USED_BY]-(c:Customer)
            
            RETURN node.text as text,
                   score,
                   p.name as product_name,
                   p.description as product_description,
                   t.name as team_name,
                   t.size as team_size,
                   collect(DISTINCT {metric: sla.metric, guarantee: sla.guarantee}) as slas,
                   collect(DISTINCT {metric: stats.metric, value: stats.value}) as stats,
                   collect(DISTINCT c.name) as customers
            """
        }
        
        # Test queries
        test_cases = [
            {
                "query": "Tell me about our customers and their subscriptions",
                "retrieval_query": retrieval_queries["customer_360"],
                "description": "Customer 360 view with subscriptions, risks, and success scores"
            },
            {
                "query": "What products do we offer and who manages them?",
                "retrieval_query": retrieval_queries["product_insights"],
                "description": "Product insights with teams, SLAs, and customer usage"
            },
            {
                "query": "Show me information about projects and their business impact",
                "retrieval_query": retrieval_queries["business_context"],
                "description": "General business context with entity relationships"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{'='*80}")
            print(f"Test Case {i}: {test_case['description']}")
            print(f"Query: {test_case['query']}")
            print("-" * 80)
            
            # Create retriever with specific retrieval query
            retriever = HybridCypherRetriever(
                driver=driver,
                vector_index_name="spyro_vector_index",
                fulltext_index_name="spyro_fulltext_index",
                embedder=embedder,
                retrieval_query=test_case["retrieval_query"],
                neo4j_database=None
            )
            
            # Create GraphRAG with this retriever
            rag = GraphRAG(
                retriever=retriever,
                llm=llm
            )
            
            try:
                # Search for context
                search_results = retriever.search(query_text=test_case["query"], top_k=3)
                
                print(f"\n📊 Retrieved {len(search_results.items)} chunks with enhanced context:")
                for j, item in enumerate(search_results.items, 1):
                    print(f"\n  Chunk {j}:")
                    print(f"  Score: {item.metadata.get('score', 'N/A')}")
                    
                    # Extract enhanced context from metadata
                    if isinstance(item.content, dict):
                        text = item.content.get('text', '')
                        print(f"  Text: {text[:150]}...")
                        
                        # Show enhanced context based on query type
                        if 'customer_name' in item.content:
                            print(f"  Customer: {item.content.get('customer_name')}")
                            print(f"  Subscriptions: {item.content.get('subscriptions')}")
                            print(f"  Products Used: {item.content.get('products_used')}")
                        elif 'product_name' in item.content:
                            print(f"  Product: {item.content.get('product_name')}")
                            print(f"  Team: {item.content.get('team_name')} ({item.content.get('team_size')} engineers)")
                            print(f"  Customers: {item.content.get('customers')}")
                        elif 'entities' in item.content:
                            entities = item.content.get('entities', [])
                            if entities:
                                print(f"  Entities: {[e['name'] for e in entities[:5]]}")
                            relationships = item.content.get('relationships', [])
                            if relationships:
                                print(f"  Relationships: {relationships[:3]}")
                
                # Generate answer using GraphRAG
                print(f"\n💡 Generating answer with GraphRAG...")
                answer = rag.search(query_text=test_case["query"])
                
                print(f"\n✅ Answer:")
                print(f"{answer.answer}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error(f"Query failed: {e}", exc_info=True)
    
    print("\n" + "=" * 80)
    print("✨ Demo Complete!")
    print("\nKey Insights:")
    print("- HybridCypherRetriever enhances chunk retrieval with graph context")
    print("- Custom retrieval queries can add entity data, relationships, and aggregations")
    print("- Different queries can be optimized for different use cases (customer 360, product insights, etc.)")
    print("- The combination of vector search + graph context provides rich, contextual answers")

if __name__ == "__main__":
    main()