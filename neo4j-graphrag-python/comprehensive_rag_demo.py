#!/usr/bin/env python3
"""
Comprehensive demonstration of neo4j-graphrag-python capabilities with SpyroSolutions data
Shows the differences between various retriever types
"""

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import (
    HybridRetriever,
    Text2CypherRetriever,
    VectorRetriever
)
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.generation import GraphRAG
import os
from dotenv import load_dotenv
import logging
import time

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

# SpyroSolutions schema for Text2Cypher
SPYRO_SCHEMA = """
Node properties:
Customer {name: STRING}
Product {name: STRING}
Project {name: STRING, status: STRING}
Team {name: STRING, size: INTEGER}
SaaSSubscription {plan: STRING, ARR: STRING}
CustomerSuccessScore {score: FLOAT}
Risk {level: STRING}
Event {impact: STRING}

The relationships:
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:Customer)-[:HAS_RISK]->(:Risk)
(:Customer)-[:AFFECTED_BY_EVENT]->(:Event)
(:Product)-[:USED_BY]->(:Customer)
(:Product)-[:ASSIGNED_TO_TEAM]->(:Team)
(:Project)-[:DELIVERS_FEATURE]->(:Feature)
"""

# Example queries for Text2Cypher
EXAMPLES = [
    "USER INPUT: 'Show customer subscriptions' QUERY: MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription) RETURN c.name as customer, s.plan as plan, s.ARR as arr",
    "USER INPUT: 'Which products are managed by which teams?' QUERY: MATCH (p:Product)-[:ASSIGNED_TO_TEAM]->(t:Team) RETURN p.name as product, t.name as team",
]

def demonstrate_retrievers():
    print("🚀 Neo4j GraphRAG Python - Comprehensive Demo")
    print("=" * 80)
    print("Demonstrating different retriever types with SpyroSolutions data\n")
    
    # Initialize components
    embedder = OpenAIEmbeddings()
    llm = OpenAILLM(model_name="gpt-4o", model_params={"temperature": 0})
    
    with neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD)) as driver:
        
        # Test queries
        test_queries = [
            "What products does SpyroSolutions offer?",
            "Which customers have which subscription plans and what are their ARR values?",
            "Show me the teams and their product responsibilities"
        ]
        
        # 1. Vector Retriever - Pure semantic search
        print("\n" + "="*80)
        print("1. VECTOR RETRIEVER - Pure Semantic Search")
        print("="*80)
        print("Searches for chunks based on semantic similarity to the query\n")
        
        vector_retriever = VectorRetriever(
            driver=driver,
            index_name="spyro_vector_index",
            embedder=embedder
        )
        
        for query in test_queries[:1]:  # Just one example
            print(f"Query: {query}")
            start_time = time.time()
            
            try:
                results = vector_retriever.search(query_text=query, top_k=3)
                elapsed = (time.time() - start_time) * 1000
                
                print(f"Found {len(results.items)} chunks in {elapsed:.0f}ms:")
                for i, item in enumerate(results.items[:2], 1):
                    print(f"\n  Chunk {i}:")
                    print(f"  Text: {item.content[:150]}...")
                print()
                
            except Exception as e:
                print(f"Error: {e}\n")
        
        # 2. Hybrid Retriever - Vector + Fulltext
        print("\n" + "="*80)
        print("2. HYBRID RETRIEVER - Vector + Fulltext Search")
        print("="*80)
        print("Combines semantic similarity and keyword matching\n")
        
        hybrid_retriever = HybridRetriever(
            driver=driver,
            vector_index_name="spyro_vector_index",
            fulltext_index_name="spyro_fulltext_index",
            embedder=embedder
        )
        
        for query in test_queries[:1]:  # Just one example
            print(f"Query: {query}")
            start_time = time.time()
            
            try:
                results = hybrid_retriever.search(query_text=query, top_k=3)
                elapsed = (time.time() - start_time) * 1000
                
                print(f"Found {len(results.items)} chunks in {elapsed:.0f}ms:")
                for i, item in enumerate(results.items[:2], 1):
                    print(f"\n  Chunk {i}:")
                    print(f"  Text: {item.content[:150]}...")
                print()
                
            except Exception as e:
                print(f"Error: {e}\n")
        
        # 3. Text2Cypher Retriever - Direct graph queries
        print("\n" + "="*80)
        print("3. TEXT2CYPHER RETRIEVER - Natural Language to Graph Queries")
        print("="*80)
        print("Converts questions to Cypher and returns actual graph data\n")
        
        text2cypher_retriever = Text2CypherRetriever(
            driver=driver,
            llm=llm,
            neo4j_schema=SPYRO_SCHEMA,
            examples=EXAMPLES
        )
        
        for query in test_queries[1:]:  # Graph-oriented queries
            print(f"Query: {query}")
            start_time = time.time()
            
            try:
                results = text2cypher_retriever.search(query_text=query)
                elapsed = (time.time() - start_time) * 1000
                
                print(f"Found {len(results.items)} results in {elapsed:.0f}ms:")
                for i, item in enumerate(results.items[:3], 1):
                    print(f"\n  Result {i}: {item.content}")
                print()
                
            except Exception as e:
                print(f"Error: {e}\n")
        
        # 4. GraphRAG - Complete Q&A system
        print("\n" + "="*80)
        print("4. GRAPHRAG - Complete Question Answering")
        print("="*80)
        print("Combines retrieval with LLM generation for natural answers\n")
        
        # Create GraphRAG with hybrid retriever
        rag = GraphRAG(
            retriever=hybrid_retriever,
            llm=llm
        )
        
        qa_queries = [
            "What are the key products offered by SpyroSolutions and their SLA guarantees?",
            "Which customers are at risk and what are their subscription values?",
            "How are the engineering teams organized across products?"
        ]
        
        for query in qa_queries:
            print(f"Question: {query}")
            start_time = time.time()
            
            try:
                response = rag.search(query_text=query)
                elapsed = (time.time() - start_time) * 1000
                
                print(f"\nAnswer ({elapsed:.0f}ms):")
                print(response.answer)
                print("-" * 80)
                
            except Exception as e:
                print(f"Error: {e}\n")
        
        # Summary comparison
        print("\n" + "="*80)
        print("SUMMARY: When to Use Each Retriever")
        print("="*80)
        print("""
1. VectorRetriever:
   - Best for: Semantic search, finding conceptually similar content
   - Use when: You need to find information based on meaning, not exact keywords
   - Example: "Tell me about cloud infrastructure" → finds SpyroCloud content

2. HybridRetriever:
   - Best for: Balanced search combining semantic and keyword matching
   - Use when: You want both conceptual matches and specific term matches
   - Example: "SpyroCloud uptime SLA" → finds by product name AND concept

3. Text2CypherRetriever:
   - Best for: Structured queries about entities and relationships
   - Use when: You need specific data from the graph (counts, lists, aggregations)
   - Example: "List all customers and their ARR" → returns exact graph data

4. GraphRAG:
   - Best for: Natural language Q&A with contextual understanding
   - Use when: You want conversational answers synthesized from multiple sources
   - Example: "Explain our customer risk profile" → comprehensive analysis
        """)
        
        print("\nKey Insights:")
        print("- neo4j-graphrag-python provides multiple retrieval strategies")
        print("- Vector/Hybrid retrievers work with text chunks")
        print("- Text2Cypher works directly with graph structure")
        print("- GraphRAG combines retrieval with generation for complete answers")

if __name__ == "__main__":
    demonstrate_retrievers()