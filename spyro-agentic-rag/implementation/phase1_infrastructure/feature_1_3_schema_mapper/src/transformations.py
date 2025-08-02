"""Transformation functions library"""

from typing import Any, Dict, List, Optional, Callable, Union
from datetime import datetime, date
import re
import json
from decimal import Decimal


class TransformationLibrary:
    """Library of transformation functions"""
    
    def __init__(self):
        self._transforms = self._register_default_transforms()
        self._custom_transforms = {}
    
    def _register_default_transforms(self) -> Dict[str, Callable]:
        """Register default transformation functions"""
        return {
            "cast": self.cast_type,
            "extract": self.extract_nested,
            "compute": self.compute_value,
            "regex": self.regex_extract,
            "split": self.split_string,
            "join": self.join_array,
            "lookup": self.lookup_value,
            "conditional": self.conditional_value,
            "normalize_date": self.normalize_date,
            "normalize_money": self.normalize_money,
            "normalize_enum": self.normalize_enum,
            "concat": self.concatenate_values,
            "parse_json": self.parse_json_string,
            "to_array": self.to_array,
            "from_array": self.from_array,
            "calculate_arr": self.calculate_arr_from_mrr
        }
    
    def get_transform(self, transform_type: Union[str, 'TransformationType']) -> Optional[Callable]:
        """Get transformation function by type"""
        transform_name = str(transform_type).split('.')[-1].lower()
        return self._transforms.get(transform_name) or self._custom_transforms.get(transform_name)
    
    def register_custom_transform(self, name: str, func: Callable):
        """Register a custom transformation function"""
        self._custom_transforms[name] = func
    
    # Core transformation functions
    
    @staticmethod
    def cast_type(value: Any, to_type: str, default: Any = None) -> Any:
        """Cast value to specified type"""
        if value is None:
            return default
        
        try:
            if to_type == "string":
                return str(value)
            elif to_type == "integer":
                # Handle money values (remove $ and ,)
                if isinstance(value, str):
                    value = value.replace('$', '').replace(',', '')
                return int(float(value))
            elif to_type == "float":
                if isinstance(value, str):
                    value = value.replace('$', '').replace(',', '')
                return float(value)
            elif to_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ('true', 'yes', '1', 'on')
                return bool(value)
            elif to_type == "date":
                return TransformationLibrary.normalize_date(value)
            elif to_type == "array":
                return TransformationLibrary.to_array(value)
            else:
                return value
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def extract_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
        """Extract value from nested structure using dot notation"""
        parts = path.split('.')
        value = data
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            elif isinstance(value, list) and part.isdigit():
                idx = int(part)
                if 0 <= idx < len(value):
                    value = value[idx]
                else:
                    return default
            else:
                return default
        
        return value
    
    @staticmethod
    def compute_value(values: Any, expression: str, **kwargs) -> Any:
        """Compute value from multiple fields using expression"""
        # Handle single value input (not a dict)
        if not isinstance(values, dict):
            # If expression is just the field name, return the value
            if expression == "company_name" or expression in str(values):
                return values
            return values
        
        # Simple expression evaluation (can be enhanced with safe eval)
        local_vars = {**values, **kwargs}
        
        # Basic arithmetic operations
        if "+" in expression:
            parts = expression.split("+")
            # Try numeric addition first
            try:
                total = 0
                for part in parts:
                    part = part.strip()
                    if part in local_vars:
                        total += float(local_vars[part] or 0)
                return total
            except (ValueError, TypeError):
                # Fall back to string concatenation
                return "".join(str(local_vars.get(p.strip(), "")) for p in parts)
        elif "*" in expression:
            parts = expression.split("*")
            result = 1
            for part in parts:
                part = part.strip()
                if part in local_vars:
                    result *= float(local_vars[part] or 0)
            return result
        
        # Direct field reference
        if expression in local_vars:
            return local_vars[expression]
        
        return None
    
    @staticmethod
    def regex_extract(value: str, pattern: str, group: int = 0, default: str = "") -> str:
        """Extract value using regex pattern"""
        if not isinstance(value, str):
            return default
        
        match = re.search(pattern, value)
        if match:
            try:
                return match.group(group)
            except IndexError:
                return default
        return default
    
    @staticmethod
    def split_string(value: str, separator: str = ",", max_split: int = -1) -> List[str]:
        """Split string into array"""
        if not isinstance(value, str):
            return []
        
        parts = value.split(separator, max_split)
        return [part.strip() for part in parts if part.strip()]
    
    @staticmethod
    def join_array(value: List[Any], separator: str = ", ") -> str:
        """Join array into string"""
        if not isinstance(value, list):
            return str(value)
        
        return separator.join(str(item) for item in value)
    
    @staticmethod
    def lookup_value(value: Any, lookup_table: Dict[str, Any], default: Any = None) -> Any:
        """Lookup value in mapping table"""
        return lookup_table.get(str(value), default)
    
    @staticmethod
    def conditional_value(values: Dict[str, Any], conditions: List[Dict[str, Any]]) -> Any:
        """Apply conditional logic to determine value"""
        for condition in conditions:
            field = condition.get("field")
            operator = condition.get("operator", "==")
            test_value = condition.get("value")
            result = condition.get("result")
            
            if field not in values:
                continue
            
            field_value = values[field]
            
            # Evaluate condition
            if operator == "==" and field_value == test_value:
                return result
            elif operator == "!=" and field_value != test_value:
                return result
            elif operator == ">" and field_value > test_value:
                return result
            elif operator == "<" and field_value < test_value:
                return result
            elif operator == ">=" and field_value >= test_value:
                return result
            elif operator == "<=" and field_value <= test_value:
                return result
            elif operator == "contains" and test_value in str(field_value):
                return result
            elif operator == "matches" and re.match(test_value, str(field_value)):
                return result
        
        # Return default if specified
        return conditions[-1].get("default") if conditions else None
    
    @staticmethod
    def normalize_date(value: Any, format: Optional[str] = None) -> Optional[str]:
        """Normalize date to ISO format"""
        if value is None:
            return None
        
        if isinstance(value, datetime):
            return value.date().isoformat()
        elif isinstance(value, date):
            return value.isoformat()
        
        if isinstance(value, str):
            # Try common date formats
            formats = [format] if format else [
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d",
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(value, fmt)
                    return dt.date().isoformat()
                except ValueError:
                    continue
        
        return None
    
    @staticmethod
    def normalize_money(value: Any, currency: str = "USD", to_cents: bool = True) -> Optional[int]:
        """Normalize money values to cents"""
        if value is None:
            return None
        
        # Convert to float first
        if isinstance(value, str):
            # Remove currency symbols and commas
            value = re.sub(r'[^\d.-]', '', value)
        
        try:
            amount = float(value)
            if to_cents:
                return int(amount * 100)
            return int(amount)
        except (ValueError, TypeError):
            return None
    
    @staticmethod
    def normalize_enum(value: Any, mapping: Dict[str, str], default: Optional[str] = None) -> Optional[str]:
        """Normalize enum values"""
        if value is None:
            return default
        
        value_str = str(value).lower().strip()
        
        # Direct mapping
        if value_str in mapping:
            return mapping[value_str]
        
        # Try to find partial match
        for key, mapped_value in mapping.items():
            if key in value_str or value_str in key:
                return mapped_value
        
        return default
    
    @staticmethod
    def concatenate_values(values: Dict[str, Any], fields: List[str], 
                          separator: str = " ", skip_empty: bool = True) -> str:
        """Concatenate multiple field values"""
        parts = []
        
        for field in fields:
            value = values.get(field)
            if value is not None and (not skip_empty or value != ""):
                parts.append(str(value))
        
        return separator.join(parts)
    
    @staticmethod
    def parse_json_string(value: str, default: Any = None) -> Any:
        """Parse JSON string"""
        if not isinstance(value, str):
            return value
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    
    @staticmethod
    def to_array(value: Any, separator: Optional[str] = None) -> List[Any]:
        """Convert value to array"""
        if isinstance(value, list):
            return value
        elif isinstance(value, str) and separator:
            return TransformationLibrary.split_string(value, separator)
        elif value is None:
            return []
        else:
            return [value]
    
    @staticmethod
    def from_array(value: List[Any], index: int = 0, default: Any = None) -> Any:
        """Extract single value from array"""
        if not isinstance(value, list):
            return value
        
        if 0 <= index < len(value):
            return value[index]
        return default
    
    @staticmethod
    def calculate_arr_from_mrr(values: Dict[str, Any], mrr_field: str = "mrr") -> Optional[int]:
        """Calculate ARR from MRR"""
        mrr = values.get(mrr_field)
        if mrr is None:
            return None
        
        try:
            return int(float(mrr) * 12)
        except (ValueError, TypeError):
            return None


# Size mapping for customer segmentation
CUSTOMER_SIZE_MAPPING = {
    "small": "SMB",
    "smb": "SMB",
    "startup": "SMB",
    "medium": "Mid-Market",
    "mid": "Mid-Market",
    "midmarket": "Mid-Market",
    "large": "Enterprise",
    "enterprise": "Enterprise",
    "strategic": "Enterprise"
}

# Status mapping for subscriptions
SUBSCRIPTION_STATUS_MAPPING = {
    "active": "active",
    "live": "active",
    "enabled": "active",
    "pending": "pending_renewal",
    "renewal": "pending_renewal",
    "cancelled": "churned",
    "expired": "churned",
    "terminated": "churned",
    "suspended": "paused",
    "hold": "paused"
}