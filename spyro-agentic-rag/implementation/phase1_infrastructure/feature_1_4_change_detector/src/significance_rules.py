"""Rules for determining change significance"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Set
import re

from .models import Change, ChangeType


@dataclass
class SignificanceRule(ABC):
    """Abstract base class for significance rules"""
    name: str
    description: str = ""
    
    @abstractmethod
    def evaluate(self, change: Change) -> float:
        """Evaluate the significance of a change (0.0 to 1.0)"""
        pass


class FieldImportanceRule(SignificanceRule):
    """Rule based on field importance"""
    
    def __init__(self, field_weights: Dict[str, float]):
        """Initialize with field importance weights
        
        Args:
            field_weights: Map of field names to importance (0.0-1.0)
        """
        super().__init__(
            name="field_importance",
            description="Evaluates significance based on field importance"
        )
        self.field_weights = field_weights
        self.default_weight = 0.5
    
    def evaluate(self, change: Change) -> float:
        """Evaluate based on importance of changed fields"""
        if not change.fields_changed:
            return 0.0
        
        # Calculate average importance of changed fields
        total_weight = 0.0
        for field in change.fields_changed:
            weight = self.field_weights.get(field, self.default_weight)
            total_weight += weight
        
        return min(1.0, total_weight / len(change.fields_changed))


class ChangeTypeRule(SignificanceRule):
    """Rule based on type of change"""
    
    def __init__(self, type_weights: Optional[Dict[ChangeType, float]] = None):
        """Initialize with change type weights"""
        super().__init__(
            name="change_type",
            description="Evaluates significance based on operation type"
        )
        self.type_weights = type_weights or {
            ChangeType.CREATE: 0.8,
            ChangeType.UPDATE: 0.5,
            ChangeType.DELETE: 0.9
        }
    
    def evaluate(self, change: Change) -> float:
        """Evaluate based on change type"""
        return self.type_weights.get(change.operation, 0.5)


class ValueChangeRule(SignificanceRule):
    """Rule based on magnitude of value changes"""
    
    def __init__(self, threshold_percentages: Optional[Dict[str, float]] = None):
        """Initialize with threshold percentages for fields"""
        super().__init__(
            name="value_change",
            description="Evaluates significance based on value change magnitude"
        )
        self.threshold_percentages = threshold_percentages or {}
        self.default_threshold = 0.1  # 10% change
    
    def evaluate(self, change: Change) -> float:
        """Evaluate based on value change magnitude"""
        if change.operation != ChangeType.UPDATE:
            return 0.5  # Not applicable
        
        significances = []
        
        for field in change.fields_changed:
            old_value = change.old_values.get(field)
            new_value = change.new_values.get(field)
            
            # Calculate significance for this field
            field_significance = self._calculate_field_significance(
                field, old_value, new_value
            )
            significances.append(field_significance)
        
        # Return average significance
        return sum(significances) / len(significances) if significances else 0.0
    
    def _calculate_field_significance(self, field: str, old_value: Any, new_value: Any) -> float:
        """Calculate significance for a single field change"""
        # Handle boolean changes first (since bool is subclass of int)
        if isinstance(old_value, bool) and isinstance(new_value, bool):
            return 0.8 if old_value != new_value else 0.0
        
        # Handle numeric changes
        elif isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            if old_value == 0:
                return 1.0 if new_value != 0 else 0.0
            
            percent_change = abs(new_value - old_value) / abs(old_value)
            threshold = self.threshold_percentages.get(field, self.default_threshold)
            
            # Map percentage change to significance
            if percent_change < threshold:
                return percent_change / threshold * 0.5
            else:
                return min(1.0, 0.5 + (percent_change - threshold) / threshold * 0.5)
        
        # Handle string changes
        elif isinstance(old_value, str) and isinstance(new_value, str):
            # Simple string comparison
            if old_value.lower() == new_value.lower():
                return 0.1  # Case change only
            elif old_value in new_value or new_value in old_value:
                return 0.3  # Partial change
            else:
                return 0.7  # Complete change
        
        # Default for other types
        return 0.5 if old_value != new_value else 0.0


class PatternRule(SignificanceRule):
    """Rule based on field name patterns"""
    
    def __init__(self, patterns: Dict[str, float]):
        """Initialize with patterns and their significance
        
        Args:
            patterns: Map of regex patterns to significance scores
        """
        super().__init__(
            name="pattern",
            description="Evaluates significance based on field name patterns"
        )
        self.patterns = {
            re.compile(pattern): score 
            for pattern, score in patterns.items()
        }
    
    def evaluate(self, change: Change) -> float:
        """Evaluate based on field name patterns"""
        if not change.fields_changed:
            return 0.0
        
        max_score = 0.0
        for field in change.fields_changed:
            for pattern, score in self.patterns.items():
                if pattern.match(field):
                    max_score = max(max_score, score)
        
        return max_score


class CriticalFieldRule(SignificanceRule):
    """Rule for critical fields that should always be significant"""
    
    def __init__(self, critical_fields: Set[str]):
        """Initialize with set of critical fields"""
        super().__init__(
            name="critical_fields",
            description="Marks changes to critical fields as highly significant"
        )
        self.critical_fields = critical_fields
    
    def evaluate(self, change: Change) -> float:
        """Evaluate if any critical fields changed"""
        if any(field in self.critical_fields for field in change.fields_changed):
            return 0.95
        return 0.0


class SignificanceEvaluator:
    """Evaluates change significance using multiple rules"""
    
    def __init__(self, rules: Optional[List[SignificanceRule]] = None):
        """Initialize with rules"""
        self.rules = rules if rules is not None else self._get_default_rules()
    
    def _get_default_rules(self) -> List[SignificanceRule]:
        """Get default significance rules"""
        return [
            # Field importance
            FieldImportanceRule({
                "id": 0.1,
                "name": 0.7,
                "status": 0.9,
                "arr": 0.8,
                "mrr": 0.8,
                "health_score": 0.7,
                "churn_risk": 0.9,
                "created_date": 0.3,
                "updated_date": 0.1
            }),
            
            # Change type weights
            ChangeTypeRule({
                ChangeType.CREATE: 0.8,
                ChangeType.UPDATE: 0.5,
                ChangeType.DELETE: 0.95
            }),
            
            # Value change thresholds
            ValueChangeRule({
                "arr": 0.05,      # 5% change threshold
                "mrr": 0.05,
                "health_score": 0.1,  # 10% change threshold
                "employee_count": 0.2  # 20% change threshold
            }),
            
            # Pattern matching
            PatternRule({
                r".*_id$": 0.2,      # ID fields are less significant
                r".*_date$": 0.3,    # Date fields
                r".*revenue.*": 0.8,  # Revenue fields are important
                r".*price.*": 0.7,   # Price fields
                r"^is_.*": 0.6      # Boolean flags
            }),
            
            # Critical fields
            CriticalFieldRule({
                "status",
                "payment_status",
                "subscription_status",
                "churn_risk",
                "contract_end_date"
            })
        ]
    
    def evaluate(self, change: Change) -> float:
        """Evaluate change significance using all rules
        
        Returns:
            Significance score between 0.0 and 1.0
        """
        if not self.rules:
            return 0.5
        
        # Collect all scores
        scores = []
        for rule in self.rules:
            score = rule.evaluate(change)
            if score > 0:  # Only include non-zero scores
                scores.append(score)
        
        if not scores:
            return 0.5
        
        # Use weighted average with bias towards higher scores
        # This ensures critical changes aren't diluted
        scores.sort(reverse=True)
        weights = [1.0 / (i + 1) for i in range(len(scores))]
        total_weight = sum(weights)
        
        weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
        return min(1.0, weighted_sum / total_weight)
    
    def add_rule(self, rule: SignificanceRule):
        """Add a custom rule"""
        self.rules.append(rule)
    
    def remove_rule(self, rule_name: str):
        """Remove a rule by name"""
        self.rules = [r for r in self.rules if r.name != rule_name]