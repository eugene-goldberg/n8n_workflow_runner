#!/usr/bin/env python3
"""
Fixed Hybrid RAG Implementation with proper index configuration
"""

import asyncio
import logging
import os
from typing import List, Optional
from dotenv import load_dotenv

import neo4j
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings
from neo4j_graphrag.experimental.pipeline.kg_builder import SimpleKGPipeline
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.indexes import create_fulltext_index, create_vector_index
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.retrievers import HybridRetriever, VectorRetriever, Text2CypherRetriever

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Business data with clear structure
BUSINESS_DATA = """
TechCorp is a leading technology company founded in 2010 by Sarah Johnson and Michael Chen. 
The company specializes in cloud computing solutions and artificial intelligence services.
TechCorp has an annual revenue of $450 million with 15% year-over-year growth.

Major customers include:
- Acme Corporation: $50 million annual contract for cloud infrastructure
- Globex Industries: $30 million for AI-powered analytics platform
- Initech Solutions: $25 million for hybrid cloud deployment

Key Projects:
1. Project Apollo: AI-driven customer analytics platform
   - Status: In development
   - Expected delivery: Q2 2024
   - Revenue impact: $75 million
   - Risk level: Medium (technical complexity)

2. Project Zeus: Next-gen cloud infrastructure
   - Status: Production
   - Monthly recurring revenue: $12 million
   - Customer: Acme Corporation
   - SLA compliance: 99.99%

Revenue at Risk:
- TechCorp has $125 million in revenue at risk due to:
  - Project Apollo delays could impact Q2 targets
  - Acme Corporation considering competitive solutions
  - SLA penalties if uptime drops below 99.9%

Customer Relationships:
- Acme Corporation is TechCorp's largest customer, accounting for 20% of total revenue
- Globex Industries has been a customer since 2015 with high satisfaction scores
- Initech Solutions is exploring expansion of services, potential $15 million opportunity

Team Structure:
- Engineering: 250 employees led by Director of Engineering Lisa Wang
- Sales: 80 employees led by VP of Sales Robert Taylor
- Customer Success: 45 employees led by Director CS Amanda Martinez

Competitive Landscape:
- Main competitors: CloudFirst, AIVentures, and DataSync
- TechCorp holds 15% market share in enterprise cloud solutions
- Unique differentiator: Integrated AI capabilities with cloud infrastructure
"""


async def setup_knowledge_graph():
    """Build knowledge graph and create indexes"""
    logger.info("Setting up knowledge graph...")
    
    # Initialize components
    driver = neo4j.GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))
    embedder = OpenAIEmbeddings(model="text-embedding-3-small")
    llm = OpenAILLM(
        model_name="gpt-4",
        model_params={
            "temperature": 0
        }
    )
    
    # Clear existing data
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        logger.info("Cleared existing data")
    
    # Build knowledge graph
    kg_builder = SimpleKGPipeline(
        llm=llm,
        driver=driver,
        embedder=embedder,
        from_pdf=False,
    )
    
    result = await kg_builder.run_async(text=BUSINESS_DATA)
    logger.info(f"Knowledge graph built: {result}")
    
    # Wait for the embeddings to be created
    await asyncio.sleep(2)
    
    # Create indexes on the chunk nodes
    try:
        # Check what labels and properties exist
        with driver.session() as session:
            # Check for chunk nodes
            result = session.run("""
                MATCH (n)
                WHERE n.embedding IS NOT NULL
                RETURN labels(n) as labels, 
                       count(n) as count,
                       keys(n) as properties
                LIMIT 5
            """)
            
            for record in result:
                logger.info(f"Found nodes with embeddings - Labels: {record['labels']}, Count: {record['count']}, Properties: {record['properties'][:5]}")
        
        # Create vector index
        create_vector_index(
            driver,
            "chunk_vector_index",
            label="__Chunk__",
            embedding_property="embedding",
            dimensions=1536,
            similarity_fn="cosine"
        )
        logger.info("Created vector index")
        
        # Create fulltext index
        create_fulltext_index(
            driver,
            "chunk_fulltext_index",
            label="__Chunk__",
            node_properties=["text"]
        )
        logger.info("Created fulltext index")
        
    except Exception as e:
        logger.warning(f"Index creation warning: {e}")
    
    return driver, embedder, llm


async def test_retrievers(driver, embedder, llm):
    """Test different retriever types"""
    logger.info("\nTesting retrievers...")
    
    # 1. Vector Retriever
    logger.info("\n--- Testing Vector Retriever ---")
    vector_retriever = VectorRetriever(
        driver=driver,
        index_name="chunk_vector_index",
        embedder=embedder
    )
    
    try:
        result = vector_retriever.search("revenue at risk", top_k=3)
        logger.info(f"Vector search found {len(result.items)} items")
        for item in result.items:
            logger.info(f"Content preview: {item.content[:100]}...")
    except Exception as e:
        logger.error(f"Vector retriever error: {e}")
    
    # 2. Hybrid Retriever
    logger.info("\n--- Testing Hybrid Retriever ---")
    hybrid_retriever = HybridRetriever(
        driver=driver,
        vector_index_name="chunk_vector_index",
        fulltext_index_name="chunk_fulltext_index",
        embedder=embedder
    )
    
    try:
        result = hybrid_retriever.search("TechCorp revenue", top_k=3)
        logger.info(f"Hybrid search found {len(result.items)} items")
        for item in result.items:
            logger.info(f"Content preview: {item.content[:100]}...")
    except Exception as e:
        logger.error(f"Hybrid retriever error: {e}")
    
    # 3. GraphRAG with Hybrid Retriever
    logger.info("\n--- Testing GraphRAG ---")
    rag = GraphRAG(retriever=hybrid_retriever, llm=llm)
    
    test_queries = [
        "What is the revenue at risk for TechCorp?",
        "Which customers does TechCorp have?",
        "Tell me about Project Apollo",
        "Who founded TechCorp?"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        result = rag.search(query_text=query, return_context=True)
        logger.info(f"Answer: {result.answer}")
        if hasattr(result, 'retriever_result'):
            logger.info(f"Context items: {len(result.retriever_result.items)}")
    
    # 4. Text2Cypher Retriever
    logger.info("\n--- Testing Text2Cypher Retriever ---")
    text2cypher = Text2CypherRetriever(
        driver=driver,
        llm=llm
    )
    
    cypher_queries = [
        "Find all companies and their founders",
        "List all projects with their status",
        "Show customer relationships"
    ]
    
    for query in cypher_queries:
        logger.info(f"\nCypher Query: {query}")
        try:
            result = text2cypher.search(query_text=query)
            logger.info(f"Found {len(result.items)} results")
            for item in result.items[:3]:
                logger.info(f"Result: {item.content}")
        except Exception as e:
            logger.error(f"Text2Cypher error: {e}")


async def main():
    """Main execution"""
    logger.info("Starting Fixed Hybrid RAG Demo...")
    
    # Setup
    driver, embedder, llm = await setup_knowledge_graph()
    
    # Test
    await test_retrievers(driver, embedder, llm)
    
    # Cleanup
    driver.close()
    logger.info("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(main())