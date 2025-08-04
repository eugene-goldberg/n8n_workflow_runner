#!/usr/bin/env python3
"""Test Cypher query for events question"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config.settings import settings
from datetime import datetime, timedelta

def test_events_cypher():
    """Test the Cypher query for finding customers with negative events"""
    driver = GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password)
    )
    
    with driver.session() as session:
        print("=== TESTING EVENTS CYPHER QUERY ===\n")
        
        # Calculate 90 days ago
        ninety_days_ago = datetime.now() - timedelta(days=90)
        print(f"Looking for events after: {ninety_days_ago.date()}\n")
        
        # First, let's see what EXPERIENCED relationships exist
        print("1. Checking EXPERIENCED relationships:")
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[:EXPERIENCED]->(e:__Entity__:EVENT)
            RETURN c.name as customer, e.type as event_type, e.impact as impact, e.timestamp as timestamp
        """)
        for record in result:
            print(f"   {record['customer']} experienced {record['event_type']} (impact: {record['impact']})")
        
        # Now the main query - count all customers and those with negative events
        print("\n2. Main query - percentage of customers with negative events in last 90 days:")
        
        # Since EXPERIENCED relationships are limited, let's use a broader approach
        # First try with actual 90 days, then with all available data
        query = """
        // Count total customers
        MATCH (c:__Entity__:CUSTOMER)
        WITH count(DISTINCT c) as total_customers
        
        // Find customers with negative events (checking both impact and severity)
        OPTIONAL MATCH (c2:__Entity__:CUSTOMER)-[:EXPERIENCED]->(e:__Entity__:EVENT)
        WHERE (e.impact = 'negative' OR e.impact = 'High' OR e.severity IN ['high', 'critical', 'medium'])
        WITH total_customers, count(DISTINCT c2) as customers_with_negative_events
        
        RETURN 
            total_customers,
            customers_with_negative_events,
            CASE 
                WHEN total_customers > 0 
                THEN (customers_with_negative_events * 100.0 / total_customers) 
                ELSE 0 
            END as percentage
        """
        
        result = session.run(query, ninety_days_ago=ninety_days_ago.isoformat())
        record = result.single()
        
        print(f"   Total customers: {record['total_customers']}")
        print(f"   Customers with negative events: {record['customers_with_negative_events']}")
        print(f"   Percentage: {record['percentage']:.2f}%")
        
        # Alternative: Check if events might be linked differently
        print("\n3. Checking all negative events in the system (last 90 days):")
        result = session.run("""
            MATCH (e:__Entity__:EVENT)
            WHERE (e.impact = 'negative' OR e.severity IN ['high', 'critical', 'medium'])
            AND e.timestamp >= datetime($ninety_days_ago)
            RETURN count(e) as negative_event_count
        """, ninety_days_ago=ninety_days_ago.isoformat())
        record = result.single()
        print(f"   Total negative events in last 90 days: {record['negative_event_count']}")
        
    driver.close()

if __name__ == "__main__":
    test_events_cypher()