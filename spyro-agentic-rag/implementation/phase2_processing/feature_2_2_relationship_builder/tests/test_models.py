"""Tests for data models"""

import pytest
from datetime import datetime, timedelta
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    TemporalAspect,
    PathAnalysis,
    TemporalCorrelation,
    GraphPattern,
    CollaborationPattern,
    RelationshipRule,
    RelationshipDiscoveryContext,
    Event,
    EntityMention
)


class TestModels:
    """Test data model functionality"""
    
    def test_entity_creation(self):
        """Test Entity creation and methods"""
        entity = Entity(
            id="test_001",
            type="Customer",
            attributes={"name": "TestCorp", "value": 100000}
        )
        
        assert entity.id == "test_001"
        assert entity.type == "Customer"
        assert entity.get_name() == "TestCorp"
        
        # Test entity without name
        entity2 = Entity(id="test_002", type="Product")
        assert entity2.get_name() == "test_002"  # Falls back to ID
    
    def test_relationship_creation(self):
        """Test Relationship creation"""
        source = Entity(id="s1", type="Source")
        target = Entity(id="t1", type="Target")
        
        rel = Relationship(
            source=source,
            target=target,
            relationship_type=RelationshipType.BELONGS_TO,
            direction=RelationshipDirection.UNIDIRECTIONAL,
            strength=RelationshipStrength.STRONG,
            confidence=0.95,
            evidence=["Test evidence"],
            temporal_aspect=TemporalAspect.PRESENT
        )
        
        assert rel.source.id == "s1"
        assert rel.target.id == "t1"
        assert rel.relationship_type == RelationshipType.BELONGS_TO
        assert rel.confidence == 0.95
        assert len(rel.evidence) == 1
    
    def test_relationship_with_path(self):
        """Test Relationship with multi-hop path"""
        entities = [
            Entity(id=f"e{i}", type=f"Type{i}")
            for i in range(4)
        ]
        
        rel = Relationship(
            source=entities[0],
            target=entities[-1],
            relationship_type=RelationshipType.CONNECTED_VIA,
            path=entities
        )
        
        assert rel.path_length == 4
        assert rel.path == entities
    
    def test_relationship_to_dict(self):
        """Test Relationship serialization"""
        source = Entity(id="s1", type="Source")
        target = Entity(id="t1", type="Target")
        
        rel = Relationship(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS,
            confidence=0.8
        )
        
        rel_dict = rel.to_dict()
        
        assert rel_dict["source_id"] == "s1"
        assert rel_dict["target_id"] == "t1"
        assert rel_dict["relationship_type"] == "IMPACTS"
        assert rel_dict["confidence"] == 0.8
        assert "discovered_at" in rel_dict
    
    def test_path_analysis(self):
        """Test PathAnalysis functionality"""
        path = [
            Entity(id="a", type="A"),
            Entity(id="b", type="B"),
            Entity(id="c", type="C")
        ]
        
        analysis = PathAnalysis(
            path=path,
            score=0.75,
            interpretation="A influences C through B",
            edge_strengths=[0.8, 0.7],
            bottlenecks=[(path[1], path[2])]
        )
        
        assert analysis.score == 0.75
        assert len(analysis.edge_strengths) == 2
        
        # Test weakest link detection
        weakest = analysis.get_weakest_link()
        assert weakest == (path[1], path[2])
    
    def test_temporal_correlation(self):
        """Test TemporalCorrelation functionality"""
        entity1 = Entity(id="e1", type="Metric")
        entity2 = Entity(id="e2", type="Metric")
        
        correlation = TemporalCorrelation(
            entity1=entity1,
            entity2=entity2,
            correlation_coefficient=0.85,
            optimal_lag_days=7,
            causality_score=0.9,
            confidence=0.8,
            events_analyzed=100
        )
        
        assert correlation.is_causal(threshold=0.8)
        assert correlation.is_significant(threshold=0.8)
        
        # Test with lower scores
        correlation2 = TemporalCorrelation(
            entity1=entity1,
            entity2=entity2,
            correlation_coefficient=0.4,
            optimal_lag_days=0,
            causality_score=0.3,
            confidence=0.5
        )
        
        assert not correlation2.is_causal()
        assert not correlation2.is_significant()
    
    def test_graph_pattern(self):
        """Test GraphPattern functionality"""
        entities = [
            Entity(id="hub", type="Hub"),
            Entity(id="spoke1", type="Spoke"),
            Entity(id="spoke2", type="Spoke")
        ]
        
        pattern = GraphPattern(
            pattern_type="hub",
            entities=entities,
            centrality_scores={
                "hub": 0.9,
                "spoke1": 0.3,
                "spoke2": 0.3
            }
        )
        
        central = pattern.get_central_entity()
        assert central is not None
        assert central.id == "hub"
    
    def test_collaboration_pattern(self):
        """Test CollaborationPattern functionality"""
        entities = [
            Entity(id="t1", type="Team"),
            Entity(id="t2", type="Team"),
            Entity(id="t3", type="Team")
        ]
        
        pattern = CollaborationPattern(
            pattern_type="triangle",
            entities=entities,
            collaboration_strength=0.8,
            supporting_evidence=["Regular meetings", "Shared projects"],
            collaboration_type="inter_team"
        )
        
        assert pattern.indicates_collaboration
        assert pattern.collaboration_strength == 0.8
        assert len(pattern.supporting_evidence) == 2
    
    def test_relationship_rule(self):
        """Test RelationshipRule functionality"""
        rule = RelationshipRule(
            source_type="Subscription",
            field="customer_id",
            target_type="Customer",
            relationship=RelationshipType.BELONGS_TO,
            bidirectional=False
        )
        
        # Test matching entity
        matching_entity = Entity(
            id="sub1",
            type="Subscription",
            attributes={"customer_id": "cust1"}
        )
        assert rule.matches(matching_entity)
        
        # Test non-matching entity (wrong type)
        non_matching1 = Entity(
            id="cust1",
            type="Customer",
            attributes={"customer_id": "cust2"}
        )
        assert not rule.matches(non_matching1)
        
        # Test non-matching entity (missing field)
        non_matching2 = Entity(
            id="sub2",
            type="Subscription",
            attributes={"product_id": "prod1"}
        )
        assert not rule.matches(non_matching2)
    
    def test_discovery_context(self):
        """Test RelationshipDiscoveryContext functionality"""
        context = RelationshipDiscoveryContext(
            min_confidence=0.7,
            exclude_types={RelationshipType.PRECEDES},
            focus_entities={"e1", "e2"}
        )
        
        # Test relationship filtering
        source = Entity(id="e1", type="E")
        target = Entity(id="e3", type="E")
        
        # Should include: high confidence, not excluded type, has focus entity
        rel1 = Relationship(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS,
            confidence=0.8
        )
        assert context.should_include_relationship(rel1)
        
        # Should exclude: low confidence
        rel2 = Relationship(
            source=source,
            target=target,
            relationship_type=RelationshipType.IMPACTS,
            confidence=0.5
        )
        assert not context.should_include_relationship(rel2)
        
        # Should exclude: excluded type
        rel3 = Relationship(
            source=source,
            target=target,
            relationship_type=RelationshipType.PRECEDES,
            confidence=0.9
        )
        assert not context.should_include_relationship(rel3)
    
    def test_event_model(self):
        """Test Event functionality"""
        now = datetime.now()
        event1 = Event(
            entity_id="e1",
            event_type="status_change",
            timestamp=now,
            value=100,
            metadata={"old_status": "active", "new_status": "inactive"}
        )
        
        event2 = Event(
            entity_id="e2",
            event_type="value_update",
            timestamp=now + timedelta(days=5)
        )
        
        # Test days between calculation
        days = event1.days_between(event2)
        assert days == 5
    
    def test_entity_mention(self):
        """Test EntityMention functionality"""
        mention = EntityMention(
            entity_id="e1",
            entity_type="Person",
            surface_form="Alice Johnson",
            start_pos=10,
            end_pos=23,
            confidence=0.95
        )
        
        assert mention.span == (10, 23)
        assert mention.confidence == 0.95
        assert mention.surface_form == "Alice Johnson"
    
    def test_relationship_type_enum(self):
        """Test RelationshipType enum values"""
        # Test explicit relationships
        assert RelationshipType.BELONGS_TO.value == "BELONGS_TO"
        assert RelationshipType.MANAGED_BY.value == "MANAGED_BY"
        
        # Test inferred relationships
        assert RelationshipType.IMPACTS.value == "IMPACTS"
        assert RelationshipType.CORRELATES_WITH.value == "CORRELATES_WITH"
        
        # Test multi-hop relationships
        assert RelationshipType.INDIRECTLY_AFFECTS.value == "INDIRECTLY_AFFECTS"
        assert RelationshipType.CONNECTED_VIA.value == "CONNECTED_VIA"
    
    def test_temporal_aspect_enum(self):
        """Test TemporalAspect enum values"""
        assert TemporalAspect.PAST.value == "PAST"
        assert TemporalAspect.PRESENT.value == "PRESENT"
        assert TemporalAspect.FUTURE.value == "FUTURE"
        assert TemporalAspect.ONGOING.value == "ONGOING"