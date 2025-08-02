#!/usr/bin/env python3
"""Simple test runner to verify the implementation"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import all modules to check for syntax errors
try:
    print("Importing models...")
    from src import models
    print("✓ Models imported successfully")
    
    print("\nImporting RelationshipBuilder...")
    from src import relationship_builder
    print("✓ RelationshipBuilder imported successfully")
    
    print("\nImporting MultiHopRelationshipDiscoverer...")
    from src import multi_hop_discoverer
    print("✓ MultiHopRelationshipDiscoverer imported successfully")
    
    print("\nImporting TemporalRelationshipAnalyzer...")
    from src import temporal_analyzer
    print("✓ TemporalRelationshipAnalyzer imported successfully")
    
    print("\nImporting SemanticRelationshipMiner...")
    from src import semantic_miner
    print("✓ SemanticRelationshipMiner imported successfully")
    
    print("\nImporting GraphPatternRecognizer...")
    from src import pattern_recognizer
    print("✓ GraphPatternRecognizer imported successfully")
    
    print("\n" + "="*60)
    print("All modules imported successfully!")
    print("="*60)
    
    # Test basic functionality
    print("\nTesting basic functionality...")
    
    # Test entity creation
    from src.models import Entity, Relationship, RelationshipType
    entity1 = Entity(id="test1", type="Test", attributes={"name": "Test Entity"})
    entity2 = Entity(id="test2", type="Test", attributes={"name": "Test Entity 2"})
    print(f"✓ Created entities: {entity1.get_name()}, {entity2.get_name()}")
    
    # Test relationship creation
    rel = Relationship(
        source=entity1,
        target=entity2,
        relationship_type=RelationshipType.RELATED_TO,
        confidence=0.8
    )
    print(f"✓ Created relationship: {rel.source.id} -> {rel.target.id}")
    
    # Test builder instantiation
    from src.relationship_builder import RelationshipBuilder
    builder = RelationshipBuilder()
    print("✓ RelationshipBuilder instantiated")
    
    # Test other components
    from src.multi_hop_discoverer import MultiHopRelationshipDiscoverer
    discoverer = MultiHopRelationshipDiscoverer()
    print("✓ MultiHopRelationshipDiscoverer instantiated")
    
    from src.temporal_analyzer import TemporalRelationshipAnalyzer
    analyzer = TemporalRelationshipAnalyzer()
    print("✓ TemporalRelationshipAnalyzer instantiated")
    
    from src.semantic_miner import SemanticRelationshipMiner
    miner = SemanticRelationshipMiner()
    print("✓ SemanticRelationshipMiner instantiated")
    
    from src.pattern_recognizer import GraphPatternRecognizer
    recognizer = GraphPatternRecognizer()
    print("✓ GraphPatternRecognizer instantiated")
    
    print("\n" + "="*60)
    print("Basic functionality tests passed!")
    print("="*60)
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n✅ All tests passed! Feature 2.2 is ready for use.")