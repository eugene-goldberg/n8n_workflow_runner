#!/usr/bin/env python3
"""
Migrate existing Spyro RAG data to LlamaIndex schema format
This will convert entities like :Customer to :__Entity__:CUSTOMER
"""

from neo4j import GraphDatabase
import os
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Label mappings
LABEL_MAPPINGS = {
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


def migrate_to_llamaindex():
    """Migrate all Spyro RAG entities to LlamaIndex format"""
    
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'), 
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    logger.info("Starting migration to LlamaIndex schema...")
    
    with driver.session() as session:
        # Count existing entities
        result = session.run("""
            MATCH (n)
            WHERE any(label in labels(n) WHERE label IN $old_labels)
            RETURN count(n) as count
        """, old_labels=list(LABEL_MAPPINGS.keys()))
        
        total_count = result.single()['count']
        logger.info(f"Found {total_count} entities to migrate")
        
        if total_count == 0:
            logger.info("No entities to migrate. Exiting.")
            driver.close()
            return
        
        # Ask for confirmation
        response = input(f"\nThis will migrate {total_count} entities to LlamaIndex format. Continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Migration cancelled.")
            driver.close()
            return
        
        # Migrate each entity type
        migrated_count = 0
        
        for old_label, new_label in LABEL_MAPPINGS.items():
            logger.info(f"\nMigrating {old_label} -> :__Entity__:{new_label}")
            
            # First, check if any entities with this label exist
            result = session.run(f"""
                MATCH (n:{old_label})
                RETURN count(n) as count
            """)
            count = result.single()['count']
            
            if count == 0:
                logger.info(f"  No {old_label} entities found, skipping")
                continue
                
            logger.info(f"  Found {count} {old_label} entities")
            
            # Add new labels
            result = session.run(f"""
                MATCH (n:{old_label})
                SET n:__Entity__:{new_label}:__Node__
                RETURN count(n) as updated
            """)
            updated = result.single()['updated']
            logger.info(f"  Added LlamaIndex labels to {updated} entities")
            
            # Remove old label
            result = session.run(f"""
                MATCH (n:{old_label})
                REMOVE n:{old_label}
                RETURN count(n) as updated
            """)
            updated = result.single()['updated']
            logger.info(f"  Removed old label from {updated} entities")
            
            migrated_count += updated
        
        # Verify migration
        logger.info("\n=== MIGRATION COMPLETE ===")
        logger.info(f"Total entities migrated: {migrated_count}")
        
        # Show sample results
        logger.info("\nSample migrated entities:")
        result = session.run("""
            MATCH (n:__Entity__)
            RETURN labels(n) as labels, n.name as name
            LIMIT 10
        """)
        
        for record in result:
            logger.info(f"  {record['name']}: {record['labels']}")
        
        # Show entity counts by type
        logger.info("\nEntity counts by type:")
        result = session.run("""
            MATCH (n:__Entity__)
            UNWIND [label IN labels(n) WHERE label NOT IN ['__Entity__', '__Node__']] as entityType
            RETURN entityType, count(*) as count
            ORDER BY entityType
        """)
        
        for record in result:
            logger.info(f"  {record['entityType']}: {record['count']}")
    
    driver.close()
    logger.info("\nMigration completed successfully!")


def verify_migration():
    """Verify the migration was successful"""
    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'), 
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )
    
    with driver.session() as session:
        # Check for any remaining old labels
        result = session.run("""
            MATCH (n)
            WHERE any(label in labels(n) WHERE label IN $old_labels)
            RETURN count(n) as count
        """, old_labels=list(LABEL_MAPPINGS.keys()))
        
        old_count = result.single()['count']
        
        # Count LlamaIndex entities
        result = session.run("""
            MATCH (n:__Entity__)
            RETURN count(n) as count
        """)
        
        new_count = result.single()['count']
        
        logger.info(f"\nVerification Results:")
        logger.info(f"Entities with old labels: {old_count}")
        logger.info(f"Entities with LlamaIndex labels: {new_count}")
        
        if old_count > 0:
            logger.warning(f"WARNING: {old_count} entities still have old labels!")
        else:
            logger.info("SUCCESS: All entities migrated to LlamaIndex format")
    
    driver.close()


if __name__ == "__main__":
    print("=== SPYRO RAG TO LLAMAINDEX MIGRATION ===")
    print("\nThis script will migrate all existing entities to LlamaIndex schema format.")
    print("For example: :Customer -> :__Entity__:CUSTOMER")
    print("\nIMPORTANT: This will modify your Neo4j database!")
    
    migrate_to_llamaindex()
    verify_migration()