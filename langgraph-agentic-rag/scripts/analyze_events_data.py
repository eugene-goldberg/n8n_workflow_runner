#!/usr/bin/env python3
"""Analyze events data structure in Neo4j"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from config.settings import settings
from datetime import datetime, timedelta

def analyze_events_data():
    """Analyze how events are structured in the database"""
    driver = GraphDatabase.driver(
        settings.neo4j.uri,
        auth=(settings.neo4j.username, settings.neo4j.password)
    )
    
    with driver.session() as session:
        print("=== ANALYZING EVENTS DATA ===\n")
        
        # Check EVENT entities without embeddings
        print("1. EVENT entities (with and without embeddings):")
        result = session.run("""
            MATCH (e:__Entity__:EVENT)
            RETURN 
                count(e) as total,
                count(e.embedding) as with_embeddings,
                collect(DISTINCT e.type) as event_types
        """)
        record = result.single()
        print(f"   Total events: {record['total']}")
        print(f"   With embeddings: {record['with_embeddings']}")
        print(f"   Event types: {record['event_types']}")
        
        # Sample some events
        print("\n2. Sample EVENT entities:")
        result = session.run("""
            MATCH (e:__Entity__:EVENT)
            WHERE e.type IS NOT NULL
            RETURN 
                e.name as name,
                e.type as type,
                e.description as description,
                e.impact as impact,
                e.severity as severity,
                e.timestamp as timestamp,
                e.date as date
            LIMIT 10
        """)
        for record in result:
            print(f"\n   Event: {record['name'] or 'Unnamed'}")
            print(f"   - Type: {record['type']}")
            print(f"   - Description: {record['description']}")
            print(f"   - Impact: {record['impact']}")
            print(f"   - Severity: {record['severity']}")
            print(f"   - Timestamp: {record['timestamp']}")
            print(f"   - Date: {record['date']}")
        
        # Check relationships to customers
        print("\n\n3. Events related to customers:")
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[r]-(e:__Entity__:EVENT)
            RETURN 
                type(r) as relationship,
                count(*) as count
        """)
        for record in result:
            print(f"   {record['relationship']}: {record['count']} relationships")
        
        # Try to find customer-event connections via MENTIONS
        print("\n\n4. Customer-Event connections via MENTIONS:")
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[:MENTIONS]-(e:__Entity__:EVENT)
            RETURN 
                c.name as customer,
                e.type as event_type,
                e.severity as severity,
                e.timestamp as timestamp
            LIMIT 10
        """)
        count = 0
        for record in result:
            count += 1
            print(f"\n   Customer: {record['customer']}")
            print(f"   - Event type: {record['event_type']}")
            print(f"   - Severity: {record['severity']}")
            print(f"   - Timestamp: {record['timestamp']}")
        
        if count == 0:
            print("   No direct MENTIONS relationships found between customers and events")
        
        # Calculate 90-day window
        ninety_days_ago = datetime.now() - timedelta(days=90)
        
        # Check events in last 90 days (if timestamps are parseable)
        print("\n\n5. Recent events analysis:")
        result = session.run("""
            MATCH (e:__Entity__:EVENT)
            WHERE e.timestamp IS NOT NULL OR e.date IS NOT NULL
            WITH e, 
                 CASE 
                    WHEN e.timestamp =~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}.*' THEN datetime(e.timestamp)
                    WHEN e.date =~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}.*' THEN datetime(e.date)
                    ELSE null
                 END as event_datetime
            WHERE event_datetime IS NOT NULL
            RETURN 
                count(e) as total_dated_events,
                count(CASE WHEN event_datetime > datetime($ninety_days_ago) THEN 1 END) as recent_events,
                count(CASE WHEN e.severity = 'negative' OR e.impact = 'negative' THEN 1 END) as negative_events
        """, ninety_days_ago=ninety_days_ago.isoformat())
        record = result.single()
        if record:
            print(f"   Total events with dates: {record['total_dated_events']}")
            print(f"   Events in last 90 days: {record['recent_events']}")
            print(f"   Negative events: {record['negative_events']}")
        
        # Try different approach - find all customer mentions
        print("\n\n6. All entities mentioned by customers:")
        result = session.run("""
            MATCH (c:__Entity__:CUSTOMER)-[:MENTIONS]-(other)
            RETURN 
                labels(other) as entity_types,
                count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        for record in result:
            print(f"   {record['entity_types']}: {record['count']} mentions")
            
    driver.close()

if __name__ == "__main__":
    analyze_events_data()