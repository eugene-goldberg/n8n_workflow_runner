"""Tests for SemanticRelationshipMiner"""

import pytest
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity,
    EntityMention,
    Relationship,
    RelationshipType,
    RelationshipDirection
)
from src.semantic_miner import SemanticRelationshipMiner


class TestSemanticMiner:
    """Test SemanticRelationshipMiner functionality"""
    
    @pytest.fixture
    def miner(self):
        """Create SemanticRelationshipMiner instance"""
        return SemanticRelationshipMiner()
    
    @pytest.fixture
    def sample_entities(self):
        """Create sample entities for testing"""
        return [
            Entity(id="person_001", type="Person", attributes={"name": "Alice Johnson"}),
            Entity(id="person_002", type="Person", attributes={"name": "Bob Smith"}),
            Entity(id="team_001", type="Team", attributes={"name": "Engineering"}),
            Entity(id="proj_001", type="Project", attributes={"name": "Migration Project"}),
            Entity(id="cust_001", type="Customer", attributes={"name": "TechCorp"})
        ]
    
    @pytest.mark.asyncio
    async def test_mine_from_text_basic(self, miner, sample_entities):
        """Test basic relationship extraction from text"""
        text = "Alice Johnson works with Bob Smith on the Engineering team."
        
        relationships = await miner.mine_from_text(text, sample_entities)
        
        assert len(relationships) > 0
        
        # Should find work relationship between Alice and Bob
        alice_bob_rels = [
            r for r in relationships
            if {r.source.attributes.get("name"), r.target.attributes.get("name")} == 
               {"Alice Johnson", "Bob Smith"}
        ]
        assert len(alice_bob_rels) > 0
        assert alice_bob_rels[0].relationship_type == RelationshipType.WORKS_WITH
    
    @pytest.mark.asyncio
    async def test_entity_mention_detection(self, miner, sample_entities):
        """Test entity mention detection in text"""
        text = "TechCorp is working with the Engineering team on the Migration Project."
        
        mentions = await miner._find_entity_mentions(text, sample_entities)
        
        # Should find mentions of TechCorp, Engineering, and Migration Project
        mention_texts = [m.surface_form for m in mentions]
        assert "techcorp" in mention_texts  # Lowercased
        assert "engineering" in mention_texts
        assert "migration project" in mention_texts
    
    @pytest.mark.asyncio
    async def test_pattern_based_extraction(self, miner, sample_entities):
        """Test pattern-based relationship extraction"""
        text = "Bob Smith manages the Engineering team."
        
        # Create mentions manually for testing
        mentions = [
            EntityMention(
                entity_id="person_002",
                entity_type="Person",
                surface_form="Bob Smith",
                start_pos=0,
                end_pos=9
            ),
            EntityMention(
                entity_id="team_001",
                entity_type="Team",
                surface_form="Engineering team",
                start_pos=22,
                end_pos=38
            )
        ]
        
        relationships = await miner._extract_pattern_relationships(text, mentions)
        
        assert len(relationships) > 0
        rel = relationships[0]
        assert rel.relationship_type == RelationshipType.MANAGES
        assert rel.direction == RelationshipDirection.UNIDIRECTIONAL
    
    @pytest.mark.asyncio
    async def test_bidirectional_relationships(self, miner, sample_entities):
        """Test bidirectional relationship extraction"""
        text = "Alice Johnson collaborates with Bob Smith on various projects."
        
        relationships = await miner.mine_from_text(text, sample_entities)
        
        collab_rels = [
            r for r in relationships
            if r.relationship_type in [RelationshipType.WORKS_WITH, RelationshipType.COLLABORATES_WITH]
        ]
        
        assert len(collab_rels) > 0
        # Bidirectional relationships should be marked as such
        assert any(r.direction == RelationshipDirection.BIDIRECTIONAL for r in collab_rels)
    
    @pytest.mark.asyncio
    async def test_responsibility_relationships(self, miner, sample_entities):
        """Test responsibility relationship extraction"""
        text = "Alice Johnson is responsible for the Migration Project."
        
        relationships = await miner.mine_from_text(text, sample_entities)
        
        resp_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.RESPONSIBLE_FOR
        ]
        
        assert len(resp_rels) > 0
        rel = resp_rels[0]
        assert rel.source.attributes["name"] == "Alice Johnson"
        assert rel.target.attributes["name"] == "Migration Project"
    
    @pytest.mark.asyncio
    async def test_impact_relationships(self, miner, sample_entities):
        """Test impact relationship extraction"""
        text = "The Engineering team's performance directly impacts TechCorp's success."
        
        relationships = await miner.mine_from_text(text, sample_entities)
        
        impact_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.IMPACTS
        ]
        
        assert len(impact_rels) > 0
    
    @pytest.mark.asyncio
    async def test_entity_name_variations(self, miner):
        """Test handling of entity name variations"""
        entities = [
            Entity(id="comp_001", type="Company", attributes={"name": "Technology Corporation"})
        ]
        
        text = "TechCorp (also known as Technology Corporation) is our main client."
        
        mentions = await miner._find_entity_mentions(text, entities)
        
        # Should find the full company name
        assert any(m.entity_id == "comp_001" for m in mentions)
    
    @pytest.mark.asyncio
    async def test_mention_deduplication(self, miner):
        """Test deduplication of overlapping mentions"""
        mentions = [
            EntityMention("e1", "Type1", "test entity", 0, 11, 0.9),
            EntityMention("e2", "Type2", "test", 0, 4, 0.8),  # Overlaps with first
            EntityMention("e3", "Type3", "entity", 5, 11, 0.7),  # Overlaps with first
            EntityMention("e4", "Type4", "other", 15, 20, 0.9)  # No overlap
        ]
        
        deduped = miner._deduplicate_mentions(mentions)
        
        assert len(deduped) == 2  # Should keep highest confidence non-overlapping
        assert deduped[0].entity_id == "e1"  # Highest confidence for position 0
        assert deduped[1].entity_id == "e4"  # No overlap
    
    @pytest.mark.asyncio
    async def test_relationship_confidence(self, miner, sample_entities):
        """Test relationship confidence scoring"""
        text = "It seems that Alice might be working with Bob on something."
        
        relationships = await miner.mine_from_text(text, sample_entities)
        
        # Uncertain language should result in lower confidence
        if relationships:
            assert all(r.confidence < 0.9 for r in relationships)
    
    @pytest.mark.asyncio
    async def test_document_metadata_inclusion(self, miner, sample_entities):
        """Test inclusion of document metadata in relationships"""
        text = "Alice manages the Engineering team."
        metadata = {
            "source": "org_chart.txt",
            "date": "2024-01-15",
            "confidence": "high"
        }
        
        relationships = await miner.mine_from_text(
            text,
            sample_entities,
            document_metadata=metadata
        )
        
        assert len(relationships) > 0
        for rel in relationships:
            assert "document" in rel.metadata
            assert rel.metadata["document"]["source"] == "org_chart.txt"
    
    @pytest.mark.asyncio
    async def test_extract_from_documents(self, miner, sample_entities):
        """Test extraction from multiple documents"""
        documents = [
            {
                "text": "Alice Johnson leads the Engineering team.",
                "doc_id": "doc1",
                "source": "org_chart"
            },
            {
                "text": "Bob Smith reports to Alice Johnson.",
                "doc_id": "doc2",
                "source": "hr_system"
            }
        ]
        
        relationships = await miner.extract_from_documents(
            documents,
            sample_entities
        )
        
        assert len(relationships) > 0
        
        # Should find relationships from both documents
        sources = set()
        for rel in relationships:
            if "document" in rel.metadata:
                sources.add(rel.metadata["document"]["source"])
        
        assert len(sources) >= 2
    
    @pytest.mark.asyncio
    async def test_relationship_context_extraction(self, miner, sample_entities):
        """Test extraction of context around relationships"""
        text = "In the quarterly review, it was noted that Alice Johnson effectively manages the Engineering team, leading to improved productivity."
        
        relationships = await miner.mine_from_text(text, sample_entities)
        
        if relationships:
            rel = relationships[0]
            
            # Create mentions for context extraction
            mentions = await miner._find_entity_mentions(text, sample_entities)
            
            context = miner.get_relationship_context(text, rel, mentions)
            
            assert len(context) > 0
            assert "manages" in context
            assert "Alice Johnson" in context
            assert "Engineering team" in context
    
    @pytest.mark.asyncio
    async def test_max_text_length_handling(self, miner, sample_entities):
        """Test handling of very long texts"""
        # Create text longer than max length
        long_text = "Alice works with Bob. " * 1000
        
        miner.config["performance"]["max_text_length"] = 100
        
        # Should not crash, should process truncated text
        relationships = await miner.mine_from_text(long_text, sample_entities)
        
        # Should still find some relationships in truncated portion
        assert isinstance(relationships, list)
    
    @pytest.mark.asyncio
    async def test_empty_inputs(self, miner):
        """Test with empty inputs"""
        # Empty text
        result1 = await miner.mine_from_text("", [Entity(id="e1", type="E")])
        assert result1 == []
        
        # Empty entities
        result2 = await miner.mine_from_text("Some text here", [])
        assert result2 == []
        
        # Both empty
        result3 = await miner.mine_from_text("", [])
        assert result3 == []