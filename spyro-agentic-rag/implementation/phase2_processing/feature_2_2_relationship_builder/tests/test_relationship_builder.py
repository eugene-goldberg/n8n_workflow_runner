"""Tests for RelationshipBuilder"""

import pytest
import asyncio
from datetime import datetime
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    RelationshipRule,
    RelationshipDiscoveryContext
)
from src.relationship_builder import RelationshipBuilder


class TestRelationshipBuilder:
    """Test RelationshipBuilder functionality"""
    
    @pytest.fixture
    def builder(self):
        """Create RelationshipBuilder instance"""
        return RelationshipBuilder()
    
    @pytest.fixture
    def sample_entities(self):
        """Create sample entities for testing"""
        return [
            Entity(
                id="cust_001",
                type="Customer",
                attributes={
                    "name": "TechCorp",
                    "arr": 500000,
                    "status": "active"
                }
            ),
            Entity(
                id="sub_001",
                type="Subscription",
                attributes={
                    "customer_id": "cust_001",
                    "product_id": "prod_001",
                    "value": 100000
                }
            ),
            Entity(
                id="prod_001",
                type="Product",
                attributes={
                    "name": "Enterprise Platform",
                    "category": "SaaS"
                }
            ),
            Entity(
                id="team_001",
                type="Team",
                attributes={
                    "name": "Customer Success",
                    "manager_id": "person_001"
                }
            ),
            Entity(
                id="person_001",
                type="Person",
                attributes={
                    "name": "Alice Johnson",
                    "role": "CS Manager"
                }
            ),
            Entity(
                id="risk_001",
                type="Risk",
                attributes={
                    "title": "Churn Risk",
                    "customer_id": "cust_001",
                    "severity": "high"
                }
            )
        ]
    
    @pytest.mark.asyncio
    async def test_build_explicit_relationships(self, builder, sample_entities):
        """Test building explicit ID-based relationships"""
        relationships = await builder.build_relationships(sample_entities)
        
        # Should find subscription->customer relationship
        sub_cust_rels = [
            r for r in relationships
            if r.source.id == "sub_001" and r.target.id == "cust_001"
        ]
        assert len(sub_cust_rels) > 0
        assert sub_cust_rels[0].relationship_type == RelationshipType.BELONGS_TO
        assert sub_cust_rels[0].confidence == 1.0
        
        # Should find team->person relationship
        team_person_rels = [
            r for r in relationships
            if r.source.id == "team_001" and r.target.id == "person_001"
        ]
        assert len(team_person_rels) > 0
        assert team_person_rels[0].relationship_type == RelationshipType.MANAGED_BY
    
    @pytest.mark.asyncio
    async def test_custom_rules(self, builder):
        """Test with custom relationship rules"""
        # Create custom rule
        custom_rule = RelationshipRule(
            source_type="Project",
            field="owner_id",
            target_type="Person",
            relationship=RelationshipType.OWNED_BY,
            bidirectional=False
        )
        
        builder.rules.append(custom_rule)
        
        # Create entities
        entities = [
            Entity(
                id="proj_001",
                type="Project",
                attributes={"name": "Migration", "owner_id": "person_002"}
            ),
            Entity(
                id="person_002",
                type="Person",
                attributes={"name": "Bob Smith"}
            )
        ]
        
        relationships = await builder.build_relationships(entities)
        
        # Should find project->person relationship
        proj_person_rels = [
            r for r in relationships
            if r.source.id == "proj_001" and r.target.id == "person_002"
        ]
        assert len(proj_person_rels) > 0
        assert proj_person_rels[0].relationship_type == RelationshipType.OWNED_BY
    
    @pytest.mark.asyncio
    async def test_bidirectional_relationships(self, builder):
        """Test bidirectional relationship creation"""
        # Add bidirectional rule
        builder.rules.append(
            RelationshipRule(
                source_type="Team",
                field="partner_team_id",
                target_type="Team",
                relationship=RelationshipType.COLLABORATES_WITH,
                bidirectional=True
            )
        )
        
        entities = [
            Entity(
                id="team_a",
                type="Team",
                attributes={"name": "Team A", "partner_team_id": "team_b"}
            ),
            Entity(
                id="team_b",
                type="Team",
                attributes={"name": "Team B"}
            )
        ]
        
        relationships = await builder.build_relationships(entities)
        
        # Should create relationships in both directions
        assert len(relationships) >= 2
        
        # Check forward relationship
        forward_rels = [
            r for r in relationships
            if r.source.id == "team_a" and r.target.id == "team_b"
        ]
        assert len(forward_rels) > 0
        
        # Check reverse relationship
        reverse_rels = [
            r for r in relationships
            if r.source.id == "team_b" and r.target.id == "team_a"
        ]
        assert len(reverse_rels) > 0
    
    @pytest.mark.asyncio
    async def test_missing_target_handling(self, builder, sample_entities):
        """Test handling of missing target entities"""
        # Add entity with reference to non-existent target
        entities = sample_entities + [
            Entity(
                id="sub_002",
                type="Subscription",
                attributes={
                    "customer_id": "cust_999",  # Non-existent
                    "product_id": "prod_001"
                }
            )
        ]
        
        # Should not crash
        relationships = await builder.build_relationships(entities)
        
        # Should not create relationship for missing target
        bad_rels = [
            r for r in relationships
            if r.source.id == "sub_002" and r.target.id == "cust_999"
        ]
        assert len(bad_rels) == 0
    
    @pytest.mark.asyncio
    async def test_temporal_relationships(self, builder):
        """Test temporal relationship building"""
        entities = [
            Entity(
                id="event_001",
                type="Event",
                attributes={
                    "name": "Project Start",
                    "created_date": "2024-01-01T00:00:00"
                }
            ),
            Entity(
                id="event_002",
                type="Event",
                attributes={
                    "name": "Milestone 1",
                    "created_date": "2024-02-01T00:00:00"
                }
            ),
            Entity(
                id="event_003",
                type="Event",
                attributes={
                    "name": "Project End",
                    "created_date": "2024-03-01T00:00:00"
                }
            )
        ]
        
        relationships = await builder.build_relationships(entities)
        
        # Should find temporal precedence relationships
        temporal_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.PRECEDES
        ]
        assert len(temporal_rels) > 0
        
        # Check correct order
        for rel in temporal_rels:
            source_date = rel.source.attributes.get("created_date")
            target_date = rel.target.attributes.get("created_date")
            assert source_date < target_date
    
    @pytest.mark.asyncio
    async def test_semantic_relationships(self, builder):
        """Test semantic relationship building"""
        entities = [
            Entity(
                id="person_a",
                type="Person",
                attributes={"name": "Alice", "team": "Engineering"}
            ),
            Entity(
                id="person_b",
                type="Person",
                attributes={"name": "Bob", "team": "Engineering"}
            ),
            Entity(
                id="person_c",
                type="Person",
                attributes={"name": "Charlie", "team": "Sales"}
            )
        ]
        
        relationships = await builder.build_relationships(entities)
        
        # Should find team membership relationships
        team_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.WORKS_WITH
        ]
        
        # Alice and Bob should be connected (same team)
        alice_bob_rels = [
            r for r in team_rels
            if {r.source.id, r.target.id} == {"person_a", "person_b"}
        ]
        assert len(alice_bob_rels) > 0
    
    @pytest.mark.asyncio
    async def test_relationship_deduplication(self, builder):
        """Test relationship deduplication"""
        # Create entities that would generate duplicate relationships
        entities = [
            Entity(
                id="cust_001",
                type="Customer",
                attributes={"name": "TestCorp"}
            ),
            Entity(
                id="sub_001",
                type="Subscription",
                attributes={"customer_id": "cust_001"}
            ),
            Entity(
                id="sub_002",
                type="Subscription",
                attributes={"customer_id": "cust_001"}
            )
        ]
        
        # Build relationships twice
        relationships1 = await builder.build_relationships(entities)
        relationships2 = await builder.build_relationships(entities)
        
        # Combine and deduplicate
        all_relationships = relationships1 + relationships2
        deduped = builder._deduplicate_relationships(all_relationships)
        
        # Should have fewer relationships after deduplication
        assert len(deduped) < len(all_relationships)
    
    @pytest.mark.asyncio
    async def test_context_filtering(self, builder, sample_entities):
        """Test relationship filtering with context"""
        context = RelationshipDiscoveryContext(
            min_confidence=0.8,
            exclude_types={RelationshipType.PRECEDES}
        )
        
        relationships = await builder.build_relationships(
            sample_entities,
            context
        )
        
        # Should not include PRECEDES relationships
        precedes_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.PRECEDES
        ]
        assert len(precedes_rels) == 0
        
        # Should only include high confidence relationships
        for rel in relationships:
            assert rel.confidence >= 0.8
    
    @pytest.mark.asyncio
    async def test_entity_index_building(self, builder, sample_entities):
        """Test entity index construction"""
        index = builder._build_entity_index(sample_entities)
        
        # Check index structure
        assert "Customer" in index
        assert "cust_001" in index["Customer"]
        assert index["Customer"]["cust_001"].id == "cust_001"
        
        # Check all entities are indexed
        for entity in sample_entities:
            assert entity.type in index
            assert entity.id in index[entity.type]
    
    @pytest.mark.asyncio
    async def test_get_relationships_for_entity(self, builder, sample_entities):
        """Test getting relationships for specific entity"""
        # Build relationships
        await builder.build_relationships(sample_entities)
        
        # Get relationships for customer
        cust_relationships = builder.get_relationships_for_entity("cust_001")
        
        assert len(cust_relationships) > 0
        
        # Check filtering by relationship type
        belongs_to_rels = builder.get_relationships_for_entity(
            "cust_001",
            rel_type=RelationshipType.BELONGS_TO
        )
        
        for rel in belongs_to_rels:
            assert rel.relationship_type == RelationshipType.BELONGS_TO
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, builder, sample_entities):
        """Test relationship caching"""
        # Enable caching
        builder.config["performance"]["cache_relationships"] = True
        
        # Build relationships
        relationships = await builder.build_relationships(sample_entities)
        
        # Check cache is populated
        assert len(builder._relationship_cache) > 0
        
        # Clear cache
        builder.clear_cache()
        assert len(builder._relationship_cache) == 0
    
    @pytest.mark.asyncio
    async def test_empty_entity_list(self, builder):
        """Test with empty entity list"""
        relationships = await builder.build_relationships([])
        assert relationships == []
    
    @pytest.mark.asyncio
    async def test_single_entity(self, builder):
        """Test with single entity"""
        entities = [
            Entity(
                id="single_001",
                type="Customer",
                attributes={"name": "SingleCorp"}
            )
        ]
        
        relationships = await builder.build_relationships(entities)
        
        # Should not create any relationships
        assert len(relationships) == 0