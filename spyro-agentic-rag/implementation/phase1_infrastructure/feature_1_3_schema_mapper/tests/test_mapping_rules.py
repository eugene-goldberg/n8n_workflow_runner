"""Tests for mapping rules"""

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mapping_rules import (
    TransformationType, MappingRule, MappingRuleSet,
    CommonPatterns, create_default_rules
)
from src.transformations import TransformationLibrary


class TestMappingRule:
    """Test cases for MappingRule"""
    
    def test_basic_rule_creation(self):
        """Test creating a basic mapping rule"""
        rule = MappingRule(
            source_field="company_name",
            target_entity="Customer",
            target_field="name",
            transformation=TransformationType.RENAME,
            confidence=0.95
        )
        
        assert rule.source_field == "company_name"
        assert rule.target_entity == "Customer"
        assert rule.target_field == "name"
        assert rule.transformation == TransformationType.RENAME
        assert rule.confidence == 0.95
    
    def test_rule_with_multiple_source_fields(self):
        """Test rule with multiple source fields"""
        rule = MappingRule(
            source_field=["first_name", "last_name"],
            target_entity="Customer",
            target_field="name",
            transformation=TransformationType.COMPUTE,
            transform_params={"expression": "first_name + ' ' + last_name"}
        )
        
        assert isinstance(rule.source_field, list)
        assert len(rule.source_field) == 2
    
    def test_apply_direct_transformation(self):
        """Test applying direct transformation"""
        rule = MappingRule(
            source_field="value",
            target_entity="Customer",
            target_field="name",
            transformation=TransformationType.DIRECT
        )
        
        source_data = {"value": "Test Company"}
        result = rule.apply(source_data)
        assert result == "Test Company"
    
    def test_apply_rename_transformation(self):
        """Test applying rename transformation"""
        rule = MappingRule(
            source_field="company",
            target_entity="Customer",
            target_field="name",
            transformation=TransformationType.RENAME
        )
        
        source_data = {"company": "Acme Corp"}
        result = rule.apply(source_data)
        assert result == "Acme Corp"
    
    def test_apply_constant_transformation(self):
        """Test applying constant transformation"""
        rule = MappingRule(
            source_field="dummy",
            target_entity="Customer",
            target_field="size",
            transformation=TransformationType.CONSTANT,
            transform_params={"value": "Enterprise"}
        )
        
        source_data = {"dummy": "ignored"}
        result = rule.apply(source_data)
        assert result == "Enterprise"
    
    def test_extract_nested_value(self):
        """Test extracting nested values"""
        rule = MappingRule(
            source_field="contact.email",
            target_entity="Customer",
            target_field="email",
            transformation=TransformationType.EXTRACT
        )
        
        source_data = {
            "contact": {
                "email": "test@example.com",
                "phone": "123-456-7890"
            }
        }
        
        # Use internal method for testing
        result = rule._extract_value(source_data, "contact.email")
        assert result == "test@example.com"
    
    def test_extract_array_element(self):
        """Test extracting array elements"""
        rule = MappingRule(
            source_field="tags.0",
            target_entity="Customer",
            target_field="primary_tag",
            transformation=TransformationType.EXTRACT
        )
        
        source_data = {"tags": ["important", "enterprise", "active"]}
        result = rule._extract_value(source_data, "tags.0")
        assert result == "important"
        
        # Test out of bounds
        result = rule._extract_value(source_data, "tags.10")
        assert result is None
    
    def test_apply_with_transformation_library(self):
        """Test applying rule with transformation library"""
        rule = MappingRule(
            source_field="revenue",
            target_entity="Customer",
            target_field="arr",
            transformation=TransformationType.CAST,
            transform_params={"to_type": "integer"}
        )
        
        source_data = {"revenue": "1000000"}
        transform_lib = TransformationLibrary()
        result = rule.apply(source_data, transform_lib)
        assert result == 1000000


class TestMappingRuleSet:
    """Test cases for MappingRuleSet"""
    
    def test_rule_set_creation(self):
        """Test creating a rule set"""
        rule_set = MappingRuleSet(
            name="test_rules",
            description="Test mapping rules"
        )
        
        assert rule_set.name == "test_rules"
        assert rule_set.description == "Test mapping rules"
        assert len(rule_set.rules) == 0
    
    def test_add_and_retrieve_rules(self):
        """Test adding and retrieving rules"""
        rule_set = MappingRuleSet("test")
        
        rule1 = MappingRule(
            source_field="field1",
            target_entity="Customer",
            target_field="name"
        )
        rule2 = MappingRule(
            source_field="field2",
            target_entity="Product",
            target_field="name"
        )
        
        rule_set.add_rule(rule1)
        rule_set.add_rule(rule2)
        
        assert len(rule_set.rules) == 2
    
    def test_get_rules_for_entity(self):
        """Test getting rules for specific entity"""
        rule_set = MappingRuleSet("test")
        
        # Add rules for different entities
        rule_set.add_rule(MappingRule("f1", "Customer", "name"))
        rule_set.add_rule(MappingRule("f2", "Customer", "size"))
        rule_set.add_rule(MappingRule("f3", "Product", "name"))
        
        customer_rules = rule_set.get_rules_for_entity("Customer")
        assert len(customer_rules) == 2
        
        product_rules = rule_set.get_rules_for_entity("Product")
        assert len(product_rules) == 1
    
    def test_get_rule_by_source(self):
        """Test getting rule by source field"""
        rule_set = MappingRuleSet("test")
        
        rule = MappingRule("company_name", "Customer", "name")
        rule_set.add_rule(rule)
        
        found_rule = rule_set.get_rule_by_source("company_name")
        assert found_rule is not None
        assert found_rule.target_field == "name"
        
        # Test not found
        not_found = rule_set.get_rule_by_source("nonexistent")
        assert not_found is None
    
    def test_get_rule_by_source_multiple_fields(self):
        """Test getting rule with multiple source fields"""
        rule_set = MappingRuleSet("test")
        
        rule = MappingRule(["first", "last"], "Customer", "name")
        rule_set.add_rule(rule)
        
        # Should find rule if any source field matches
        found = rule_set.get_rule_by_source("first")
        assert found is not None
        
        found = rule_set.get_rule_by_source("last")
        assert found is not None
    
    def test_validate_rules(self):
        """Test rule validation against schema"""
        rule_set = MappingRuleSet("test")
        
        rule_set.add_rule(MappingRule("existing_field", "Customer", "name"))
        rule_set.add_rule(MappingRule("nested.field", "Customer", "email"))
        rule_set.add_rule(MappingRule("missing_field", "Customer", "size"))
        
        schema = {
            "existing_field": {"type": "string"},
            "nested": {
                "type": "object",
                "properties": {
                    "field": {"type": "string"}
                }
            }
        }
        
        errors = rule_set.validate(schema)
        assert len(errors) == 1
        assert "missing_field" in errors[0]


class TestCommonPatterns:
    """Test cases for CommonPatterns"""
    
    def test_detect_customer_id_patterns(self):
        """Test detection of customer ID patterns"""
        assert CommonPatterns.detect_field_type("customer_id") == "customer_id"
        assert CommonPatterns.detect_field_type("customerId") == "customer_id"
        assert CommonPatterns.detect_field_type("client_id") == "customer_id"
        assert CommonPatterns.detect_field_type("account_id") == "customer_id"
        assert CommonPatterns.detect_field_type("company_id") == "customer_id"
        assert CommonPatterns.detect_field_type("org_id") == "customer_id"
    
    def test_detect_date_patterns(self):
        """Test detection of date patterns"""
        assert CommonPatterns.detect_field_type("created_date") == "date"
        assert CommonPatterns.detect_field_type("updated_at") == "date"
        assert CommonPatterns.detect_field_type("end_time") == "date"
        assert CommonPatterns.detect_field_type("created") == "date"
        assert CommonPatterns.detect_field_type("modified") == "date"
    
    def test_detect_money_patterns(self):
        """Test detection of money patterns"""
        assert CommonPatterns.detect_field_type("annual_revenue") == "money"
        assert CommonPatterns.detect_field_type("total_price") == "money"
        assert CommonPatterns.detect_field_type("monthly_cost") == "money"
        assert CommonPatterns.detect_field_type("payment_amount") == "money"
        assert CommonPatterns.detect_field_type("mrr") == "money"
        assert CommonPatterns.detect_field_type("arr") == "money"
    
    def test_detect_other_patterns(self):
        """Test detection of other field patterns"""
        assert CommonPatterns.detect_field_type("email_address") == "email"
        assert CommonPatterns.detect_field_type("contact_email") == "email"
        assert CommonPatterns.detect_field_type("phone_number") == "phone"
        assert CommonPatterns.detect_field_type("website_url") == "url"
        assert CommonPatterns.detect_field_type("page_count") == "integer"
        assert CommonPatterns.detect_field_type("success_rate") == "percentage"
        assert CommonPatterns.detect_field_type("order_status") == "enum"
    
    def test_no_pattern_match(self):
        """Test fields that don't match any pattern"""
        assert CommonPatterns.detect_field_type("random_field") is None
        assert CommonPatterns.detect_field_type("xyz123") is None


class TestDefaultRules:
    """Test cases for default rule creation"""
    
    def test_create_default_rules(self):
        """Test creating default rules"""
        default_rules = create_default_rules()
        
        assert "salesforce" in default_rules
        assert "hubspot" in default_rules
    
    def test_salesforce_default_rules(self):
        """Test Salesforce default rules"""
        default_rules = create_default_rules()
        sf_rules = default_rules["salesforce"]
        
        assert sf_rules.name == "salesforce"
        assert len(sf_rules.rules) > 0
        
        # Check specific rules
        account_rule = None
        for rule in sf_rules.rules:
            if rule.source_field == "AccountId":
                account_rule = rule
                break
        
        assert account_rule is not None
        assert account_rule.target_entity == "Customer"
        assert account_rule.target_field == "id"
    
    def test_hubspot_default_rules(self):
        """Test HubSpot default rules"""
        default_rules = create_default_rules()
        hs_rules = default_rules["hubspot"]
        
        assert hs_rules.name == "hubspot"
        assert len(hs_rules.rules) > 0
        
        # Check nested field extraction
        id_rule = None
        for rule in hs_rules.rules:
            if rule.source_field == "properties.hs_object_id":
                id_rule = rule
                break
        
        assert id_rule is not None
        assert id_rule.transformation == TransformationType.EXTRACT