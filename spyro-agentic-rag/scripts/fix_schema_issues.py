#!/usr/bin/env python3
"""Fix remaining schema issues"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.config import Config
from neo4j import GraphDatabase

config = Config.from_env()
driver = GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password))

with driver.session(database=config.neo4j_database) as session:
    print("Fixing remaining schema issues...")
    
    # Fix team revenue metric syntax
    session.run("""
        MATCH (t:Team) WHERE t.revenue_supported IS NOT NULL
        RETURN count(t) as count
    """)
    
    # Create FeatureUsage properly (seems the relationships weren't matching)
    print("\nCreating FeatureUsage nodes...")
    result = session.run("""
        MATCH (p:Product)-[:HAS_FEATURE]->(f:Feature)
        WITH p, f, 
             CASE p.name 
                WHEN 'SpyroCloud' THEN 
                    CASE f.name
                        WHEN 'Auto-scaling' THEN {adoption: 0.85, value: 9.2}
                        WHEN 'Multi-region deployment' THEN {adoption: 0.45, value: 8.7}
                        WHEN 'Real-time monitoring' THEN {adoption: 0.92, value: 9.5}
                        ELSE {adoption: 0.5, value: 7.0}
                    END
                WHEN 'SpyroAI' THEN
                    CASE f.name
                        WHEN 'Predictive analytics' THEN {adoption: 0.72, value: 9.3}
                        WHEN 'Machine learning' THEN {adoption: 0.38, value: 8.5}
                        WHEN 'Natural language processing' THEN {adoption: 0.81, value: 9.1}
                        ELSE {adoption: 0.4, value: 7.5}
                    END
                WHEN 'SpyroSecure' THEN
                    CASE f.name
                        WHEN 'Threat detection' THEN {adoption: 0.95, value: 9.8}
                        WHEN 'Compliance automation' THEN {adoption: 0.88, value: 9.0}
                        WHEN 'Access control' THEN {adoption: 0.91, value: 9.4}
                        ELSE {adoption: 0.6, value: 8.0}
                    END
                ELSE {adoption: 0.5, value: 7.5}
             END as metrics
        CREATE (fu:FeatureUsage {
            adoption_rate: metrics.adoption,
            value_score: metrics.value,
            active_users: toInteger(metrics.adoption * 1000),
            last_updated: date(),
            released_date: date() - duration({months: 6})
        })
        CREATE (f)-[:HAS_USAGE]->(fu)
        RETURN count(fu) as created
    """)
    
    count = list(result)[0]['created']
    print(f"Created {count} FeatureUsage nodes")
    
    # Create CompetitiveAdvantage nodes
    print("\nCreating CompetitiveAdvantage nodes...")
    advantages = [
        ("SpyroCloud", "Auto-scaling", "+15% faster", "Enterprise"),
        ("SpyroCloud", "Multi-region deployment", "3x locations", "Global"),
        ("SpyroAI", "Predictive analytics", "10x faster", "FinTech"),
        ("SpyroAI", "Machine learning", "No-code approach", "SMB"),
        ("SpyroSecure", "Threat detection", "ML-powered", "Enterprise"),
        ("SpyroSecure", "Compliance automation", "Auto-generated", "Healthcare")
    ]
    
    for product, feature, advantage, segment in advantages:
        session.run("""
            MATCH (p:Product {name: $product})-[:HAS_FEATURE]->(f:Feature {name: $feature})
            CREATE (ca:CompetitiveAdvantage {
                vs_industry: $advantage,
                market_segment: $segment,
                created_date: date()
            })
            CREATE (f)-[:PROVIDES_ADVANTAGE]->(ca)
            MERGE (ms:MarketSegment {name: $segment})
            CREATE (ca)-[:IN_SEGMENT]->(ms)
        """, {
            "product": product,
            "feature": feature,
            "advantage": advantage,
            "segment": segment
        })
    
    print("Created CompetitiveAdvantage nodes")
    
    # Verify all is well
    print("\nVerifying fixes...")
    checks = [
        ("FeatureUsage", "MATCH (fu:FeatureUsage) RETURN count(fu) as count"),
        ("CompetitiveAdvantage", "MATCH (ca:CompetitiveAdvantage) RETURN count(ca) as count"),
        ("Team revenue metrics", "MATCH (t:Team) WHERE t.revenue_supported IS NOT NULL RETURN count(t) as count")
    ]
    
    for name, query in checks:
        result = session.run(query)
        count = list(result)[0]['count']
        print(f"✓ {name}: {count}")

driver.close()
print("\n✅ Schema fixes complete!")