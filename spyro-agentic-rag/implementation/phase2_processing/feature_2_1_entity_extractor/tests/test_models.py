"""Tests for data models"""

import pytest
from datetime import datetime
import uuid

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity, EntityType, MappingRule, ValidationError,
    ValidationResult, DetectedEntity, ConfidenceLevel
)


class TestEntity:
    """Test Entity model"""
    
    def test_entity_creation(self):
        """Test creating an entity"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            source_id="cust_123",
            source_system="salesforce",
            attributes={"name": "TechCorp", "arr": 500000}
        )
        
        assert entity.type == EntityType.CUSTOMER
        assert entity.source_id == "cust_123"
        assert entity.source_system == "salesforce"
        assert entity.attributes["name"] == "TechCorp"
        assert entity.confidence == 1.0
    
    def test_entity_merge(self):
        """Test merging entities"""
        entity1 = Entity(
            type=EntityType.CUSTOMER,
            source_id="sf_123",
            source_system="salesforce",
            attributes={"name": "TechCorp", "arr": 500000}
        )
        
        entity2 = Entity(
            type=EntityType.CUSTOMER,
            source_id="gs_456",
            source_system="gainsight",
            attributes={"name": "Tech Corp", "employees": 100}
        )
        
        merged = entity1.merge_with(entity2)
        
        # Check merged attributes
        assert merged.attributes["name"] == "Tech Corp"  # entity2 takes precedence
        assert merged.attributes["arr"] == 500000  # from entity1
        assert merged.attributes["employees"] == 100  # from entity2
        
        # Check source tracking
        assert merged.source_ids["salesforce"] == "sf_123"
        assert merged.source_ids["gainsight"] == "gs_456"
        assert entity1.id in merged.merged_from
        assert entity2.id in merged.merged_from
    
    def test_entity_to_dict(self):
        """Test entity serialization"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            source_id="cust_123",
            attributes={"name": "TechCorp"}
        )
        
        data = entity.to_dict()
        
        assert data["type"] == "Customer"
        assert data["source_id"] == "cust_123"
        assert data["attributes"]["name"] == "TechCorp"
        assert "id" in data
        assert "extracted_at" in data


class TestMappingRule:
    """Test MappingRule model"""
    
    def test_mapping_rule_creation(self):
        """Test creating a mapping rule"""
        rule = MappingRule(
            entity_type="Customer",
            target_field="name",
            transformation="uppercase",
            required=True,
            default_value="Unknown"
        )
        
        assert rule.entity_type == "Customer"
        assert rule.target_field == "name"
        assert rule.transformation == "uppercase"
        assert rule.required is True
        assert rule.default_value == "Unknown"
    
    def test_mapping_rule_defaults(self):
        """Test mapping rule defaults"""
        rule = MappingRule(
            entity_type="Customer",
            target_field="name"
        )
        
        assert rule.transformation is None
        assert rule.required is True
        assert rule.default_value is None


class TestValidationModels:
    """Test validation-related models"""
    
    def test_validation_error(self):
        """Test ValidationError creation"""
        error = ValidationError(
            entity_id="123",
            field="email",
            error_type="invalid_format",
            message="Invalid email format",
            severity="error",
            suggested_fix="user@example.com"
        )
        
        assert error.entity_id == "123"
        assert error.field == "email"
        assert error.error_type == "invalid_format"
        assert error.severity == "error"
        assert error.suggested_fix == "user@example.com"
    
    def test_validation_result(self):
        """Test ValidationResult"""
        errors = [
            ValidationError(
                entity_id="123",
                field="name",
                error_type="missing",
                message="Name is required"
            )
        ]
        
        warnings = [
            ValidationError(
                entity_id="123",
                field="arr",
                error_type="out_of_range",
                message="ARR is unusually high",
                severity="warning"
            )
        ]
        
        result = ValidationResult(
            is_valid=False,
            errors=errors,
            warnings=warnings
        )
        
        assert not result.is_valid
        assert result.has_errors
        assert result.has_warnings
        assert len(result.errors) == 1
        assert len(result.warnings) == 1


class TestDetectedEntity:
    """Test DetectedEntity model"""
    
    def test_detected_entity_creation(self):
        """Test creating a detected entity"""
        detected = DetectedEntity(
            text="TechCorp Inc.",
            type=EntityType.CUSTOMER,
            start_pos=10,
            end_pos=23,
            confidence=0.9,
            detection_method="pattern"
        )
        
        assert detected.text == "TechCorp Inc."
        assert detected.type == EntityType.CUSTOMER
        assert detected.start_pos == 10
        assert detected.end_pos == 23
        assert detected.confidence == 0.9
        assert detected.detection_method == "pattern"


class TestEntityType:
    """Test EntityType enum"""
    
    def test_entity_types(self):
        """Test all entity types are defined"""
        expected_types = [
            "CUSTOMER", "PRODUCT", "SUBSCRIPTION",
            "TEAM", "PROJECT", "RISK", "OBJECTIVE", "UNKNOWN"
        ]
        
        actual_types = [t.name for t in EntityType]
        
        for expected in expected_types:
            assert expected in actual_types
    
    def test_entity_type_values(self):
        """Test entity type string values"""
        assert EntityType.CUSTOMER.value == "Customer"
        assert EntityType.PRODUCT.value == "Product"
        assert EntityType.SUBSCRIPTION.value == "Subscription"