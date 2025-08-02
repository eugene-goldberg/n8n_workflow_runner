"""Tests for MultiHopRelationshipDiscoverer"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    PathAnalysis
)
from src.multi_hop_discoverer import MultiHopRelationshipDiscoverer


class TestMultiHopDiscoverer:
    """Test MultiHopRelationshipDiscoverer functionality"""
    
    @pytest.fixture
    def discoverer(self):
        """Create MultiHopRelationshipDiscoverer instance"""
        return MultiHopRelationshipDiscoverer()
    
    @pytest.fixture
    def sample_entities(self):
        """Create sample entities for testing"""
        return [
            Entity(id="cust_001", type="Customer", attributes={"name": "TechCorp"}),
            Entity(id="proj_001", type="Project", attributes={"name": "Migration"}),
            Entity(id="team_001", type="Team", attributes={"name": "Engineering"}),
            Entity(id="risk_001", type="Risk", attributes={"title": "Delay Risk"}),
            Entity(id="obj_001", type="Objective", attributes={"title": "Q4 Goals"}),
            Entity(id="person_001", type="Person", attributes={"name": "Alice"})
        ]
    
    @pytest.fixture
    def sample_relationships(self):
        """Create sample direct relationships"""
        return [
            Relationship(
                source=Entity(id="cust_001", type="Customer"),
                target=Entity(id="proj_001", type="Project"),
                relationship_type=RelationshipType.OWNS,
                confidence=0.9
            ),
            Relationship(
                source=Entity(id="proj_001", type="Project"),
                target=Entity(id="team_001", type="Team"),
                relationship_type=RelationshipType.ASSIGNED_TO,
                confidence=0.95
            ),
            Relationship(
                source=Entity(id="team_001", type="Team"),
                target=Entity(id="obj_001", type="Objective"),
                relationship_type=RelationshipType.RESPONSIBLE_FOR,
                confidence=0.8
            ),
            Relationship(
                source=Entity(id="risk_001", type="Risk"),
                target=Entity(id="proj_001", type="Project"),
                relationship_type=RelationshipType.IMPACTS,
                confidence=0.85
            )
        ]
    
    @pytest.mark.asyncio
    async def test_discover_multi_hop_basic(self, discoverer, sample_entities, sample_relationships):
        """Test basic multi-hop discovery"""
        multi_hop_rels = await discoverer.discover_multi_hop(
            sample_entities,
            sample_relationships,
            max_hops=3
        )
        
        # Should discover customer->team relationship via project
        cust_team_rels = [
            r for r in multi_hop_rels
            if r.source.id == "cust_001" and r.target.id == "team_001"
        ]
        assert len(cust_team_rels) > 0
        
        rel = cust_team_rels[0]
        assert len(rel.path) == 3  # Customer -> Project -> Team
        assert rel.path[0].id == "cust_001"
        assert rel.path[1].id == "proj_001"
        assert rel.path[2].id == "team_001"
    
    @pytest.mark.asyncio
    async def test_path_analysis(self, discoverer, sample_entities, sample_relationships):
        """Test path analysis functionality"""
        # Build graph
        discoverer._build_graph(sample_entities, sample_relationships)
        
        # Create path
        path = [
            Entity(id="cust_001", type="Customer"),
            Entity(id="proj_001", type="Project"),
            Entity(id="team_001", type="Team")
        ]
        
        analysis = await discoverer._analyze_path(path)
        
        assert isinstance(analysis, PathAnalysis)
        assert analysis.score > 0
        assert len(analysis.edge_strengths) == 2
        assert analysis.interpretation != ""
    
    @pytest.mark.asyncio
    async def test_max_hops_limit(self, discoverer, sample_entities, sample_relationships):
        """Test max hops limitation"""
        # Test with max_hops=2
        multi_hop_rels = await discoverer.discover_multi_hop(
            sample_entities,
            sample_relationships,
            max_hops=2
        )
        
        # Should not find paths longer than 2 hops
        for rel in multi_hop_rels:
            assert len(rel.path) <= 3  # max 2 hops = 3 nodes
    
    @pytest.mark.asyncio
    async def test_path_strength_filtering(self, discoverer, sample_entities, sample_relationships):
        """Test filtering by path strength"""
        # Set high minimum path strength
        discoverer.config["min_path_strength"] = 0.9
        
        multi_hop_rels = await discoverer.discover_multi_hop(
            sample_entities,
            sample_relationships
        )
        
        # All relationships should have high confidence
        for rel in multi_hop_rels:
            assert rel.confidence >= 0.9
    
    @pytest.mark.asyncio
    async def test_risk_cascade_detection(self, discoverer, sample_entities, sample_relationships):
        """Test detection of risk cascades"""
        multi_hop_rels = await discoverer.discover_multi_hop(
            sample_entities,
            sample_relationships
        )
        
        # Should find risk->customer relationship via project
        risk_cust_rels = [
            r for r in multi_hop_rels
            if r.source.id == "risk_001" and r.target.id == "cust_001"
        ]
        
        assert len(risk_cust_rels) > 0
        rel = risk_cust_rels[0]
        assert rel.relationship_type == RelationshipType.INDIRECTLY_AFFECTS
    
    @pytest.mark.asyncio
    async def test_bottleneck_detection(self, discoverer):
        """Test bottleneck detection in paths"""
        # Create path with varying edge strengths
        path = [
            Entity(id="a", type="A"),
            Entity(id="b", type="B"),
            Entity(id="c", type="C"),
            Entity(id="d", type="D")
        ]
        
        edge_strengths = [0.9, 0.3, 0.8]  # Middle edge is weak
        
        analysis = PathAnalysis(
            path=path,
            score=0.6,
            interpretation="Test path",
            edge_strengths=edge_strengths
        )
        
        bottlenecks = discoverer._find_bottlenecks(path, edge_strengths)
        
        assert len(bottlenecks) > 0
        # Weak link should be between b and c
        assert bottlenecks[0] == (path[1], path[2])
    
    @pytest.mark.asyncio
    async def test_interesting_targets_selection(self, discoverer, sample_entities):
        """Test selection of interesting target entities"""
        # Build a simple graph
        relationships = [
            Relationship(
                source=Entity(id="cust_001", type="Customer"),
                target=Entity(id="proj_001", type="Project"),
                relationship_type=RelationshipType.OWNS
            )
        ]
        
        discoverer._build_graph(sample_entities, relationships)
        
        source = sample_entities[0]  # Customer
        targets = discoverer._find_interesting_targets(source, sample_entities)
        
        # Should prioritize different entity types
        target_types = [t.type for t in targets]
        assert "Customer" not in target_types[:3]  # Same type should be lower priority
        
        # Should not include direct neighbors
        assert "proj_001" not in [t.id for t in targets]
    
    @pytest.mark.asyncio
    async def test_business_relevance_check(self, discoverer):
        """Test business relevance checking"""
        entity1 = Entity(
            id="team_a",
            type="Team",
            attributes={"industry": "tech", "region": "US"}
        )
        entity2 = Entity(
            id="team_b",
            type="Team",
            attributes={"industry": "tech", "region": "EU"}
        )
        entity3 = Entity(
            id="team_c",
            type="Team",
            attributes={"industry": "finance", "region": "US"}
        )
        
        # Same industry should be relevant
        assert discoverer._has_business_relevance(entity1, entity2) == True
        
        # Same region should be relevant
        assert discoverer._has_business_relevance(entity1, entity3) == True
        
        # No shared attributes
        entity4 = Entity(
            id="team_d",
            type="Team",
            attributes={"department": "HR"}
        )
        assert discoverer._has_business_relevance(entity1, entity4) == False
    
    @pytest.mark.asyncio
    async def test_path_interpretation(self, discoverer):
        """Test path interpretation logic"""
        # Test known pattern
        path1 = [
            Entity(id="c", type="Customer"),
            Entity(id="p", type="Project"),
            Entity(id="t", type="Team")
        ]
        
        interpretation1 = discoverer._simple_path_interpretation(path1)
        assert "Customer connected to Team through Project" in interpretation1
        
        # Test risk pattern
        path2 = [
            Entity(id="r", type="Risk"),
            Entity(id="c", type="Customer"),
            Entity(id="s", type="Subscription")
        ]
        
        interpretation2 = discoverer._simple_path_interpretation(path2)
        assert "Risk impacts Customer's Subscription" in interpretation2
    
    @pytest.mark.asyncio
    async def test_multi_hop_relationship_creation(self, discoverer):
        """Test creation of multi-hop relationships"""
        source = Entity(id="cust", type="Customer", attributes={"name": "TestCorp"})
        target = Entity(id="team", type="Team", attributes={"name": "Support"})
        path = [
            source,
            Entity(id="proj", type="Project"),
            target
        ]
        
        analysis = PathAnalysis(
            path=path,
            score=0.75,
            interpretation="Customer to Team via Project",
            edge_strengths=[0.8, 0.7]
        )
        
        rel = discoverer._create_multi_hop_relationship(
            source, target, path, analysis
        )
        
        assert rel.source.id == "cust"
        assert rel.target.id == "team"
        assert rel.relationship_type == RelationshipType.CONNECTED_VIA
        assert rel.path == path
        assert rel.path_length == 3
        assert rel.confidence == 0.75
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, discoverer, sample_entities, sample_relationships):
        """Test path caching"""
        discoverer.config["performance"]["cache_paths"] = True
        
        # First discovery
        await discoverer.discover_multi_hop(
            sample_entities,
            sample_relationships
        )
        
        # Cache should be populated
        assert len(discoverer._path_cache) > 0
        
        # Clear cache
        discoverer.clear_cache()
        assert len(discoverer._path_cache) == 0
    
    @pytest.mark.asyncio
    async def test_get_path_between(self, discoverer, sample_entities, sample_relationships):
        """Test getting specific path between entities"""
        discoverer._build_graph(sample_entities, sample_relationships)
        
        path = discoverer.get_path_between("cust_001", "team_001")
        
        assert path is not None
        assert len(path) == 3
        assert path[0].id == "cust_001"
        assert path[-1].id == "team_001"
        
        # Test non-existent path
        no_path = discoverer.get_path_between("cust_001", "person_001")
        assert no_path is None
    
    @pytest.mark.asyncio
    async def test_empty_inputs(self, discoverer):
        """Test with empty inputs"""
        # Empty entities
        result1 = await discoverer.discover_multi_hop([], [])
        assert result1 == []
        
        # Empty relationships
        entities = [Entity(id="e1", type="E")]
        result2 = await discoverer.discover_multi_hop(entities, [])
        assert result2 == []