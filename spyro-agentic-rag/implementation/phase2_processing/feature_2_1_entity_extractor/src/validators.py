"""Entity validation functionality"""

import re
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .models import Entity, EntityType, ValidationError, ValidationResult

logger = logging.getLogger(__name__)


class EntityValidator:
    """Validates entities against schema and business rules"""
    
    def __init__(self):
        """Initialize validator with default rules"""
        self.validation_rules = self._get_default_validation_rules()
    
    async def validate_entity(
        self,
        entity: Entity,
        custom_rules: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """Validate an entity
        
        Args:
            entity: Entity to validate
            custom_rules: Optional custom validation rules
            
        Returns:
            ValidationResult with errors and warnings
        """
        errors = []
        warnings = []
        
        # Get validation rules for entity type
        rules = custom_rules or self.validation_rules.get(
            entity.type.value, 
            {}
        )
        
        # Validate required fields
        required_fields = rules.get("required_fields", [])
        for field in required_fields:
            if field not in entity.attributes or entity.attributes[field] is None:
                errors.append(ValidationError(
                    entity_id=entity.id,
                    field=field,
                    error_type="missing_required",
                    message=f"Required field '{field}' is missing",
                    suggested_fix=self._get_default_value(entity.type, field)
                ))
        
        # Validate field types
        field_types = rules.get("field_types", {})
        for field, expected_type in field_types.items():
            if field in entity.attributes:
                value = entity.attributes[field]
                if not self._check_field_type(value, expected_type):
                    errors.append(ValidationError(
                        entity_id=entity.id,
                        field=field,
                        error_type="invalid_type",
                        message=f"Field '{field}' should be {expected_type}",
                        suggested_fix=self._convert_type(value, expected_type)
                    ))
        
        # Validate field formats
        field_formats = rules.get("field_formats", {})
        for field, format_pattern in field_formats.items():
            if field in entity.attributes and entity.attributes[field]:
                value = str(entity.attributes[field])
                if not re.match(format_pattern, value):
                    errors.append(ValidationError(
                        entity_id=entity.id,
                        field=field,
                        error_type="invalid_format",
                        message=f"Field '{field}' has invalid format",
                        suggested_fix=self._fix_format(value, format_pattern)
                    ))
        
        # Validate field ranges
        field_ranges = rules.get("field_ranges", {})
        for field, range_config in field_ranges.items():
            if field in entity.attributes:
                value = entity.attributes[field]
                if isinstance(value, (int, float)):
                    min_val = range_config.get("min")
                    max_val = range_config.get("max")
                    
                    if min_val is not None and value < min_val:
                        warnings.append(ValidationError(
                            entity_id=entity.id,
                            field=field,
                            error_type="out_of_range",
                            message=f"Field '{field}' value {value} is below minimum {min_val}",
                            severity="warning"
                        ))
                    
                    if max_val is not None and value > max_val:
                        warnings.append(ValidationError(
                            entity_id=entity.id,
                            field=field,
                            error_type="out_of_range",
                            message=f"Field '{field}' value {value} exceeds maximum {max_val}",
                            severity="warning"
                        ))
        
        # Business rule validation
        business_errors = await self._validate_business_rules(entity, rules)
        errors.extend(business_errors)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def _get_default_validation_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get default validation rules by entity type"""
        return {
            "Customer": {
                "required_fields": ["id", "name"],
                "field_types": {
                    "id": "string",
                    "name": "string",
                    "arr": "number",
                    "employee_count": "integer",
                    "created_date": "datetime"
                },
                "field_formats": {
                    "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    "website": r"^https?://.*"
                },
                "field_ranges": {
                    "arr": {"min": 0},
                    "employee_count": {"min": 1, "max": 1000000}
                }
            },
            "Product": {
                "required_fields": ["id", "name", "category"],
                "field_types": {
                    "id": "string",
                    "name": "string",
                    "category": "string",
                    "price": "number"
                },
                "field_ranges": {
                    "price": {"min": 0}
                }
            },
            "Subscription": {
                "required_fields": ["id", "customer_id", "product_id"],
                "field_types": {
                    "id": "string",
                    "customer_id": "string",
                    "product_id": "string",
                    "start_date": "datetime",
                    "end_date": "datetime",
                    "value": "number"
                },
                "field_ranges": {
                    "value": {"min": 0}
                }
            },
            "Team": {
                "required_fields": ["id", "name"],
                "field_types": {
                    "id": "string",
                    "name": "string",
                    "size": "integer",
                    "department": "string"
                },
                "field_ranges": {
                    "size": {"min": 1, "max": 1000}
                }
            },
            "Risk": {
                "required_fields": ["id", "title", "severity"],
                "field_types": {
                    "id": "string",
                    "title": "string",
                    "severity": "string",
                    "probability": "number",
                    "impact": "number"
                },
                "field_formats": {
                    "severity": r"^(low|medium|high|critical)$"
                },
                "field_ranges": {
                    "probability": {"min": 0, "max": 1},
                    "impact": {"min": 0, "max": 10}
                }
            }
        }
    
    async def _validate_business_rules(
        self,
        entity: Entity,
        rules: Dict[str, Any]
    ) -> List[ValidationError]:
        """Validate entity against business rules"""
        errors = []
        
        # Customer-specific rules
        if entity.type == EntityType.CUSTOMER:
            # ARR should be positive for active customers
            if entity.attributes.get("status") == "active":
                arr = entity.attributes.get("arr", 0)
                if arr <= 0:
                    errors.append(ValidationError(
                        entity_id=entity.id,
                        field="arr",
                        error_type="business_rule",
                        message="Active customers should have positive ARR"
                    ))
        
        # Subscription-specific rules
        elif entity.type == EntityType.SUBSCRIPTION:
            # End date should be after start date
            start_date = entity.attributes.get("start_date")
            end_date = entity.attributes.get("end_date")
            
            if start_date and end_date:
                try:
                    start = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                    end = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                    
                    if end <= start:
                        errors.append(ValidationError(
                            entity_id=entity.id,
                            field="end_date",
                            error_type="business_rule",
                            message="End date must be after start date"
                        ))
                except:
                    pass
        
        return errors
    
    def _check_field_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected type"""
        if value is None:
            return True  # None is valid for optional fields
        
        type_checks = {
            "string": lambda v: isinstance(v, str),
            "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
            "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
            "boolean": lambda v: isinstance(v, bool),
            "datetime": lambda v: self._is_valid_datetime(v),
            "array": lambda v: isinstance(v, list),
            "object": lambda v: isinstance(v, dict)
        }
        
        check_func = type_checks.get(expected_type)
        return check_func(value) if check_func else True
    
    def _is_valid_datetime(self, value: Any) -> bool:
        """Check if value is a valid datetime"""
        if isinstance(value, datetime):
            return True
        
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True
            except:
                pass
        
        return False
    
    def _convert_type(self, value: Any, target_type: str) -> Any:
        """Convert value to target type"""
        try:
            if target_type == "string":
                return str(value)
            elif target_type == "integer":
                return int(float(str(value).replace(",", "")))
            elif target_type == "number":
                return float(str(value).replace(",", ""))
            elif target_type == "boolean":
                return str(value).lower() in ("true", "1", "yes", "on")
            elif target_type == "datetime":
                # Try to parse common date formats
                return value  # Would need proper date parsing
        except:
            pass
        
        return None
    
    def _fix_format(self, value: str, pattern: str) -> Optional[str]:
        """Attempt to fix format issues"""
        # Email format fix
        if "email" in pattern or "@" in pattern:
            # Basic email cleanup
            cleaned = value.lower().strip()
            cleaned = re.sub(r'\s+', '', cleaned)
            return cleaned if re.match(pattern, cleaned) else None
        
        # URL format fix
        if "http" in pattern:
            if not value.startswith(("http://", "https://")):
                return f"https://{value}"
        
        return None
    
    def _get_default_value(self, entity_type: EntityType, field: str) -> Any:
        """Get default value for a field"""
        defaults = {
            "status": "active",
            "created_date": datetime.now().isoformat(),
            "updated_date": datetime.now().isoformat(),
            "is_active": True,
            "score": 0.0,
            "count": 0
        }
        
        return defaults.get(field)