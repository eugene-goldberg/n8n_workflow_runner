"""Tests for entity models"""

import pytest
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.entity_models import (
    FieldType, EntityField, SPYRO_ENTITIES,
    get_entity_fields, get_required_fields, validate_entity_data
)


class TestEntityField:
    """Test cases for EntityField"""
    
    def test_basic_field_creation(self):
        """Test creating entity fields"""
        field = EntityField(
            name="test_field",
            field_type=FieldType.STRING,
            required=True,
            description="Test field"
        )
        
        assert field.name == "test_field"
        assert field.field_type == FieldType.STRING
        assert field.required == True
        assert field.description == "Test field"
    
    def test_field_validation_string(self):
        """Test string field validation"""
        field = EntityField("name", FieldType.STRING)
        
        assert field.validate_value("test") == True
        assert field.validate_value("") == True  # Empty string is valid
        assert field.validate_value(123) == False
        assert field.validate_value(None) == False  # Required by default
        
        # Optional field
        optional_field = EntityField("name", FieldType.STRING, required=False)
        assert optional_field.validate_value(None) == True
    
    def test_field_validation_integer(self):
        """Test integer field validation"""
        field = EntityField("count", FieldType.INTEGER)
        
        assert field.validate_value(123) == True
        assert field.validate_value(0) == True
        assert field.validate_value(-5) == True
        assert field.validate_value("123") == False
        assert field.validate_value(123.45) == False
    
    def test_field_validation_float(self):
        """Test float field validation"""
        field = EntityField("rate", FieldType.FLOAT)
        
        assert field.validate_value(123.45) == True
        assert field.validate_value(123) == True  # int is acceptable for float
        assert field.validate_value(0.0) == True
        assert field.validate_value("123.45") == False
    
    def test_field_validation_boolean(self):
        """Test boolean field validation"""
        field = EntityField("active", FieldType.BOOLEAN)
        
        assert field.validate_value(True) == True
        assert field.validate_value(False) == True
        assert field.validate_value(1) == False
        assert field.validate_value("true") == False
    
    def test_field_validation_date(self):
        """Test date field validation"""
        field = EntityField("created", FieldType.DATE)
        
        assert field.validate_value("2024-01-15") == True
        assert field.validate_value(datetime.now()) == True
        assert field.validate_value(123) == False
    
    def test_field_validation_array(self):
        """Test array field validation"""
        field = EntityField("tags", FieldType.ARRAY)
        
        assert field.validate_value([]) == True
        assert field.validate_value(["a", "b", "c"]) == True
        assert field.validate_value([1, 2, 3]) == True
        assert field.validate_value("not array") == False
        assert field.validate_value({}) == False
    
    def test_field_validation_object(self):
        """Test object field validation"""
        field = EntityField("metadata", FieldType.OBJECT)
        
        assert field.validate_value({}) == True
        assert field.validate_value({"key": "value"}) == True
        assert field.validate_value([]) == False
        assert field.validate_value("not object") == False
    
    def test_field_validation_enum(self):
        """Test enum field validation"""
        field = EntityField(
            "status",
            FieldType.ENUM,
            enum_values=["active", "inactive", "pending"]
        )
        
        assert field.validate_value("active") == True
        assert field.validate_value("inactive") == True
        assert field.validate_value("unknown") == False
        assert field.validate_value(None) == False


class TestEntityModels:
    """Test cases for entity model definitions"""
    
    def test_spyro_entities_structure(self):
        """Test SPYRO_ENTITIES structure"""
        # Check all expected entities exist
        expected_entities = [
            "Customer", "Product", "Subscription", 
            "Team", "Project"
        ]
        
        for entity in expected_entities:
            assert entity in SPYRO_ENTITIES
            assert isinstance(SPYRO_ENTITIES[entity], dict)
            assert len(SPYRO_ENTITIES[entity]) > 0
    
    def test_customer_entity_fields(self):
        """Test Customer entity fields"""
        customer_fields = SPYRO_ENTITIES["Customer"]
        
        # Check required fields
        assert "id" in customer_fields
        assert customer_fields["id"].required == True
        assert customer_fields["id"].field_type == FieldType.STRING
        
        assert "name" in customer_fields
        assert customer_fields["name"].required == True
        
        assert "size" in customer_fields
        assert customer_fields["size"].field_type == FieldType.ENUM
        assert customer_fields["size"].enum_values == ["SMB", "Mid-Market", "Enterprise"]
        
        assert "arr" in customer_fields
        assert customer_fields["arr"].field_type == FieldType.INTEGER
        
        # Check optional fields
        assert "health_score" in customer_fields
        assert customer_fields["health_score"].required == False
    
    def test_product_entity_fields(self):
        """Test Product entity fields"""
        product_fields = SPYRO_ENTITIES["Product"]
        
        assert "id" in product_fields
        assert "name" in product_fields
        assert "category" in product_fields
        
        # Check features array field
        assert "features" in product_fields
        assert product_fields["features"].field_type == FieldType.ARRAY
        assert product_fields["features"].array_type == FieldType.STRING
        
        # Check status enum
        assert "status" in product_fields
        assert product_fields["status"].field_type == FieldType.ENUM
        assert "active" in product_fields["status"].enum_values
    
    def test_subscription_entity_fields(self):
        """Test Subscription entity fields"""
        sub_fields = SPYRO_ENTITIES["Subscription"]
        
        # Check references
        assert "customer_id" in sub_fields
        assert sub_fields["customer_id"].required == True
        assert "product_id" in sub_fields
        assert sub_fields["product_id"].required == True
        
        # Check money fields
        assert "mrr" in sub_fields
        assert sub_fields["mrr"].field_type == FieldType.INTEGER
        assert "arr" in sub_fields
        assert sub_fields["arr"].field_type == FieldType.INTEGER
        
        # Check date fields
        assert "start_date" in sub_fields
        assert sub_fields["start_date"].field_type == FieldType.DATE
    
    def test_get_entity_fields(self):
        """Test get_entity_fields helper"""
        customer_fields = get_entity_fields("Customer")
        assert len(customer_fields) > 0
        assert "id" in customer_fields
        
        # Test unknown entity
        unknown_fields = get_entity_fields("UnknownEntity")
        assert unknown_fields == {}
    
    def test_get_required_fields(self):
        """Test get_required_fields helper"""
        customer_required = get_required_fields("Customer")
        assert "id" in customer_required
        assert "name" in customer_required
        assert "size" in customer_required
        assert "arr" in customer_required
        assert "created_date" in customer_required
        assert "updated_date" in customer_required
        
        # Optional fields should not be in required
        assert "health_score" not in customer_required
        assert "website" not in customer_required
    
    def test_validate_entity_data_valid(self):
        """Test validating valid entity data"""
        valid_customer = {
            "id": "cust_001",
            "name": "Acme Corp",
            "size": "Enterprise",
            "industry": "Technology",
            "arr": 1000000,
            "created_date": "2024-01-15",
            "updated_date": "2024-01-20"
        }
        
        errors = validate_entity_data("Customer", valid_customer)
        assert len(errors) == 0
    
    def test_validate_entity_data_missing_required(self):
        """Test validation with missing required fields"""
        incomplete_customer = {
            "id": "cust_001",
            "name": "Acme Corp"
            # Missing: size, industry, arr, dates
        }
        
        errors = validate_entity_data("Customer", incomplete_customer)
        assert len(errors) > 0
        assert any("Missing required field" in error for error in errors)
        assert any("size" in error for error in errors)
        assert any("arr" in error for error in errors)
    
    def test_validate_entity_data_invalid_types(self):
        """Test validation with invalid field types"""
        invalid_customer = {
            "id": "cust_001",
            "name": "Acme Corp",
            "size": "Invalid Size",  # Not in enum
            "industry": "Technology",
            "arr": "not a number",  # Should be integer
            "created_date": "2024-01-15",
            "updated_date": "2024-01-20"
        }
        
        errors = validate_entity_data("Customer", invalid_customer)
        assert len(errors) > 0
        assert any("size" in error for error in errors)
        assert any("arr" in error for error in errors)
    
    def test_validate_entity_data_unknown_fields(self):
        """Test validation with unknown fields"""
        customer_with_extra = {
            "id": "cust_001",
            "name": "Acme Corp",
            "size": "Enterprise",
            "industry": "Technology",
            "arr": 1000000,
            "created_date": "2024-01-15",
            "updated_date": "2024-01-20",
            "unknown_field": "value",
            "another_unknown": 123
        }
        
        errors = validate_entity_data("Customer", customer_with_extra)
        assert len(errors) == 2
        assert any("unknown_field" in error for error in errors)
        assert any("another_unknown" in error for error in errors)
    
    def test_validate_unknown_entity(self):
        """Test validation with unknown entity type"""
        errors = validate_entity_data("UnknownEntity", {"field": "value"})
        assert len(errors) == 1
        assert "Unknown entity type" in errors[0]
    
    def test_all_entities_have_id(self):
        """Test that all entities have an id field"""
        for entity_name, fields in SPYRO_ENTITIES.items():
            assert "id" in fields, f"{entity_name} missing id field"
            assert fields["id"].required == True
            assert fields["id"].field_type == FieldType.STRING