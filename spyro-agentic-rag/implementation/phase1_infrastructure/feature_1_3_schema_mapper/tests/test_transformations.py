"""Tests for transformation functions"""

import pytest
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.transformations import TransformationLibrary


class TestTransformationLibrary:
    """Test cases for TransformationLibrary"""
    
    def test_cast_type_string(self):
        """Test casting to string"""
        assert TransformationLibrary.cast_type(123, "string") == "123"
        assert TransformationLibrary.cast_type(True, "string") == "True"
        assert TransformationLibrary.cast_type(None, "string", "default") == "default"
    
    def test_cast_type_integer(self):
        """Test casting to integer"""
        assert TransformationLibrary.cast_type("123", "integer") == 123
        assert TransformationLibrary.cast_type(123.45, "integer") == 123
        assert TransformationLibrary.cast_type("$1,234", "integer") == 1234
        assert TransformationLibrary.cast_type("invalid", "integer", 0) == 0
    
    def test_cast_type_float(self):
        """Test casting to float"""
        assert TransformationLibrary.cast_type("123.45", "float") == 123.45
        assert TransformationLibrary.cast_type(123, "float") == 123.0
        assert TransformationLibrary.cast_type("$1,234.56", "float") == 1234.56
    
    def test_cast_type_boolean(self):
        """Test casting to boolean"""
        assert TransformationLibrary.cast_type("true", "boolean") == True
        assert TransformationLibrary.cast_type("yes", "boolean") == True
        assert TransformationLibrary.cast_type("1", "boolean") == True
        assert TransformationLibrary.cast_type("false", "boolean") == False
        assert TransformationLibrary.cast_type("no", "boolean") == False
        assert TransformationLibrary.cast_type(0, "boolean") == False
    
    def test_extract_nested(self):
        """Test nested value extraction"""
        data = {
            "user": {
                "name": "John",
                "contact": {
                    "email": "john@example.com",
                    "phones": ["123", "456"]
                }
            }
        }
        
        assert TransformationLibrary.extract_nested(data, "user.name") == "John"
        assert TransformationLibrary.extract_nested(data, "user.contact.email") == "john@example.com"
        assert TransformationLibrary.extract_nested(data, "user.contact.phones.0") == "123"
        assert TransformationLibrary.extract_nested(data, "nonexistent", "default") == "default"
    
    def test_compute_value(self):
        """Test value computation"""
        values = {"a": 10, "b": 20, "c": 5}
        
        # Test addition
        assert TransformationLibrary.compute_value(values, "a + b") == 30
        assert TransformationLibrary.compute_value(values, "a + b + c") == 35
        
        # Test multiplication
        assert TransformationLibrary.compute_value(values, "a * c") == 50
        
        # Test direct reference
        assert TransformationLibrary.compute_value(values, "b") == 20
    
    def test_regex_extract(self):
        """Test regex extraction"""
        assert TransformationLibrary.regex_extract(
            "Order #12345", r"#(\d+)", 1
        ) == "12345"
        
        assert TransformationLibrary.regex_extract(
            "Email: john@example.com", r"Email: (\S+)", 1
        ) == "john@example.com"
        
        assert TransformationLibrary.regex_extract(
            "No match", r"\d+", 0, "default"
        ) == "default"
    
    def test_split_string(self):
        """Test string splitting"""
        assert TransformationLibrary.split_string("a,b,c") == ["a", "b", "c"]
        assert TransformationLibrary.split_string("a, b, c") == ["a", "b", "c"]
        assert TransformationLibrary.split_string("a|b|c", "|") == ["a", "b", "c"]
        assert TransformationLibrary.split_string("single") == ["single"]
        assert TransformationLibrary.split_string("") == []
    
    def test_join_array(self):
        """Test array joining"""
        assert TransformationLibrary.join_array(["a", "b", "c"]) == "a, b, c"
        assert TransformationLibrary.join_array(["a", "b", "c"], " | ") == "a | b | c"
        assert TransformationLibrary.join_array([1, 2, 3]) == "1, 2, 3"
        assert TransformationLibrary.join_array("not a list") == "not a list"
    
    def test_lookup_value(self):
        """Test value lookup"""
        lookup_table = {
            "US": "United States",
            "UK": "United Kingdom",
            "CA": "Canada"
        }
        
        assert TransformationLibrary.lookup_value("US", lookup_table) == "United States"
        assert TransformationLibrary.lookup_value("UK", lookup_table) == "United Kingdom"
        assert TransformationLibrary.lookup_value("XX", lookup_table, "Unknown") == "Unknown"
    
    def test_conditional_value(self):
        """Test conditional logic"""
        values = {"status": "active", "score": 85, "type": "premium"}
        
        conditions = [
            {"field": "status", "operator": "==", "value": "active", "result": "Good"},
            {"field": "status", "operator": "==", "value": "inactive", "result": "Bad"},
            {"default": "Unknown"}
        ]
        
        assert TransformationLibrary.conditional_value(values, conditions) == "Good"
        
        # Test numeric comparison
        conditions = [
            {"field": "score", "operator": ">", "value": 90, "result": "Excellent"},
            {"field": "score", "operator": ">=", "value": 80, "result": "Good"},
            {"field": "score", "operator": ">=", "value": 70, "result": "Fair"},
            {"default": "Poor"}
        ]
        
        assert TransformationLibrary.conditional_value(values, conditions) == "Good"
        
        # Test contains operator
        conditions = [
            {"field": "type", "operator": "contains", "value": "prem", "result": "Premium User"},
            {"default": "Regular User"}
        ]
        
        assert TransformationLibrary.conditional_value(values, conditions) == "Premium User"
    
    def test_normalize_date(self):
        """Test date normalization"""
        # Test various formats
        assert TransformationLibrary.normalize_date("2024-01-15") == "2024-01-15"
        assert TransformationLibrary.normalize_date("2024/01/15") == "2024-01-15"
        assert TransformationLibrary.normalize_date("01/15/2024") == "2024-01-15"
        assert TransformationLibrary.normalize_date("15/01/2024") == "2024-01-15"
        
        # Test datetime to date
        assert TransformationLibrary.normalize_date("2024-01-15T10:30:00") == "2024-01-15"
        assert TransformationLibrary.normalize_date("2024-01-15T10:30:00Z") == "2024-01-15"
        
        # Test datetime object
        dt = datetime(2024, 1, 15, 10, 30)
        assert TransformationLibrary.normalize_date(dt) == "2024-01-15"
        
        # Test invalid date
        assert TransformationLibrary.normalize_date("invalid") is None
        assert TransformationLibrary.normalize_date(None) is None
    
    def test_normalize_money(self):
        """Test money normalization"""
        # Test various formats
        assert TransformationLibrary.normalize_money(100) == 10000  # to cents
        assert TransformationLibrary.normalize_money("100") == 10000
        assert TransformationLibrary.normalize_money("$100") == 10000
        assert TransformationLibrary.normalize_money("$1,234.56") == 123456
        assert TransformationLibrary.normalize_money("-50.25") == -5025
        
        # Test without cents conversion
        assert TransformationLibrary.normalize_money(100.50, to_cents=False) == 100
        
        # Test invalid values
        assert TransformationLibrary.normalize_money("invalid") is None
        assert TransformationLibrary.normalize_money(None) is None
    
    def test_normalize_enum(self):
        """Test enum normalization"""
        mapping = {
            "active": "active",
            "live": "active",
            "inactive": "churned",
            "cancelled": "churned"
        }
        
        assert TransformationLibrary.normalize_enum("active", mapping) == "active"
        assert TransformationLibrary.normalize_enum("LIVE", mapping) == "active"
        assert TransformationLibrary.normalize_enum("inactive", mapping) == "churned"
        assert TransformationLibrary.normalize_enum("unknown", mapping, "default") == "default"
        
        # Test partial matching
        assert TransformationLibrary.normalize_enum("is_active", mapping) == "active"
    
    def test_concatenate_values(self):
        """Test value concatenation"""
        values = {
            "first_name": "John",
            "last_name": "Doe",
            "middle": "",
            "title": "Dr."
        }
        
        assert TransformationLibrary.concatenate_values(
            values, ["first_name", "last_name"]
        ) == "John Doe"
        
        assert TransformationLibrary.concatenate_values(
            values, ["title", "first_name", "last_name"], " "
        ) == "Dr. John Doe"
        
        # Test skip_empty
        assert TransformationLibrary.concatenate_values(
            values, ["first_name", "middle", "last_name"], " ", skip_empty=True
        ) == "John Doe"
        
        assert TransformationLibrary.concatenate_values(
            values, ["first_name", "middle", "last_name"], " ", skip_empty=False
        ) == "John  Doe"
    
    def test_parse_json_string(self):
        """Test JSON parsing"""
        json_str = '{"name": "John", "age": 30}'
        result = TransformationLibrary.parse_json_string(json_str)
        assert result == {"name": "John", "age": 30}
        
        # Test invalid JSON
        assert TransformationLibrary.parse_json_string("invalid", "default") == "default"
        
        # Test non-string input
        assert TransformationLibrary.parse_json_string({"already": "dict"}) == {"already": "dict"}
    
    def test_to_array(self):
        """Test array conversion"""
        assert TransformationLibrary.to_array([1, 2, 3]) == [1, 2, 3]
        assert TransformationLibrary.to_array("a,b,c", ",") == ["a", "b", "c"]
        assert TransformationLibrary.to_array("single") == ["single"]
        assert TransformationLibrary.to_array(None) == []
    
    def test_from_array(self):
        """Test array extraction"""
        assert TransformationLibrary.from_array([1, 2, 3], 0) == 1
        assert TransformationLibrary.from_array([1, 2, 3], 2) == 3
        assert TransformationLibrary.from_array([1, 2, 3], 5, "default") == "default"
        assert TransformationLibrary.from_array("not array", 0) == "not array"
    
    def test_calculate_arr_from_mrr(self):
        """Test ARR calculation"""
        assert TransformationLibrary.calculate_arr_from_mrr({"mrr": 1000}) == 12000
        assert TransformationLibrary.calculate_arr_from_mrr({"mrr": 833.33}) == 9999
        assert TransformationLibrary.calculate_arr_from_mrr({"monthly": 1000}, "monthly") == 12000
        assert TransformationLibrary.calculate_arr_from_mrr({}) is None
    
    def test_custom_transform_registration(self):
        """Test custom transformation registration"""
        lib = TransformationLibrary()
        
        # Register custom transform
        def custom_transform(value, prefix="Custom:"):
            return f"{prefix} {value}"
        
        lib.register_custom_transform("add_prefix", custom_transform)
        
        # Test retrieval
        transform_fn = lib.get_transform("add_prefix")
        assert transform_fn is not None
        assert transform_fn("test") == "Custom: test"
        assert transform_fn("test", prefix="Special:") == "Special: test"