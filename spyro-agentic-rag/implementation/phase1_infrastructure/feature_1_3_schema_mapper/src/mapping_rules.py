"""Mapping rule definitions and management"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
import re


class TransformationType(Enum):
    """Types of transformations available"""
    DIRECT = "direct"  # Direct copy
    RENAME = "rename"  # Simple field rename
    CAST = "cast"  # Type casting
    EXTRACT = "extract"  # Extract from nested structure
    COMPUTE = "compute"  # Compute from multiple fields
    CONSTANT = "constant"  # Use constant value
    REGEX = "regex"  # Regex extraction
    SPLIT = "split"  # Split string into array
    JOIN = "join"  # Join array into string
    LOOKUP = "lookup"  # Lookup table transformation
    CONDITIONAL = "conditional"  # Conditional mapping


@dataclass
class MappingRule:
    """Defines how to map a source field to target entity field"""
    source_field: Union[str, List[str]]  # Source field(s) path
    target_entity: str  # Target entity name
    target_field: str  # Target field name
    transformation: TransformationType = TransformationType.DIRECT
    transform_params: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0  # Confidence score (0-1)
    description: str = ""
    
    def apply(self, source_data: Dict[str, Any], 
              transform_lib: Optional['TransformationLibrary'] = None) -> Any:
        """Apply this mapping rule to source data"""
        # Extract source value(s)
        if isinstance(self.source_field, list):
            # Multiple source fields
            source_values = {}
            for field in self.source_field:
                value = self._extract_value(source_data, field)
                source_values[field] = value
        else:
            # Single source field
            source_values = self._extract_value(source_data, self.source_field)
        
        # Apply transformation
        if self.transformation == TransformationType.DIRECT:
            return source_values
        elif self.transformation == TransformationType.RENAME:
            return source_values
        elif self.transformation == TransformationType.CONSTANT:
            return self.transform_params.get("value")
        elif self.transformation == TransformationType.EXTRACT:
            # For extract, source_values is already the extracted value
            return source_values
        elif transform_lib:
            transform_fn = transform_lib.get_transform(self.transformation)
            if transform_fn:
                return transform_fn(source_values, **self.transform_params)
        
        return source_values
    
    def _extract_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Extract value from nested structure using dot notation"""
        parts = field_path.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(value):
                    value = value[idx]
                else:
                    return None
            else:
                return None
        
        return value


@dataclass 
class MappingRuleSet:
    """Collection of mapping rules for a source schema"""
    name: str
    description: str = ""
    rules: List[MappingRule] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_rule(self, rule: MappingRule):
        """Add a mapping rule"""
        self.rules.append(rule)
    
    def get_rules_for_entity(self, entity_name: str) -> List[MappingRule]:
        """Get all rules that map to a specific entity"""
        return [r for r in self.rules if r.target_entity == entity_name]
    
    def get_rule_by_source(self, source_field: str) -> Optional[MappingRule]:
        """Get rule for a specific source field"""
        for rule in self.rules:
            if isinstance(rule.source_field, str) and rule.source_field == source_field:
                return rule
            elif isinstance(rule.source_field, list) and source_field in rule.source_field:
                return rule
        return None
    
    def validate(self, source_schema: Dict[str, Any]) -> List[str]:
        """Validate rules against source schema"""
        errors = []
        
        for rule in self.rules:
            # Check if source fields exist
            if isinstance(rule.source_field, str):
                if not self._field_exists(source_schema, rule.source_field):
                    errors.append(f"Source field not found: {rule.source_field}")
            else:
                for field in rule.source_field:
                    if not self._field_exists(source_schema, field):
                        errors.append(f"Source field not found: {field}")
        
        return errors
    
    def _field_exists(self, schema: Dict[str, Any], field_path: str) -> bool:
        """Check if field exists in schema"""
        # Simple implementation - can be enhanced for complex schemas
        return field_path in schema or '.' in field_path


class CommonPatterns:
    """Common field mapping patterns"""
    
    # Common field name variations
    CUSTOMER_ID_PATTERNS = [
        r"customer[_-]?id",
        r"client[_-]?id", 
        r"account[_-]?id",
        r"company[_-]?id",
        r"org[_-]?id"
    ]
    
    DATE_PATTERNS = [
        r".*[_-]?date$",
        r".*[_-]?at$",
        r".*[_-]?time$",
        r"created",
        r"updated",
        r"modified"
    ]
    
    MONEY_PATTERNS = [
        r".*revenue.*",
        r".*price.*",
        r".*cost.*",
        r".*amount.*",
        r".*fee.*",
        r"mrr",
        r"arr"
    ]
    
    @classmethod
    def detect_field_type(cls, field_name: str) -> Optional[str]:
        """Detect likely field type from name"""
        field_lower = field_name.lower()
        
        # Check customer ID patterns
        for pattern in cls.CUSTOMER_ID_PATTERNS:
            if re.match(pattern, field_lower):
                return "customer_id"
        
        # Check date patterns
        for pattern in cls.DATE_PATTERNS:
            if re.match(pattern, field_lower):
                return "date"
        
        # Check money patterns
        for pattern in cls.MONEY_PATTERNS:
            if re.match(pattern, field_lower):
                return "money"
        
        # Check other common patterns
        if "email" in field_lower:
            return "email"
        elif "phone" in field_lower:
            return "phone"
        elif "url" in field_lower or "website" in field_lower:
            return "url"
        elif "count" in field_lower or "number" in field_lower:
            return "integer"
        elif "percent" in field_lower or "rate" in field_lower:
            return "percentage"
        elif "status" in field_lower or "state" in field_lower:
            return "enum"
        
        return None


def create_default_rules() -> Dict[str, MappingRuleSet]:
    """Create default mapping rules for common schemas"""
    rules = {}
    
    # Salesforce-style mapping
    salesforce_rules = MappingRuleSet(
        name="salesforce",
        description="Default mappings for Salesforce-style schemas"
    )
    
    salesforce_rules.add_rule(MappingRule(
        source_field="AccountId",
        target_entity="Customer",
        target_field="id",
        transformation=TransformationType.RENAME
    ))
    
    salesforce_rules.add_rule(MappingRule(
        source_field="Name",
        target_entity="Customer", 
        target_field="name",
        transformation=TransformationType.RENAME
    ))
    
    salesforce_rules.add_rule(MappingRule(
        source_field="AnnualRevenue",
        target_entity="Customer",
        target_field="arr",
        transformation=TransformationType.CAST,
        transform_params={"to_type": "integer"}
    ))
    
    rules["salesforce"] = salesforce_rules
    
    # HubSpot-style mapping
    hubspot_rules = MappingRuleSet(
        name="hubspot",
        description="Default mappings for HubSpot-style schemas"
    )
    
    hubspot_rules.add_rule(MappingRule(
        source_field="properties.hs_object_id",
        target_entity="Customer",
        target_field="id",
        transformation=TransformationType.EXTRACT
    ))
    
    hubspot_rules.add_rule(MappingRule(
        source_field="properties.name",
        target_entity="Customer",
        target_field="name",
        transformation=TransformationType.EXTRACT
    ))
    
    rules["hubspot"] = hubspot_rules
    
    return rules