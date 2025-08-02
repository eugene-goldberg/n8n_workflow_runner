"""SpyroSolutions entity model definitions"""

from dataclasses import dataclass
from typing import Type, Any, Optional, List, Dict
from enum import Enum
from datetime import datetime


class FieldType(Enum):
    """Supported field types"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    ARRAY = "array"
    OBJECT = "object"
    ENUM = "enum"


@dataclass
class EntityField:
    """Definition of an entity field"""
    name: str
    field_type: FieldType
    required: bool = True
    description: str = ""
    default: Any = None
    enum_values: Optional[List[str]] = None
    array_type: Optional[FieldType] = None
    
    def validate_value(self, value: Any) -> bool:
        """Validate a value against this field definition"""
        if value is None:
            return not self.required
        
        if self.field_type == FieldType.STRING:
            return isinstance(value, str)
        elif self.field_type == FieldType.INTEGER:
            return isinstance(value, int)
        elif self.field_type == FieldType.FLOAT:
            return isinstance(value, (int, float))
        elif self.field_type == FieldType.BOOLEAN:
            return isinstance(value, bool)
        elif self.field_type == FieldType.DATE:
            return isinstance(value, (str, datetime))
        elif self.field_type == FieldType.DATETIME:
            return isinstance(value, (str, datetime))
        elif self.field_type == FieldType.ARRAY:
            return isinstance(value, list)
        elif self.field_type == FieldType.OBJECT:
            return isinstance(value, dict)
        elif self.field_type == FieldType.ENUM:
            return value in (self.enum_values or [])
        
        return False


# SpyroSolutions Entity Definitions
SPYRO_ENTITIES = {
    "Customer": {
        "id": EntityField("id", FieldType.STRING, required=True, description="Unique customer identifier"),
        "name": EntityField("name", FieldType.STRING, required=True, description="Customer company name"),
        "size": EntityField("size", FieldType.ENUM, required=True, 
                           enum_values=["SMB", "Mid-Market", "Enterprise"],
                           description="Customer size segment"),
        "industry": EntityField("industry", FieldType.STRING, required=True, description="Industry vertical"),
        "arr": EntityField("arr", FieldType.INTEGER, required=True, description="Annual Recurring Revenue"),
        "employee_count": EntityField("employee_count", FieldType.INTEGER, required=False, 
                                     description="Number of employees"),
        "created_date": EntityField("created_date", FieldType.DATE, required=True, 
                                   description="Customer creation date"),
        "updated_date": EntityField("updated_date", FieldType.DATE, required=True, 
                                   description="Last update date"),
        "health_score": EntityField("health_score", FieldType.INTEGER, required=False,
                                   description="Customer health score (0-100)"),
        "churn_risk": EntityField("churn_risk", FieldType.ENUM, required=False,
                                 enum_values=["low", "medium", "high"],
                                 description="Churn risk level"),
        "region": EntityField("region", FieldType.STRING, required=False, description="Geographic region"),
        "website": EntityField("website", FieldType.STRING, required=False, description="Company website"),
        "contact_email": EntityField("contact_email", FieldType.STRING, required=False, 
                                    description="Primary contact email"),
        "account_manager": EntityField("account_manager", FieldType.STRING, required=False,
                                      description="Assigned account manager")
    },
    
    "Product": {
        "id": EntityField("id", FieldType.STRING, required=True, description="Unique product identifier"),
        "name": EntityField("name", FieldType.STRING, required=True, description="Product name"),
        "category": EntityField("category", FieldType.STRING, required=True, description="Product category"),
        "description": EntityField("description", FieldType.STRING, required=False, 
                                  description="Product description"),
        "features": EntityField("features", FieldType.ARRAY, required=False, 
                               array_type=FieldType.STRING,
                               description="List of product features"),
        "version": EntityField("version", FieldType.STRING, required=False, description="Product version"),
        "release_date": EntityField("release_date", FieldType.DATE, required=False, 
                                   description="Product release date"),
        "status": EntityField("status", FieldType.ENUM, required=True,
                             enum_values=["active", "beta", "deprecated"],
                             description="Product status"),
        "pricing_model": EntityField("pricing_model", FieldType.ENUM, required=False,
                                    enum_values=["subscription", "usage-based", "tiered"],
                                    description="Pricing model"),
        "base_price": EntityField("base_price", FieldType.INTEGER, required=False,
                                 description="Base price in cents")
    },
    
    "Subscription": {
        "id": EntityField("id", FieldType.STRING, required=True, description="Unique subscription identifier"),
        "customer_id": EntityField("customer_id", FieldType.STRING, required=True, 
                                  description="Reference to Customer"),
        "product_id": EntityField("product_id", FieldType.STRING, required=True, 
                                 description="Reference to Product"),
        "mrr": EntityField("mrr", FieldType.INTEGER, required=True, 
                          description="Monthly Recurring Revenue in cents"),
        "arr": EntityField("arr", FieldType.INTEGER, required=True, 
                          description="Annual Recurring Revenue in cents"),
        "start_date": EntityField("start_date", FieldType.DATE, required=True, 
                                 description="Subscription start date"),
        "end_date": EntityField("end_date", FieldType.DATE, required=False, 
                               description="Subscription end date"),
        "status": EntityField("status", FieldType.ENUM, required=True,
                             enum_values=["active", "pending_renewal", "churned", "paused"],
                             description="Subscription status"),
        "payment_method": EntityField("payment_method", FieldType.ENUM, required=False,
                                     enum_values=["credit_card", "invoice", "wire_transfer"],
                                     description="Payment method"),
        "billing_cycle": EntityField("billing_cycle", FieldType.ENUM, required=False,
                                    enum_values=["monthly", "quarterly", "annual"],
                                    description="Billing cycle"),
        "discount_percentage": EntityField("discount_percentage", FieldType.INTEGER, required=False,
                                          description="Discount percentage (0-100)"),
        "seats": EntityField("seats", FieldType.INTEGER, required=False,
                            description="Number of licensed seats"),
        "usage_limit": EntityField("usage_limit", FieldType.INTEGER, required=False,
                                  description="Usage limit for the subscription")
    },
    
    "Team": {
        "id": EntityField("id", FieldType.STRING, required=True, description="Unique team identifier"),
        "name": EntityField("name", FieldType.STRING, required=True, description="Team name"),
        "size": EntityField("size", FieldType.INTEGER, required=True, description="Number of team members"),
        "focus_area": EntityField("focus_area", FieldType.STRING, required=True, 
                                 description="Primary focus area"),
        "manager": EntityField("manager", FieldType.STRING, required=True, description="Team manager name"),
        "created_date": EntityField("created_date", FieldType.DATE, required=False, 
                                   description="Team creation date"),
        "velocity": EntityField("velocity", FieldType.INTEGER, required=False,
                               description="Team velocity metric"),
        "capacity": EntityField("capacity", FieldType.INTEGER, required=False,
                               description="Team capacity"),
        "utilization": EntityField("utilization", FieldType.FLOAT, required=False,
                                  description="Team utilization percentage"),
        "location": EntityField("location", FieldType.STRING, required=False,
                               description="Team location"),
        "supported_products": EntityField("supported_products", FieldType.ARRAY, required=False,
                                         array_type=FieldType.STRING,
                                         description="List of supported product IDs")
    },
    
    "Project": {
        "id": EntityField("id", FieldType.STRING, required=True, description="Unique project identifier"),
        "name": EntityField("name", FieldType.STRING, required=True, description="Project name"),
        "description": EntityField("description", FieldType.STRING, required=False, 
                                  description="Project description"),
        "type": EntityField("type", FieldType.ENUM, required=True,
                           enum_values=["feature", "infrastructure", "security", "performance", "migration"],
                           description="Project type"),
        "status": EntityField("status", FieldType.ENUM, required=True,
                             enum_values=["planning", "active", "completed", "on_hold", "cancelled"],
                             description="Project status"),
        "team_id": EntityField("team_id", FieldType.STRING, required=True, 
                              description="Reference to Team"),
        "customer_id": EntityField("customer_id", FieldType.STRING, required=False,
                                  description="Reference to Customer (if applicable)"),
        "start_date": EntityField("start_date", FieldType.DATE, required=True, 
                                 description="Project start date"),
        "end_date": EntityField("end_date", FieldType.DATE, required=False, 
                               description="Project end date"),
        "budget": EntityField("budget", FieldType.INTEGER, required=False,
                             description="Project budget in cents"),
        "completion_percentage": EntityField("completion_percentage", FieldType.INTEGER, required=False,
                                           description="Completion percentage (0-100)"),
        "priority": EntityField("priority", FieldType.ENUM, required=False,
                               enum_values=["low", "medium", "high", "critical"],
                               description="Project priority"),
        "stakeholders": EntityField("stakeholders", FieldType.ARRAY, required=False,
                                   array_type=FieldType.STRING,
                                   description="List of stakeholder names")
    }
}


def get_entity_fields(entity_name: str) -> Dict[str, EntityField]:
    """Get field definitions for an entity"""
    return SPYRO_ENTITIES.get(entity_name, {})


def get_required_fields(entity_name: str) -> List[str]:
    """Get list of required fields for an entity"""
    fields = get_entity_fields(entity_name)
    return [name for name, field in fields.items() if field.required]


def validate_entity_data(entity_name: str, data: Dict[str, Any]) -> List[str]:
    """Validate data against entity schema, return list of errors"""
    errors = []
    fields = get_entity_fields(entity_name)
    
    if not fields:
        errors.append(f"Unknown entity type: {entity_name}")
        return errors
    
    # Check required fields
    for field_name, field_def in fields.items():
        if field_def.required and field_name not in data:
            errors.append(f"Missing required field: {field_name}")
        elif field_name in data:
            if not field_def.validate_value(data[field_name]):
                errors.append(f"Invalid value for field {field_name}: {data[field_name]}")
    
    # Check for unknown fields
    for field_name in data:
        if field_name not in fields:
            errors.append(f"Unknown field: {field_name}")
    
    return errors