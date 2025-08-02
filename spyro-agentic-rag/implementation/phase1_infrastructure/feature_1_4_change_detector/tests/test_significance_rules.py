"""Tests for significance rules"""

import pytest

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Change, ChangeType
from src.significance_rules import (
    FieldImportanceRule, ChangeTypeRule, ValueChangeRule,
    PatternRule, CriticalFieldRule, SignificanceEvaluator
)


class TestFieldImportanceRule:
    """Test cases for field importance rule"""
    
    def test_evaluate_single_field(self):
        """Test evaluating importance of single field change"""
        rule = FieldImportanceRule({
            "name": 0.8,
            "description": 0.3,
            "status": 0.9
        })
        
        # High importance field
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["status"]
        )
        assert rule.evaluate(change) == 0.9
        
        # Low importance field
        change.fields_changed = ["description"]
        assert rule.evaluate(change) == 0.3
        
        # Default importance
        change.fields_changed = ["unknown_field"]
        assert rule.evaluate(change) == 0.5
    
    def test_evaluate_multiple_fields(self):
        """Test evaluating multiple field changes"""
        rule = FieldImportanceRule({
            "status": 0.9,
            "name": 0.7,
            "description": 0.2
        })
        
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["status", "name", "description"]
        )
        
        # Average importance
        expected = (0.9 + 0.7 + 0.2) / 3
        assert rule.evaluate(change) == pytest.approx(expected)
    
    def test_no_fields_changed(self):
        """Test when no fields changed"""
        rule = FieldImportanceRule({})
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=[]
        )
        assert rule.evaluate(change) == 0.0


class TestChangeTypeRule:
    """Test cases for change type rule"""
    
    def test_default_weights(self):
        """Test default change type weights"""
        rule = ChangeTypeRule()
        
        # Create
        change = Change("Customer", "1", ChangeType.CREATE)
        assert rule.evaluate(change) == 0.8
        
        # Update
        change.operation = ChangeType.UPDATE
        assert rule.evaluate(change) == 0.5
        
        # Delete
        change.operation = ChangeType.DELETE
        assert rule.evaluate(change) == 0.9
    
    def test_custom_weights(self):
        """Test custom change type weights"""
        rule = ChangeTypeRule({
            ChangeType.CREATE: 0.6,
            ChangeType.UPDATE: 0.3,
            ChangeType.DELETE: 1.0
        })
        
        change = Change("Customer", "1", ChangeType.CREATE)
        assert rule.evaluate(change) == 0.6
        
        change.operation = ChangeType.DELETE
        assert rule.evaluate(change) == 1.0


class TestValueChangeRule:
    """Test cases for value change rule"""
    
    def test_numeric_changes(self):
        """Test numeric value changes"""
        rule = ValueChangeRule({
            "revenue": 0.05,  # 5% threshold
            "count": 0.2      # 20% threshold
        })
        
        # Small change (below threshold)
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["revenue"],
            old_values={"revenue": 1000},
            new_values={"revenue": 1030}  # 3% change
        )
        significance = rule.evaluate(change)
        assert significance < 0.5
        
        # Large change (above threshold)
        change.new_values = {"revenue": 1200}  # 20% change
        significance = rule.evaluate(change)
        assert significance > 0.5
        
        # Zero to non-zero
        change.old_values = {"revenue": 0}
        change.new_values = {"revenue": 100}
        assert rule.evaluate(change) == 1.0
    
    def test_string_changes(self):
        """Test string value changes"""
        rule = ValueChangeRule()
        
        # Case change only
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["name"],
            old_values={"name": "test company"},
            new_values={"name": "Test Company"}
        )
        assert rule.evaluate(change) == 0.1
        
        # Partial change
        change.old_values = {"name": "Test"}
        change.new_values = {"name": "Test Company"}
        assert rule.evaluate(change) == 0.3
        
        # Complete change
        change.old_values = {"name": "Old Name"}
        change.new_values = {"name": "New Name"}
        assert rule.evaluate(change) == 0.7
    
    def test_boolean_changes(self):
        """Test boolean value changes"""
        rule = ValueChangeRule()
        
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["active"],
            old_values={"active": True},
            new_values={"active": False}
        )
        assert rule.evaluate(change) == 0.8
        
        # No change
        change.new_values = {"active": True}
        assert rule.evaluate(change) == 0.0
    
    def test_non_update_operation(self):
        """Test non-update operations"""
        rule = ValueChangeRule()
        
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.CREATE
        )
        assert rule.evaluate(change) == 0.5


class TestPatternRule:
    """Test cases for pattern rule"""
    
    def test_pattern_matching(self):
        """Test field name pattern matching"""
        rule = PatternRule({
            r".*_id$": 0.2,
            r".*revenue.*": 0.9,
            r"^is_.*": 0.6
        })
        
        # ID field
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["customer_id"]
        )
        assert rule.evaluate(change) == 0.2
        
        # Revenue field
        change.fields_changed = ["annual_revenue"]
        assert rule.evaluate(change) == 0.9
        
        # Boolean field
        change.fields_changed = ["is_active"]
        assert rule.evaluate(change) == 0.6
        
        # No match
        change.fields_changed = ["random_field"]
        assert rule.evaluate(change) == 0.0
    
    def test_multiple_patterns(self):
        """Test when multiple patterns match"""
        rule = PatternRule({
            r".*_id$": 0.2,
            r"customer.*": 0.7
        })
        
        # Field matches both patterns - should use highest score
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["customer_id"]
        )
        assert rule.evaluate(change) == 0.7


class TestCriticalFieldRule:
    """Test cases for critical field rule"""
    
    def test_critical_field_detection(self):
        """Test detection of critical fields"""
        rule = CriticalFieldRule({"status", "payment_status", "churn_risk"})
        
        # Critical field changed
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["status", "name"]
        )
        assert rule.evaluate(change) == 0.95
        
        # No critical fields
        change.fields_changed = ["name", "description"]
        assert rule.evaluate(change) == 0.0
        
        # Empty fields
        change.fields_changed = []
        assert rule.evaluate(change) == 0.0


class TestSignificanceEvaluator:
    """Test cases for significance evaluator"""
    
    def test_default_rules(self):
        """Test evaluator with default rules"""
        evaluator = SignificanceEvaluator()
        
        # Critical field change
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["status"],
            old_values={"status": "active"},
            new_values={"status": "churned"}
        )
        significance = evaluator.evaluate(change)
        assert significance > 0.8  # Should be high
        
        # Trivial change
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["updated_date"],
            old_values={"updated_date": "2024-01-01"},
            new_values={"updated_date": "2024-01-02"}
        )
        significance = evaluator.evaluate(change)
        assert significance < 0.6  # Should be relatively low
    
    def test_custom_rules(self):
        """Test evaluator with custom rules"""
        evaluator = SignificanceEvaluator([
            ChangeTypeRule({
                ChangeType.CREATE: 1.0,
                ChangeType.UPDATE: 0.0,
                ChangeType.DELETE: 0.0
            })
        ])
        
        # Only CREATE should have high significance
        change = Change("Customer", "1", ChangeType.CREATE)
        assert evaluator.evaluate(change) == 1.0
        
        change.operation = ChangeType.UPDATE
        assert evaluator.evaluate(change) == 0.5  # Default when no rules match
    
    def test_add_remove_rules(self):
        """Test adding and removing rules"""
        evaluator = SignificanceEvaluator([])
        
        # Add rule
        rule = ChangeTypeRule()
        evaluator.add_rule(rule)
        assert len(evaluator.rules) == 1
        
        # Evaluate with rule
        change = Change("Customer", "1", ChangeType.DELETE)
        assert evaluator.evaluate(change) == 0.9
        
        # Remove rule
        evaluator.remove_rule("change_type")
        assert len(evaluator.rules) == 0
        assert evaluator.evaluate(change) == 0.5  # Default
    
    def test_weighted_average(self):
        """Test weighted average calculation"""
        evaluator = SignificanceEvaluator([
            ChangeTypeRule({ChangeType.UPDATE: 0.8}),
            FieldImportanceRule({"name": 0.4})
        ])
        
        change = Change(
            entity_type="Customer",
            entity_id="1",
            operation=ChangeType.UPDATE,
            fields_changed=["name"]
        )
        
        # Should give more weight to higher score (0.8)
        significance = evaluator.evaluate(change)
        assert significance > 0.5
        assert significance < 0.8