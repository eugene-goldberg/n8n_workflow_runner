#!/usr/bin/env python3
"""
Clear existing data and add fresh missing data to Neo4j
"""

import os
from neo4j import GraphDatabase

# Neo4j connection
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "password123")

driver = GraphDatabase.driver(uri, auth=(username, password))

def clear_existing_data():
    """Clear existing test data"""
    print("Clearing existing test data...")
    
    with driver.session() as session:
        # Clear existing entities
        entities_to_clear = [
            'SUPPORT_TICKET',
            'INTEGRATION_ISSUE', 
            'EXECUTIVE_SPONSOR',
            'EXTERNAL_DEPENDENCY',
            'SKILL'
        ]
        
        for entity in entities_to_clear:
            result = session.run(f"""
            MATCH (n:__Entity__:{entity})
            WITH n, COUNT(n) as count
            DETACH DELETE n
            RETURN count
            """)
            # Get count before deletion
            count = session.run(f"""
            MATCH (n:__Entity__:{entity})
            RETURN COUNT(n) as count
            """).single()['count']
            # Now delete
            session.run(f"""
            MATCH (n:__Entity__:{entity})
            DETACH DELETE n
            """)
            if count > 0:
                print(f"  Cleared {count} {entity} entities")
        
        # Clear project priorities
        session.run("""
        MATCH (p:__Entity__:PROJECT)
        REMOVE p.priority
        """)
        
        # Clear feature dates
        session.run("""
        MATCH (f:__Entity__:FEATURE)
        REMOVE f.launch_date, f.is_recent, f.quarter_released
        """)
        
        # Clear lifecycle stages
        session.run("""
        MATCH (c:__Entity__:CUSTOMER)
        REMOVE c.lifecycle_stage
        """)
        
        print("✓ Existing data cleared")

def main():
    """Clear and re-add data"""
    print("Refreshing Neo4j test data...")
    print("=" * 50)
    
    try:
        # First clear existing data
        clear_existing_data()
        
        # Then run the add script
        print("\nAdding fresh data...")
        import subprocess
        result = subprocess.run(
            ["python3", "scripts/add_missing_data.py"],
            capture_output=True,
            text=True,
            env={**os.environ}
        )
        
        if result.returncode == 0:
            print(result.stdout)
        else:
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    main()