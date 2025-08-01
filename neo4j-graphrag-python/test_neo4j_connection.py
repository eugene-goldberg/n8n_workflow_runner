#!/usr/bin/env python3
"""
Test Neo4j connection and basic setup
"""

import neo4j
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password123"

def test_connection():
    """Test Neo4j connection"""
    try:
        driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Verify connection
        driver.verify_connectivity()
        logger.info("✅ Successfully connected to Neo4j!")
        
        # Get database info
        with driver.session() as session:
            result = session.run("CALL dbms.components()")
            for record in result:
                logger.info(f"Neo4j Version: {record['name']} - {record['versions']}")
        
        # Check APOC installation
        with driver.session() as session:
            try:
                result = session.run("RETURN apoc.version() as version")
                version = result.single()["version"]
                logger.info(f"✅ APOC installed: {version}")
            except:
                logger.warning("⚠️  APOC not installed or not configured")
        
        # Create some test data
        with driver.session() as session:
            # Clear existing data
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("🧹 Cleared existing data")
            
            # Create sample nodes
            session.run("""
                CREATE (tc:Company {name: 'TechCorp', revenue: 450000000})
                CREATE (ac:Customer {name: 'Acme Corporation'})
                CREATE (tc)-[:HAS_CUSTOMER {contract_value: 50000000}]->(ac)
                CREATE (p:Project {name: 'Project Apollo', status: 'In Development'})
                CREATE (tc)-[:WORKS_ON]->(p)
            """)
            
            # Verify creation
            result = session.run("MATCH (n) RETURN count(n) as count")
            count = result.single()["count"]
            logger.info(f"✅ Created {count} test nodes")
            
            # Test a simple query
            result = session.run("""
                MATCH (c:Company)-[:HAS_CUSTOMER]->(customer)
                RETURN c.name as company, customer.name as customer
            """)
            for record in result:
                logger.info(f"Found relationship: {record['company']} -> {record['customer']}")
        
        driver.close()
        logger.info("✅ All tests passed!")
        
    except Exception as e:
        logger.error(f"❌ Connection failed: {e}")
        raise

if __name__ == "__main__":
    test_connection()