"""Tests for GraphPatternRecognizer"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipStrength,
    GraphPattern,
    CollaborationPattern
)
from src.pattern_recognizer import GraphPatternRecognizer


class TestPatternRecognizer:
    """Test GraphPatternRecognizer functionality"""
    
    @pytest.fixture
    def recognizer(self):
        """Create GraphPatternRecognizer instance"""
        return GraphPatternRecognizer()
    
    @pytest.fixture
    def hub_entities_and_relationships(self):
        """Create entities and relationships forming a hub pattern"""
        hub = Entity(id="hub_001", type="Customer", attributes={"name": "MegaCorp"})
        spokes = [
            Entity(id="sub_001", type="Subscription", attributes={"name": "Premium"}),
            Entity(id="team_001", type="Team", attributes={"name": "Support"}),
            Entity(id="team_002", type="Team", attributes={"name": "Success"}),
            Entity(id="risk_001", type="Risk", attributes={"title": "Churn Risk"}),
            Entity(id="proj_001", type="Project", attributes={"name": "Onboarding"}),
            Entity(id="tick_001", type="Ticket", attributes={"title": "Issue #1"})
        ]
        
        entities = [hub] + spokes
        
        relationships = []
        for spoke in spokes:
            relationships.append(
                Relationship(
                    source=spoke,
                    target=hub,
                    relationship_type=RelationshipType.BELONGS_TO,
                    confidence=0.9,
                    strength=RelationshipStrength.STRONG
                )
            )
        
        return entities, relationships
    
    @pytest.fixture
    def triangle_entities_and_relationships(self):
        """Create entities and relationships forming triangles"""
        entities = [
            Entity(id="team_a", type="Team", attributes={"name": "Team Alpha"}),
            Entity(id="team_b", type="Team", attributes={"name": "Team Beta"}),
            Entity(id="team_c", type="Team", attributes={"name": "Team Gamma"}),
            Entity(id="proj", type="Project", attributes={"name": "Joint Project"})
        ]
        
        relationships = [
            # Triangle between teams
            Relationship(
                source=entities[0], target=entities[1],
                relationship_type=RelationshipType.COLLABORATES_WITH,
                confidence=0.8
            ),
            Relationship(
                source=entities[1], target=entities[2],
                relationship_type=RelationshipType.COLLABORATES_WITH,
                confidence=0.8
            ),
            Relationship(
                source=entities[0], target=entities[2],
                relationship_type=RelationshipType.WORKS_WITH,
                confidence=0.7
            ),
            # All teams connected to project
            Relationship(
                source=entities[0], target=entities[3],
                relationship_type=RelationshipType.ASSIGNED_TO,
                confidence=0.9
            ),
            Relationship(
                source=entities[1], target=entities[3],
                relationship_type=RelationshipType.ASSIGNED_TO,
                confidence=0.9
            )
        ]
        
        return entities, relationships
    
    @pytest.mark.asyncio
    async def test_hub_detection(self, recognizer, hub_entities_and_relationships):
        """Test hub pattern detection"""
        entities, relationships = hub_entities_and_relationships
        
        patterns = await recognizer.recognize_patterns(entities, relationships)
        
        # Should detect hub pattern
        hub_patterns = [p for p in patterns if p.pattern_type == "hub"]
        assert len(hub_patterns) > 0
        
        hub_pattern = hub_patterns[0]
        assert hub_pattern.get_central_entity().id == "hub_001"
        assert len(hub_pattern.entities) > recognizer.config["patterns"]["hub_detection"]["min_connections"]
    
    @pytest.mark.asyncio
    async def test_triangle_detection(self, recognizer, triangle_entities_and_relationships):
        """Test triangle pattern detection"""
        entities, relationships = triangle_entities_and_relationships
        
        patterns = await recognizer.recognize_patterns(entities, relationships)
        
        # Should detect triangle patterns
        triangle_patterns = [p for p in patterns if p.pattern_type == "triangle"]
        assert len(triangle_patterns) > 0
        
        # Check collaboration pattern
        collab_patterns = [
            p for p in triangle_patterns
            if isinstance(p, CollaborationPattern)
        ]
        assert len(collab_patterns) > 0
        
        pattern = collab_patterns[0]
        assert pattern.indicates_collaboration
        assert len(pattern.entities) == 3
    
    @pytest.mark.asyncio
    async def test_community_detection(self, recognizer):
        """Test community detection"""
        # Create a community structure
        community1 = [
            Entity(id=f"c1_e{i}", type="Person", attributes={"name": f"Person {i}"})
            for i in range(5)
        ]
        community2 = [
            Entity(id=f"c2_e{i}", type="Person", attributes={"name": f"Person {i+5}"})
            for i in range(4)
        ]
        
        entities = community1 + community2
        relationships = []
        
        # Dense connections within communities
        for i in range(len(community1)):
            for j in range(i+1, len(community1)):
                relationships.append(
                    Relationship(
                        source=community1[i],
                        target=community1[j],
                        relationship_type=RelationshipType.WORKS_WITH,
                        confidence=0.9
                    )
                )
        
        for i in range(len(community2)):
            for j in range(i+1, len(community2)):
                relationships.append(
                    Relationship(
                        source=community2[i],
                        target=community2[j],
                        relationship_type=RelationshipType.WORKS_WITH,
                        confidence=0.9
                    )
                )
        
        # Sparse connections between communities
        relationships.append(
            Relationship(
                source=community1[0],
                target=community2[0],
                relationship_type=RelationshipType.RELATED_TO,
                confidence=0.5
            )
        )
        
        patterns = await recognizer.recognize_patterns(entities, relationships)
        
        # Should detect at least 2 communities
        community_patterns = [p for p in patterns if p.pattern_type == "community"]
        assert len(community_patterns) >= 2
    
    @pytest.mark.asyncio
    async def test_chain_detection(self, recognizer):
        """Test chain pattern detection"""
        # Create a chain of entities
        chain_entities = []
        for i in range(6):
            chain_entities.append(
                Entity(id=f"chain_{i}", type="Process", attributes={"step": i})
            )
        
        relationships = []
        for i in range(len(chain_entities) - 1):
            relationships.append(
                Relationship(
                    source=chain_entities[i],
                    target=chain_entities[i+1],
                    relationship_type=RelationshipType.PRECEDES,
                    confidence=0.9
                )
            )
        
        patterns = await recognizer.recognize_patterns(chain_entities, relationships)
        
        # Should detect chain pattern
        chain_patterns = [p for p in patterns if p.pattern_type == "chain"]
        assert len(chain_patterns) > 0
        
        chain = chain_patterns[0]
        assert len(chain.entities) >= recognizer.config["patterns"]["chain_detection"]["min_chain_length"]
    
    @pytest.mark.asyncio
    async def test_star_detection(self, recognizer):
        """Test star pattern detection"""
        # Create star pattern
        center = Entity(id="center", type="Manager", attributes={"name": "Central Manager"})
        spokes = []
        
        for i in range(6):
            spokes.append(
                Entity(id=f"spoke_{i}", type="Employee", attributes={"name": f"Employee {i}"})
            )
        
        entities = [center] + spokes
        relationships = []
        
        # All spokes connected only to center
        for spoke in spokes:
            relationships.append(
                Relationship(
                    source=center,
                    target=spoke,
                    relationship_type=RelationshipType.MANAGES,
                    confidence=0.9
                )
            )
        
        patterns = await recognizer.recognize_patterns(entities, relationships)
        
        # Should detect star pattern
        star_patterns = [p for p in patterns if p.pattern_type == "star"]
        assert len(star_patterns) > 0
        
        star = star_patterns[0]
        assert star.get_central_entity().id == "center"
        assert star.metadata["spoke_count"] >= recognizer.config["patterns"]["star_detection"]["min_spokes"]
    
    @pytest.mark.asyncio
    async def test_pattern_scoring(self, recognizer, hub_entities_and_relationships):
        """Test pattern importance scoring"""
        entities, relationships = hub_entities_and_relationships
        
        patterns = await recognizer.recognize_patterns(entities, relationships)
        
        # All patterns should have importance scores
        for pattern in patterns:
            assert "importance_score" in pattern.metadata
            assert 0 <= pattern.metadata["importance_score"] <= 2.0
        
        # Patterns should be sorted by importance
        scores = [p.metadata["importance_score"] for p in patterns]
        assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.asyncio
    async def test_collaboration_analysis(self, recognizer):
        """Test collaboration strength analysis"""
        entities = [
            Entity(id="e1", type="Team"),
            Entity(id="e2", type="Team"),
            Entity(id="e3", type="Team")
        ]
        
        relationships = [
            Relationship(
                source=entities[0], target=entities[1],
                relationship_type=RelationshipType.COLLABORATES_WITH,
                confidence=0.9
            ),
            Relationship(
                source=entities[1], target=entities[2],
                relationship_type=RelationshipType.WORKS_WITH,
                confidence=0.8
            ),
            Relationship(
                source=entities[0], target=entities[2],
                relationship_type=RelationshipType.ASSIGNED_TO,
                confidence=0.7
            )
        ]
        
        strength = recognizer._analyze_collaboration_strength(entities, relationships)
        
        assert strength > 0
        assert strength <= 1.0
    
    @pytest.mark.asyncio
    async def test_centrality_calculation(self, recognizer, hub_entities_and_relationships):
        """Test centrality score calculation"""
        entities, relationships = hub_entities_and_relationships
        
        graph = recognizer._build_graph(entities, relationships)
        
        # Hub should have highest centrality
        hub_centrality = 0
        hub_id = "hub_001"
        
        patterns = await recognizer._detect_hubs(graph, entities)
        
        for pattern in patterns:
            if hub_id in pattern.centrality_scores:
                hub_centrality = pattern.centrality_scores[hub_id]
                break
        
        assert hub_centrality > 0.5  # Hub should have high centrality
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, recognizer, hub_entities_and_relationships):
        """Test pattern caching"""
        entities, relationships = hub_entities_and_relationships
        
        recognizer.config["performance"]["cache_patterns"] = True
        
        # First call
        patterns1 = await recognizer.recognize_patterns(entities, relationships)
        
        # Second call should use cache
        patterns2 = await recognizer.recognize_patterns(entities, relationships)
        
        # Should return same results
        assert len(patterns1) == len(patterns2)
        
        # Clear cache
        recognizer.clear_cache()
        assert len(recognizer._pattern_cache) == 0
    
    @pytest.mark.asyncio
    async def test_parallel_detection(self, recognizer, hub_entities_and_relationships):
        """Test parallel pattern detection"""
        entities, relationships = hub_entities_and_relationships
        
        # Enable parallel detection
        recognizer.config["performance"]["parallel_detection"] = True
        
        patterns = await recognizer.recognize_patterns(entities, relationships)
        
        # Should still find patterns
        assert len(patterns) > 0
        
        # Disable and compare
        recognizer.config["performance"]["parallel_detection"] = False
        recognizer.clear_cache()
        
        patterns_serial = await recognizer.recognize_patterns(entities, relationships)
        
        # Results should be similar
        assert len(patterns) == len(patterns_serial)
    
    @pytest.mark.asyncio
    async def test_empty_inputs(self, recognizer):
        """Test with empty inputs"""
        # Empty entities
        result1 = await recognizer.recognize_patterns([], [])
        assert result1 == []
        
        # Empty relationships
        entities = [Entity(id="e1", type="E")]
        result2 = await recognizer.recognize_patterns(entities, [])
        assert result2 == []