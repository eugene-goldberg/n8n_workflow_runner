"""Tests for entity validators"""

import pytest
import asyncio
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.validators import EntityValidator
from src.models import Entity, EntityType, ValidationError, ValidationResult


class TestEntityValidator:
    """Test EntityValidator functionality"""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance"""
        return EntityValidator()
    
    @pytest.mark.asyncio
    async def test_validate_required_fields(self, validator):
        """Test validation of required fields"""
        # Missing required field
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={"name": "TestCorp"}  # Missing 'id'
        )
        
        result = await validator.validate_entity(entity)
        
        assert not result.is_valid
        assert result.has_errors
        assert len(result.errors) == 1
        assert result.errors[0].field == "id"
        assert result.errors[0].error_type == "missing_required"
    
    @pytest.mark.asyncio
    async def test_validate_field_types(self, validator):
        """Test validation of field types"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "arr": "not_a_number",  # Should be number
                "employee_count": 100.5  # Should be integer
            }
        )
        
        result = await validator.validate_entity(entity)
        
        assert not result.is_valid
        
        # Check ARR type error
        arr_errors = [e for e in result.errors if e.field == "arr"]
        assert len(arr_errors) == 1
        assert arr_errors[0].error_type == "invalid_type"
        
        # Check employee count type error
        emp_errors = [e for e in result.errors if e.field == "employee_count"]
        assert len(emp_errors) == 1
        assert emp_errors[0].error_type == "invalid_type"
    
    @pytest.mark.asyncio
    async def test_validate_field_formats(self, validator):
        """Test validation of field formats"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "email": "invalid.email",  # Invalid format
                "website": "not-a-url"  # Invalid format
            }
        )
        
        result = await validator.validate_entity(entity)
        
        assert not result.is_valid
        
        # Check email format error
        email_errors = [e for e in result.errors if e.field == "email"]
        assert len(email_errors) == 1
        assert email_errors[0].error_type == "invalid_format"
        assert email_errors[0].suggested_fix is None  # Can't fix this email
        
        # Check website format error
        website_errors = [e for e in result.errors if e.field == "website"]
        assert len(website_errors) == 1
        assert website_errors[0].error_type == "invalid_format"
    
    @pytest.mark.asyncio
    async def test_validate_field_ranges(self, validator):
        """Test validation of field ranges"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "arr": -1000,  # Negative ARR
                "employee_count": 2000000  # Too many employees
            }
        )
        
        result = await validator.validate_entity(entity)
        
        # Range violations should be warnings, not errors
        assert result.is_valid  # Still valid
        assert result.has_warnings
        
        # Check ARR warning
        arr_warnings = [w for w in result.warnings if w.field == "arr"]
        assert len(arr_warnings) == 1
        assert "below minimum" in arr_warnings[0].message
        
        # Check employee count warning
        emp_warnings = [w for w in result.warnings if w.field == "employee_count"]
        assert len(emp_warnings) == 1
        assert "exceeds maximum" in emp_warnings[0].message
    
    @pytest.mark.asyncio
    async def test_business_rules_customer(self, validator):
        """Test customer-specific business rules"""
        # Active customer with zero ARR
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "status": "active",
                "arr": 0
            }
        )
        
        result = await validator.validate_entity(entity)
        
        assert not result.is_valid
        business_errors = [
            e for e in result.errors
            if e.error_type == "business_rule"
        ]
        assert len(business_errors) == 1
        assert "positive ARR" in business_errors[0].message
    
    @pytest.mark.asyncio
    async def test_business_rules_subscription(self, validator):
        """Test subscription-specific business rules"""
        # End date before start date
        entity = Entity(
            type=EntityType.SUBSCRIPTION,
            attributes={
                "id": "sub_001",
                "customer_id": "cust_001",
                "product_id": "prod_001",
                "start_date": "2024-06-01T00:00:00",
                "end_date": "2024-01-01T00:00:00"
            }
        )
        
        result = await validator.validate_entity(entity)
        
        assert not result.is_valid
        date_errors = [
            e for e in result.errors
            if e.error_type == "business_rule" and "date" in e.message
        ]
        assert len(date_errors) == 1
    
    @pytest.mark.asyncio
    async def test_risk_validation(self, validator):
        """Test risk entity validation"""
        # Invalid severity
        entity = Entity(
            type=EntityType.RISK,
            attributes={
                "id": "risk_001",
                "title": "Test Risk",
                "severity": "extreme",  # Not allowed
                "probability": 1.5,  # Out of range
                "impact": -1  # Negative impact
            }
        )
        
        result = await validator.validate_entity(entity)
        
        assert not result.is_valid
        
        # Severity format error
        severity_errors = [e for e in result.errors if e.field == "severity"]
        assert len(severity_errors) == 1
        
        # Probability range warning
        prob_warnings = [w for w in result.warnings if w.field == "probability"]
        assert len(prob_warnings) == 1
    
    @pytest.mark.asyncio
    async def test_type_conversion_suggestions(self, validator):
        """Test type conversion in suggested fixes"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "arr": "500,000",  # String that can be converted
                "employee_count": "100"  # String that can be converted
            }
        )
        
        result = await validator.validate_entity(entity)
        
        # Should have type errors with suggested fixes
        arr_errors = [e for e in result.errors if e.field == "arr"]
        assert len(arr_errors) == 1
        assert arr_errors[0].suggested_fix == 500000.0
        
        emp_errors = [e for e in result.errors if e.field == "employee_count"]
        assert len(emp_errors) == 1
        assert emp_errors[0].suggested_fix == 100
    
    @pytest.mark.asyncio
    async def test_email_format_fix(self, validator):
        """Test email format fixing"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "email": "  USER@EXAMPLE.COM  "  # Needs cleanup
            }
        )
        
        result = await validator.validate_entity(entity)
        
        # Should suggest cleaned email
        email_errors = [e for e in result.errors if e.field == "email"]
        assert len(email_errors) == 1
        assert email_errors[0].suggested_fix == "user@example.com"
    
    @pytest.mark.asyncio
    async def test_url_format_fix(self, validator):
        """Test URL format fixing"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "website": "example.com"  # Missing protocol
            }
        )
        
        result = await validator.validate_entity(entity)
        
        # Should suggest URL with protocol
        website_errors = [e for e in result.errors if e.field == "website"]
        assert len(website_errors) == 1
        assert website_errors[0].suggested_fix == "https://example.com"
    
    @pytest.mark.asyncio
    async def test_custom_validation_rules(self, validator):
        """Test validation with custom rules"""
        custom_rules = {
            "required_fields": ["id", "name", "custom_field"],
            "field_types": {
                "custom_field": "string"
            },
            "field_ranges": {
                "score": {"min": 0, "max": 100}
            }
        }
        
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp"
                # Missing custom_field
            }
        )
        
        result = await validator.validate_entity(entity, custom_rules)
        
        assert not result.is_valid
        custom_errors = [e for e in result.errors if e.field == "custom_field"]
        assert len(custom_errors) == 1
    
    @pytest.mark.asyncio
    async def test_datetime_validation(self, validator):
        """Test datetime field validation"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp",
                "created_date": "not-a-date"  # Invalid datetime
            }
        )
        
        result = await validator.validate_entity(entity)
        
        date_errors = [e for e in result.errors if e.field == "created_date"]
        assert len(date_errors) == 1
        assert date_errors[0].error_type == "invalid_type"
    
    @pytest.mark.asyncio
    async def test_valid_entity(self, validator):
        """Test validation of a completely valid entity"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "ValidCorp",
                "arr": 500000,
                "employee_count": 100,
                "email": "contact@validcorp.com",
                "website": "https://validcorp.com",
                "status": "active",
                "created_date": datetime.now().isoformat()
            }
        )
        
        result = await validator.validate_entity(entity)
        
        assert result.is_valid
        assert not result.has_errors
        assert not result.has_warnings
    
    @pytest.mark.asyncio
    async def test_default_value_suggestions(self, validator):
        """Test default value suggestions for missing fields"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "id": "cust_001",
                "name": "TestCorp"
                # Missing fields that have defaults
            }
        )
        
        # Temporarily add status to required fields for testing
        custom_rules = {
            "required_fields": ["id", "name", "status"],
            "field_types": {"status": "string"}
        }
        
        result = await validator.validate_entity(entity, custom_rules)
        
        status_errors = [e for e in result.errors if e.field == "status"]
        assert len(status_errors) == 1
        assert status_errors[0].suggested_fix == "active"  # Default value