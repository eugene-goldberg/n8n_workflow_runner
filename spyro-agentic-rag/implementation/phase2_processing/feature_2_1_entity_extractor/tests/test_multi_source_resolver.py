"""Tests for multi-source entity resolver"""

import pytest
import asyncio

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.multi_source_resolver import MultiSourceEntityResolver
from src.models import Entity, EntityType


class TestMultiSourceEntityResolver:
    """Test MultiSourceEntityResolver functionality"""
    
    @pytest.fixture
    def resolver(self):
        """Create resolver instance"""
        return MultiSourceEntityResolver(
            similarity_threshold=0.85,
            use_llm_validation=False,
            merge_strategy="most_complete"
        )
    
    @pytest.mark.asyncio
    async def test_resolve_identical_entities(self, resolver):
        """Test resolving identical entities from different sources"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="sf_123",
                source_system="salesforce",
                attributes={"name": "TechCorp", "email": "info@techcorp.com"}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="gs_456",
                source_system="gainsight",
                attributes={"name": "TechCorp", "email": "info@techcorp.com"}
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should merge into one entity
        assert len(resolved) == 1
        
        merged = resolved[0]
        assert merged.source_ids["salesforce"] == "sf_123"
        assert merged.source_ids["gainsight"] == "gs_456"
        assert merged.attributes["name"] == "TechCorp"
    
    @pytest.mark.asyncio
    async def test_resolve_similar_names(self, resolver):
        """Test resolving entities with similar names"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="sf_124",
                source_system="salesforce",
                attributes={"name": "Tech Corp", "arr": 500000}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="hs_789",
                source_system="hubspot",
                attributes={"name": "TechCorp", "employees": 100}
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should merge due to high name similarity
        assert len(resolved) == 1
        
        merged = resolved[0]
        # Should have attributes from both
        assert merged.attributes["arr"] == 500000
        assert merged.attributes["employees"] == 100
    
    @pytest.mark.asyncio
    async def test_no_merge_different_types(self, resolver):
        """Test that different entity types are not merged"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                attributes={"name": "TechCorp"}
            ),
            Entity(
                type=EntityType.PRODUCT,
                source_id="2",
                attributes={"name": "TechCorp"}
            )
        ]
        
        resolved = await resolver.resolve_entities(entities, group_by_type=True)
        
        # Should not merge different types
        assert len(resolved) == 2
        assert {e.type for e in resolved} == {EntityType.CUSTOMER, EntityType.PRODUCT}
    
    @pytest.mark.asyncio
    async def test_cross_reference_ids(self, resolver):
        """Test merging based on cross-referenced IDs"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="sf_125",
                source_system="salesforce",
                attributes={
                    "id": "sf_125",
                    "name": "CrossRef Corp",
                    "gainsight_id": "gs_999"
                }
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="gs_999",
                source_system="gainsight",
                attributes={
                    "id": "gs_999",
                    "name": "CrossRef Corporation",
                    "salesforce_id": "sf_125"
                }
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should merge based on cross-referenced IDs
        assert len(resolved) == 1
        assert resolved[0].source_ids["salesforce"] == "sf_125"
        assert resolved[0].source_ids["gainsight"] == "gs_999"
    
    @pytest.mark.asyncio
    async def test_email_matching(self, resolver):
        """Test merging based on email match"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                source_system="system1",
                attributes={
                    "name": "Different Name Inc",
                    "email": "contact@company.com"
                }
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="2",
                source_system="system2",
                attributes={
                    "name": "Completely Different LLC",
                    "email": "contact@company.com"
                }
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should merge based on email match despite different names
        assert len(resolved) == 1
    
    @pytest.mark.asyncio
    async def test_domain_matching(self, resolver):
        """Test merging based on domain"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                attributes={
                    "name": "Tech Company",
                    "website": "https://www.techcompany.com"
                }
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="2",
                attributes={
                    "name": "Tech Co",
                    "email": "info@techcompany.com"
                }
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should merge based on domain match
        assert len(resolved) == 1
    
    @pytest.mark.asyncio
    async def test_merge_strategies(self, resolver):
        """Test different merge strategies"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                source_system="salesforce",
                attributes={
                    "name": "OldName",
                    "arr": 100000,
                    "status": "active"
                },
                confidence=0.9
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="2",
                source_system="hubspot",
                attributes={
                    "name": "OldName",
                    "arr": 150000
                },
                confidence=0.7
            )
        ]
        
        # Test most_complete strategy
        resolver.merge_strategy = "most_complete"
        resolved = await resolver.resolve_entities(entities)
        assert len(resolved) == 1
        assert resolved[0].attributes["status"] == "active"  # Has more fields
        
        # Test most_recent strategy
        resolver.merge_strategy = "most_recent"
        # Make second entity more recent
        import time
        time.sleep(0.01)
        entities[1].extracted_at = entities[1].extracted_at.__class__.now()
        
        resolved = await resolver.resolve_entities(entities)
        assert len(resolved) == 1
        # Should prefer newer ARR value
        assert resolved[0].attributes["arr"] == 150000
        
        # Test weighted strategy
        resolver.merge_strategy = "weighted"
        resolved = await resolver.resolve_entities(entities)
        assert len(resolved) == 1
        # Salesforce has higher weight, should prefer its values
        assert resolved[0].attributes["name"] == "OldName"
    
    @pytest.mark.asyncio
    async def test_no_duplicates(self, resolver):
        """Test when there are no duplicates"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                attributes={"name": "Company A", "domain": "companya.com"}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="2",
                attributes={"name": "Company B", "domain": "companyb.com"}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="3",
                attributes={"name": "Company C", "domain": "companyc.com"}
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should not merge any
        assert len(resolved) == 3
        assert {e.attributes["name"] for e in resolved} == {
            "Company A", "Company B", "Company C"
        }
    
    @pytest.mark.asyncio
    async def test_multiple_duplicates(self, resolver):
        """Test resolving multiple sets of duplicates"""
        entities = [
            # First duplicate set
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                attributes={"name": "TechCorp", "email": "tech@corp.com"}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="2",
                attributes={"name": "Tech Corp", "email": "tech@corp.com"}
            ),
            # Second duplicate set
            Entity(
                type=EntityType.CUSTOMER,
                source_id="3",
                attributes={"name": "DataCo", "domain": "dataco.com"}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="4",
                attributes={"name": "Data Co", "website": "https://dataco.com"}
            ),
            # Non-duplicate
            Entity(
                type=EntityType.CUSTOMER,
                source_id="5",
                attributes={"name": "UniqueCompany", "email": "unique@company.com"}
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should have 3 entities: 2 merged sets + 1 unique
        assert len(resolved) == 3
        
        # Check that appropriate entities were merged
        names = {e.attributes["name"] for e in resolved}
        assert "UniqueCompany" in names
    
    @pytest.mark.asyncio
    async def test_confidence_threshold(self, resolver):
        """Test similarity threshold enforcement"""
        # Set high threshold
        resolver.similarity_threshold = 0.95
        
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                attributes={"name": "TechCorp International"}
            ),
            Entity(
                type=EntityType.CUSTOMER,
                source_id="2",
                attributes={"name": "TechCorp Inc"}  # Similar but not 95% match
            )
        ]
        
        resolved = await resolver.resolve_entities(entities)
        
        # Should not merge due to high threshold
        assert len(resolved) == 2
    
    @pytest.mark.asyncio
    async def test_cache_clearing(self, resolver):
        """Test cache clearing"""
        # Populate cache by resolving
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                source_id="1",
                attributes={"name": "CacheTest"}
            )
        ]
        
        await resolver.resolve_entities(entities)
        
        # Clear cache
        resolver.clear_cache()
        
        # Cache should be empty
        assert len(resolver._resolution_cache) == 0