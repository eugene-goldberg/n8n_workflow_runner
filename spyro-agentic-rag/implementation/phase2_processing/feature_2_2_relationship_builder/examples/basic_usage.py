"""Basic usage example for Relationship Builder"""

import asyncio
from datetime import datetime, timedelta
import json

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Entity, Event
from src.relationship_builder import RelationshipBuilder
from src.multi_hop_discoverer import MultiHopRelationshipDiscoverer
from src.temporal_analyzer import TemporalRelationshipAnalyzer
from src.semantic_miner import SemanticRelationshipMiner
from src.pattern_recognizer import GraphPatternRecognizer


async def main():
    """Demonstrate relationship builder capabilities"""
    
    # Create sample entities
    entities = [
        # Customers
        Entity(id="cust_001", type="Customer", attributes={
            "name": "TechCorp",
            "arr": 500000,
            "industry": "technology",
            "status": "active"
        }),
        Entity(id="cust_002", type="Customer", attributes={
            "name": "DataSystems",
            "arr": 300000,
            "industry": "technology",
            "status": "active"
        }),
        
        # Teams
        Entity(id="team_001", type="Team", attributes={
            "name": "Customer Success",
            "manager_id": "person_001",
            "size": 5
        }),
        Entity(id="team_002", type="Team", attributes={
            "name": "Engineering",
            "manager_id": "person_002",
            "size": 10
        }),
        Entity(id="team_003", type="Team", attributes={
            "name": "Support",
            "size": 8
        }),
        
        # People
        Entity(id="person_001", type="Person", attributes={
            "name": "Alice Johnson",
            "role": "CS Manager",
            "team": "Customer Success"
        }),
        Entity(id="person_002", type="Person", attributes={
            "name": "Bob Smith",
            "role": "Engineering Manager",
            "team": "Engineering"
        }),
        
        # Subscriptions
        Entity(id="sub_001", type="Subscription", attributes={
            "customer_id": "cust_001",
            "product_id": "prod_001",
            "value": 100000,
            "start_date": "2024-01-01T00:00:00"
        }),
        Entity(id="sub_002", type="Subscription", attributes={
            "customer_id": "cust_002",
            "product_id": "prod_001",
            "value": 50000,
            "start_date": "2024-02-01T00:00:00"
        }),
        
        # Products
        Entity(id="prod_001", type="Product", attributes={
            "name": "Enterprise Platform",
            "category": "SaaS"
        }),
        
        # Projects
        Entity(id="proj_001", type="Project", attributes={
            "name": "TechCorp Onboarding",
            "customer_id": "cust_001",
            "team_id": "team_001",
            "status": "active"
        }),
        Entity(id="proj_002", type="Project", attributes={
            "name": "Platform Enhancement",
            "team_id": "team_002",
            "status": "active"
        }),
        
        # Risks
        Entity(id="risk_001", type="Risk", attributes={
            "title": "Churn Risk - TechCorp",
            "customer_id": "cust_001",
            "severity": "high",
            "identified_date": "2024-03-01T00:00:00"
        })
    ]
    
    print("=" * 60)
    print("RELATIONSHIP BUILDER DEMO")
    print("=" * 60)
    
    # 1. Build explicit relationships
    print("\n1. Building Explicit Relationships...")
    builder = RelationshipBuilder()
    relationships = await builder.build_relationships(entities)
    
    print(f"Found {len(relationships)} explicit relationships:")
    for rel in relationships[:5]:  # Show first 5
        print(f"  {rel.source.type} '{rel.source.get_name()}' "
              f"-[{rel.relationship_type.value}]-> "
              f"{rel.target.type} '{rel.target.get_name()}'")
    
    # 2. Discover multi-hop relationships
    print("\n2. Discovering Multi-Hop Relationships...")
    multi_hop_discoverer = MultiHopRelationshipDiscoverer()
    multi_hop_rels = await multi_hop_discoverer.discover_multi_hop(
        entities, relationships, max_hops=3
    )
    
    print(f"Found {len(multi_hop_rels)} multi-hop relationships:")
    for rel in multi_hop_rels[:3]:  # Show first 3
        path_str = " -> ".join(e.get_name() for e in rel.path)
        print(f"  {path_str} ({rel.relationship_type.value})")
    
    # 3. Analyze temporal patterns
    print("\n3. Analyzing Temporal Patterns...")
    
    # Create sample events
    base_date = datetime(2024, 1, 1)
    events = []
    
    # Customer activity events
    for i in range(30):
        date = base_date + timedelta(days=i)
        events.append(Event(
            entity_id="cust_001",
            event_type="activity",
            timestamp=date,
            value=100 + i * 5
        ))
        
        # Risk events correlate with customer activity
        if i > 10:
            events.append(Event(
                entity_id="risk_001",
                event_type="severity_change",
                timestamp=date + timedelta(days=7),  # 7-day lag
                value=50 + (i-10) * 3
            ))
    
    temporal_analyzer = TemporalRelationshipAnalyzer()
    temporal_rels = await temporal_analyzer.analyze_temporal_patterns(
        entities, events
    )
    
    print(f"Found {len(temporal_rels)} temporal relationships:")
    for rel in temporal_rels[:3]:
        print(f"  {rel.source.get_name()} {rel.relationship_type.value} "
              f"{rel.target.get_name()} (confidence: {rel.confidence:.2f})")
    
    # 4. Extract semantic relationships
    print("\n4. Extracting Semantic Relationships...")
    
    text = """
    Alice Johnson manages the Customer Success team and works closely with Bob Smith 
    from Engineering. The Customer Success team is responsible for TechCorp's onboarding 
    project. Bob Smith's Engineering team depends on feedback from Customer Success to 
    improve the Enterprise Platform. The platform directly impacts both TechCorp and 
    DataSystems customer experiences.
    """
    
    semantic_miner = SemanticRelationshipMiner()
    semantic_rels = await semantic_miner.mine_from_text(text, entities)
    
    print(f"Found {len(semantic_rels)} semantic relationships from text:")
    for rel in semantic_rels:
        print(f"  {rel.source.get_name()} {rel.relationship_type.value} "
              f"{rel.target.get_name()} (evidence: {rel.evidence[0]})")
    
    # 5. Recognize graph patterns
    print("\n5. Recognizing Graph Patterns...")
    
    # Combine all relationships
    all_relationships = relationships + multi_hop_rels + temporal_rels + semantic_rels
    
    pattern_recognizer = GraphPatternRecognizer()
    patterns = await pattern_recognizer.recognize_patterns(entities, all_relationships)
    
    print(f"Found {len(patterns)} graph patterns:")
    for pattern in patterns[:5]:
        if pattern.pattern_type == "hub":
            central = pattern.get_central_entity()
            print(f"  Hub Pattern: {central.get_name()} connects {len(pattern.entities)-1} entities")
        elif pattern.pattern_type == "triangle":
            names = [e.get_name() for e in pattern.entities]
            print(f"  Triangle Pattern: {' <-> '.join(names)}")
        elif pattern.pattern_type == "community":
            print(f"  Community: {len(pattern.entities)} entities "
                  f"(density: {pattern.metadata.get('density', 0):.2f})")
    
    # 6. Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total Entities: {len(entities)}")
    print(f"Total Relationships: {len(all_relationships)}")
    print(f"Relationship Types: {len(set(r.relationship_type for r in all_relationships))}")
    print(f"Graph Patterns: {len(patterns)}")
    
    # Export sample relationships
    print("\nExporting first 10 relationships to 'relationships_sample.json'...")
    sample_rels = [rel.to_dict() for rel in all_relationships[:10]]
    with open("relationships_sample.json", "w") as f:
        json.dump(sample_rels, f, indent=2, default=str)
    
    print("\nDemo completed!")


if __name__ == "__main__":
    asyncio.run(main())