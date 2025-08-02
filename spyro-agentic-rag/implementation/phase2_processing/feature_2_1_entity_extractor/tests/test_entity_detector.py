"""Tests for entity type detector"""

import pytest
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.entity_detector import EntityTypeDetector
from src.models import EntityType, EntityPattern, DetectedEntity


class TestEntityTypeDetector:
    """Test EntityTypeDetector functionality"""
    
    @pytest.fixture
    def detector(self):
        """Create detector instance"""
        return EntityTypeDetector()
    
    @pytest.mark.asyncio
    async def test_detect_customer_patterns(self, detector):
        """Test detecting customer entities"""
        text = "Our customer TechCorp has been with us for 5 years. BigData Inc is also a valued client."
        
        entities = await detector.detect_entities(text)
        
        # Should detect both customers
        customer_entities = [e for e in entities if e.type == EntityType.CUSTOMER]
        assert len(customer_entities) >= 2
        
        # Check detected names
        detected_names = {e.text for e in customer_entities}
        assert any("TechCorp" in name for name in detected_names)
        assert any("BigData Inc" in name for name in detected_names)
    
    @pytest.mark.asyncio
    async def test_detect_team_patterns(self, detector):
        """Test detecting team entities"""
        text = "The engineering team is working with the sales department on this project."
        
        entities = await detector.detect_entities(text)
        
        team_entities = [e for e in entities if e.type == EntityType.TEAM]
        assert len(team_entities) >= 2
        
        detected_teams = {e.text.lower() for e in team_entities}
        assert any("engineering" in team for team in detected_teams)
        assert any("sales" in team for team in detected_teams)
    
    @pytest.mark.asyncio
    async def test_detect_product_patterns(self, detector):
        """Test detecting product entities"""
        text = "We're launching SpyroCloud next month. The SpyroPlatform will follow in Q2."
        
        entities = await detector.detect_entities(text)
        
        product_entities = [e for e in entities if e.type == EntityType.PRODUCT]
        assert len(product_entities) >= 2
        
        product_names = {e.text for e in product_entities}
        assert "SpyroCloud" in product_names
        assert "SpyroPlatform" in product_names
    
    @pytest.mark.asyncio
    async def test_detect_risk_patterns(self, detector):
        """Test detecting risk entities"""
        text = "We've identified a high churn risk with this account. The security risk has been mitigated."
        
        entities = await detector.detect_entities(text)
        
        risk_entities = [e for e in entities if e.type == EntityType.RISK]
        assert len(risk_entities) >= 2
        
        risk_texts = [e.text.lower() for e in risk_entities]
        assert any("churn risk" in text for text in risk_texts)
        assert any("security risk" in text for text in risk_texts)
    
    @pytest.mark.asyncio
    async def test_detect_objective_patterns(self, detector):
        """Test detecting objective entities"""
        text = "Our Q4 revenue target is $10M. The goal to reduce churn by 20% is on track."
        
        entities = await detector.detect_entities(text)
        
        objective_entities = [e for e in entities if e.type == EntityType.OBJECTIVE]
        assert len(objective_entities) >= 1
        
        # Should detect Q4 revenue objective
        assert any("Q4 revenue" in e.text for e in objective_entities)
    
    @pytest.mark.asyncio
    async def test_detect_subscription_patterns(self, detector):
        """Test detecting subscription entities"""
        text = "Subscription SUB-12345 will renew next month. Contract ID: CONT-67890 expires in Q3."
        
        entities = await detector.detect_entities(text)
        
        sub_entities = [e for e in entities if e.type == EntityType.SUBSCRIPTION]
        assert len(sub_entities) >= 2
        
        sub_ids = {e.text for e in sub_entities}
        assert any("SUB-12345" in id for id in sub_ids)
        assert any("CONT-67890" in id for id in sub_ids)
    
    @pytest.mark.asyncio
    async def test_entity_position_tracking(self, detector):
        """Test that entity positions are correctly tracked"""
        text = "TechCorp is our largest customer."
        
        entities = await detector.detect_entities(text)
        
        # Find TechCorp entity
        techcorp = next(
            (e for e in entities if "TechCorp" in e.text),
            None
        )
        
        assert techcorp is not None
        assert techcorp.start_pos == text.index("TechCorp")
        assert techcorp.end_pos == techcorp.start_pos + len("TechCorp")
        
        # Verify the text slice matches
        assert text[techcorp.start_pos:techcorp.end_pos] == "TechCorp"
    
    @pytest.mark.asyncio
    async def test_context_required_patterns(self, detector):
        """Test patterns that require context"""
        # Without context - should not detect
        text1 = "The platform is stable."
        entities1 = await detector.detect_entities(text1)
        team_entities1 = [e for e in entities1 if e.type == EntityType.TEAM]
        assert len(team_entities1) == 0
        
        # With context - should detect
        text2 = "The platform team is working on stability."
        entities2 = await detector.detect_entities(text2)
        team_entities2 = [e for e in entities2 if e.type == EntityType.TEAM]
        assert len(team_entities2) >= 1
    
    @pytest.mark.asyncio
    async def test_overlapping_detection_handling(self, detector):
        """Test handling of overlapping entity detections"""
        text = "TechCorp Inc is our customer."
        
        entities = await detector.detect_entities(text)
        
        # Should not have overlapping detections
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Check no overlap
                assert not (
                    entity1.start_pos < entity2.end_pos and
                    entity2.start_pos < entity1.end_pos
                )
    
    @pytest.mark.asyncio
    async def test_specific_entity_types_filter(self, detector):
        """Test filtering by specific entity types"""
        text = "Customer TechCorp has a subscription with the platform team."
        
        # Detect only customers
        customer_only = await detector.detect_entities(
            text,
            entity_types=[EntityType.CUSTOMER]
        )
        
        assert all(e.type == EntityType.CUSTOMER for e in customer_only)
        assert len(customer_only) >= 1
        
        # Detect only teams
        team_only = await detector.detect_entities(
            text,
            entity_types=[EntityType.TEAM]
        )
        
        assert all(e.type == EntityType.TEAM for e in team_only)
        assert len(team_only) >= 1
    
    @pytest.mark.asyncio
    async def test_word_boundary_detection(self, detector):
        """Test that word boundaries are respected"""
        text = "Customers are important. The customer TechCorp is our biggest."
        
        entities = await detector.detect_entities(text)
        
        # Should not detect "Customer" in "Customers"
        customer_entities = [
            e for e in entities
            if e.type == EntityType.CUSTOMER and e.text == "Customers"
        ]
        assert len(customer_entities) == 0
    
    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self, detector):
        """Test case-insensitive pattern matching"""
        text = "The ENGINEERING team and the Engineering Team are the same."
        
        entities = await detector.detect_entities(text)
        
        team_entities = [e for e in entities if e.type == EntityType.TEAM]
        assert len(team_entities) >= 2
    
    @pytest.mark.asyncio
    async def test_custom_pattern_addition(self, detector):
        """Test adding custom patterns"""
        # Add custom pattern
        custom_pattern = EntityPattern(
            entity_type=EntityType.CUSTOMER,
            pattern=r'ACME-\d+',
            pattern_type="regex",
            confidence=0.95
        )
        
        detector.add_pattern(custom_pattern)
        
        text = "Customer ACME-12345 has placed a new order."
        entities = await detector.detect_entities(text)
        
        # Should detect custom pattern
        acme_entities = [
            e for e in entities
            if "ACME-12345" in e.text
        ]
        assert len(acme_entities) == 1
        assert acme_entities[0].confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_pattern_removal(self, detector):
        """Test removing patterns"""
        # Get initial count
        text = "The engineering team is great."
        initial_entities = await detector.detect_entities(text)
        initial_count = len(initial_entities)
        
        # Remove a pattern
        detector.remove_pattern(r'(?:the\s+)?(\w+)\s+(?:team|department|group|division)\b')
        
        # Should detect fewer entities
        after_entities = await detector.detect_entities(text)
        assert len(after_entities) < initial_count
    
    @pytest.mark.asyncio
    async def test_cache_functionality(self, detector):
        """Test detection caching"""
        text = "TechCorp is our customer."
        
        # First call - not cached
        entities1 = await detector.detect_entities(text)
        
        # Second call - should be cached
        entities2 = await detector.detect_entities(text)
        
        # Results should be the same
        assert len(entities1) == len(entities2)
        
        # Clear cache
        detector.clear_cache()
        
        # Cache should be empty
        assert len(detector._detection_cache) == 0
    
    @pytest.mark.asyncio
    async def test_empty_text_handling(self, detector):
        """Test handling of empty or None text"""
        # Empty string
        entities1 = await detector.detect_entities("")
        assert len(entities1) == 0
        
        # Whitespace only
        entities2 = await detector.detect_entities("   \n\t  ")
        assert len(entities2) == 0
    
    @pytest.mark.asyncio
    async def test_confidence_scores(self, detector):
        """Test that confidence scores are properly set"""
        text = "Customer BigCorp Inc has high value."
        
        entities = await detector.detect_entities(text)
        
        # All entities should have confidence scores
        assert all(0 <= e.confidence <= 1 for e in entities)
        
        # Company patterns should have high confidence
        company_entities = [
            e for e in entities
            if "BigCorp Inc" in e.text
        ]
        assert len(company_entities) > 0
        assert all(e.confidence >= 0.8 for e in company_entities)