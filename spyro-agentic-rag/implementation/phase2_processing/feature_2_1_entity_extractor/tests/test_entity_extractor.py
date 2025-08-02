"""Tests for entity extractor"""

import pytest
import asyncio
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.entity_extractor import EntityExtractor
from src.models import MappingRule, EntityType, Entity, ExtractionContext
from src.validators import EntityValidator


class TestEntityExtractor:
    """Test EntityExtractor functionality"""
    
    @pytest.fixture
    def extractor(self):
        """Create entity extractor instance"""
        return EntityExtractor()
    
    @pytest.fixture
    def mapping_rules(self):
        """Create sample mapping rules"""
        return {
            "id": MappingRule(
                entity_type="Customer",
                target_field="id",
                required=True
            ),
            "company_name": MappingRule(
                entity_type="Customer",
                target_field="name",
                transformation="strip",
                required=True
            ),
            "annual_revenue": MappingRule(
                entity_type="Customer",
                target_field="arr",
                transformation="float",
                required=False
            ),
            "employee_count": MappingRule(
                entity_type="Customer",
                target_field="employees",
                transformation="int",
                required=False,
                default_value=0
            )
        }
    
    @pytest.mark.asyncio
    async def test_extract_single_entity(self, extractor, mapping_rules):
        """Test extracting a single entity"""
        raw_data = {
            "id": "cust_123",
            "company_name": "  TechCorp  ",
            "annual_revenue": "500000",
            "employee_count": "100"
        }
        
        entities = await extractor.extract_entities(raw_data, mapping_rules)
        
        assert len(entities) == 1
        entity = entities[0]
        
        assert entity.type == EntityType.CUSTOMER
        assert entity.attributes["id"] == "cust_123"
        assert entity.attributes["name"] == "TechCorp"  # stripped
        assert entity.attributes["arr"] == 500000.0  # converted to float
        assert entity.attributes["employees"] == 100  # converted to int
    
    @pytest.mark.asyncio
    async def test_extract_with_missing_optional_fields(self, extractor, mapping_rules):
        """Test extraction with missing optional fields"""
        raw_data = {
            "id": "cust_124",
            "company_name": "SmallCorp"
            # Missing annual_revenue and employee_count
        }
        
        entities = await extractor.extract_entities(raw_data, mapping_rules)
        
        assert len(entities) == 1
        entity = entities[0]
        
        assert entity.attributes["id"] == "cust_124"
        assert entity.attributes["name"] == "SmallCorp"
        assert entity.attributes["employees"] == 0  # default value
        assert "arr" not in entity.attributes  # no default, not included
    
    @pytest.mark.asyncio
    async def test_extract_multiple_entity_types(self, extractor):
        """Test extracting multiple entity types from one record"""
        raw_data = {
            "customer_id": "cust_125",
            "customer_name": "BigCorp",
            "subscription_id": "sub_001",
            "product_name": "SpyroCloud",
            "subscription_value": 100000
        }
        
        mapping_rules = {
            "customer_id": MappingRule(
                entity_type="Customer",
                target_field="id"
            ),
            "customer_name": MappingRule(
                entity_type="Customer",
                target_field="name"
            ),
            "subscription_id": MappingRule(
                entity_type="Subscription",
                target_field="id"
            ),
            "product_name": MappingRule(
                entity_type="Product",
                target_field="name"
            ),
            "subscription_value": MappingRule(
                entity_type="Subscription",
                target_field="value",
                transformation="float"
            )
        }
        
        entities = await extractor.extract_entities(raw_data, mapping_rules)
        
        # Should have 3 entities: Customer, Product, Subscription
        assert len(entities) == 3
        
        entity_types = {e.type for e in entities}
        assert EntityType.CUSTOMER in entity_types
        assert EntityType.PRODUCT in entity_types
        assert EntityType.SUBSCRIPTION in entity_types
    
    @pytest.mark.asyncio
    async def test_extract_with_context(self, extractor, mapping_rules):
        """Test extraction with context"""
        raw_data = {
            "id": "cust_126",
            "company_name": "ContextCorp"
        }
        
        context = ExtractionContext(
            source_system="salesforce",
            metadata={"import_batch": "batch_001"}
        )
        
        entities = await extractor.extract_entities(
            raw_data, mapping_rules, context
        )
        
        assert len(entities) == 1
        entity = entities[0]
        
        assert entity.source_system == "salesforce"
        assert entity.source_id == "salesforce_cust_126"
        assert "import_batch" not in entity.metadata  # Context metadata not copied
    
    @pytest.mark.asyncio
    async def test_extract_bulk(self, extractor, mapping_rules):
        """Test bulk extraction"""
        records = [
            {
                "id": f"cust_{i}",
                "company_name": f"Company {i}",
                "annual_revenue": str(i * 10000)
            }
            for i in range(10)
        ]
        
        entities = await extractor.extract_entities_bulk(
            records, mapping_rules, batch_size=3
        )
        
        # Should have 10 entities
        assert len(entities) == 10
        
        # Check a few entities
        assert entities[0].attributes["name"] == "Company 0"
        assert entities[5].attributes["arr"] == 50000.0
        assert entities[9].attributes["id"] == "cust_9"
    
    @pytest.mark.asyncio
    async def test_transformation_functions(self, extractor):
        """Test various transformation functions"""
        test_cases = [
            ("uppercase", "hello", "HELLO"),
            ("lowercase", "WORLD", "world"),
            ("strip", "  spaces  ", "spaces"),
            ("int", "42", 42),
            ("float", "3.14", 3.14),
            ("bool", "true", True),
            ("multiply:2", "10", 20.0),
            ("divide:5", "100", 20.0)
        ]
        
        for transformation, input_val, expected in test_cases:
            result = extractor._apply_transformation(input_val, transformation)
            assert result == expected
    
    @pytest.mark.asyncio
    async def test_validation_integration(self, extractor):
        """Test integration with validation"""
        # Create mapping for customer with validation
        mapping_rules = {
            "id": MappingRule(
                entity_type="Customer",
                target_field="id"
            ),
            "name": MappingRule(
                entity_type="Customer",
                target_field="name"
            ),
            "email": MappingRule(
                entity_type="Customer",
                target_field="email"
            )
        }
        
        # Invalid email
        raw_data = {
            "id": "cust_127",
            "name": "TestCorp",
            "email": "invalid-email"
        }
        
        context = ExtractionContext(
            source_system="test",
            validation_config={
                "auto_fix_errors": False
            }
        )
        
        entities = await extractor.extract_entities(
            raw_data, mapping_rules, context
        )
        
        # Entity should be rejected due to validation
        assert len(entities) == 0
    
    @pytest.mark.asyncio
    async def test_stats_tracking(self, extractor, mapping_rules):
        """Test extraction statistics tracking"""
        # Reset stats
        extractor.reset_stats()
        
        # Extract some entities
        raw_data1 = {
            "id": "cust_128",
            "company_name": "StatsCorp"
        }
        
        await extractor.extract_entities(raw_data1, mapping_rules)
        
        # Check stats
        stats = extractor.get_extraction_stats()
        assert stats["total_extracted"] == 1
        assert stats["validation_errors"] == 0
        assert stats["auto_fixed"] == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, extractor):
        """Test error handling in bulk extraction"""
        # Create records with some that will cause errors
        records = [
            {"id": "1", "company_name": "Good1"},
            None,  # This will cause an error
            {"id": "3", "company_name": "Good2"},
        ]
        
        mapping_rules = {
            "id": MappingRule(entity_type="Customer", target_field="id"),
            "company_name": MappingRule(entity_type="Customer", target_field="name")
        }
        
        # Should handle errors gracefully
        entities = await extractor.extract_entities_bulk(
            records, mapping_rules, batch_size=10
        )
        
        # Should only get 2 valid entities
        assert len(entities) == 2
        assert entities[0].attributes["name"] == "Good1"
        assert entities[1].attributes["name"] == "Good2"