"""Main schema mapper implementation"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import asyncio

from .entity_models import SPYRO_ENTITIES, validate_entity_data, get_required_fields
from .mapping_rules import (
    MappingRule, MappingRuleSet, TransformationType, 
    CommonPatterns, create_default_rules
)
from .transformations import TransformationLibrary, CUSTOMER_SIZE_MAPPING, SUBSCRIPTION_STATUS_MAPPING
from .llm_mapper import LLMMapper


logger = logging.getLogger(__name__)


@dataclass
class MappingResult:
    """Result of applying schema mapping"""
    entities: Dict[str, List[Dict[str, Any]]] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    unmapped_fields: List[str] = field(default_factory=list)
    statistics: Dict[str, Any] = field(default_factory=dict)


class SchemaMapper:
    """Maps external schemas to SpyroSolutions entities"""
    
    def __init__(self, llm_enabled: bool = True):
        """Initialize schema mapper
        
        Args:
            llm_enabled: Whether to use LLM for auto-mapping
        """
        self.transform_lib = TransformationLibrary()
        self.default_rules = create_default_rules()
        self.custom_rules = {}
        self.llm_mapper = LLMMapper() if llm_enabled else None
        
        # Register common transformations
        self._register_common_transforms()
    
    def _register_common_transforms(self):
        """Register common custom transformations"""
        # Customer size normalization
        self.transform_lib.register_custom_transform(
            "normalize_customer_size",
            lambda value: CUSTOMER_SIZE_MAPPING.get(str(value).lower(), value)
        )
        
        # Subscription status normalization
        self.transform_lib.register_custom_transform(
            "normalize_subscription_status",
            lambda value: SUBSCRIPTION_STATUS_MAPPING.get(str(value).lower(), value)
        )
    
    async def auto_map_schema(
        self, 
        source_schema: Dict[str, Any],
        sample_data: Optional[List[Dict[str, Any]]] = None,
        target_entities: Optional[List[str]] = None,
        confidence_threshold: float = 0.7
    ) -> MappingRuleSet:
        """Automatically map source schema to target entities
        
        Args:
            source_schema: Source data schema
            sample_data: Sample records for better mapping
            target_entities: List of target entities to map to
            confidence_threshold: Minimum confidence for auto-mapping
            
        Returns:
            Generated mapping rule set
        """
        if target_entities is None:
            target_entities = list(SPYRO_ENTITIES.keys())
        
        rule_set = MappingRuleSet(
            name="auto_generated",
            description="Auto-generated mapping rules"
        )
        
        # First try rule-based mapping
        rule_based_mappings = self._generate_rule_based_mappings(
            source_schema, target_entities, sample_data
        )
        
        for mapping in rule_based_mappings:
            if mapping.confidence >= confidence_threshold:
                rule_set.add_rule(mapping)
        
        # Then use LLM for remaining fields if enabled
        if self.llm_mapper:
            mapped_source_fields = {
                rule.source_field for rule in rule_set.rules 
                if isinstance(rule.source_field, str)
            }
            
            unmapped_fields = [
                field for field in source_schema 
                if field not in mapped_source_fields
            ]
            
            if unmapped_fields:
                llm_mappings = await self.llm_mapper.generate_mappings(
                    {field: source_schema[field] for field in unmapped_fields},
                    target_entities,
                    sample_data
                )
                
                for mapping in llm_mappings:
                    if mapping.confidence >= confidence_threshold:
                        rule_set.add_rule(mapping)
        
        return rule_set
    
    def _generate_rule_based_mappings(
        self,
        source_schema: Dict[str, Any],
        target_entities: List[str],
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[MappingRule]:
        """Generate mappings using rule-based patterns"""
        mappings = []
        
        for source_field, field_info in source_schema.items():
            # Try exact match
            for entity_name in target_entities:
                entity_fields = SPYRO_ENTITIES.get(entity_name, {})
                
                # Exact field name match
                if source_field in entity_fields:
                    mappings.append(MappingRule(
                        source_field=source_field,
                        target_entity=entity_name,
                        target_field=source_field,
                        transformation=TransformationType.DIRECT,
                        confidence=1.0,
                        description="Exact field name match"
                    ))
                    break
                
                # Check for common name variations
                source_lower = source_field.lower()
                for target_field, field_def in entity_fields.items():
                    target_lower = target_field.lower()
                    
                    # Common variations
                    if (source_lower == "company_name" and target_field == "name" and 
                        entity_name == "Customer"):
                        mappings.append(MappingRule(
                            source_field=source_field,
                            target_entity=entity_name,
                            target_field=target_field,
                            transformation=TransformationType.RENAME,
                            confidence=0.95,
                            description="Common name variation"
                        ))
                        break
                    elif (source_lower == "annual_revenue" and target_field == "arr" and
                          entity_name == "Customer"):
                        mappings.append(MappingRule(
                            source_field=source_field,
                            target_entity=entity_name,
                            target_field=target_field,
                            transformation=TransformationType.CAST,
                            transform_params={"to_type": "integer"},
                            confidence=0.9,
                            description="Revenue field mapping"
                        ))
                        break
                    elif (source_lower == "industry_vertical" and target_field == "industry" and
                          entity_name == "Customer"):
                        mappings.append(MappingRule(
                            source_field=source_field,
                            target_entity=entity_name,
                            target_field=target_field,
                            transformation=TransformationType.RENAME,
                            confidence=0.85,
                            description="Industry field mapping"
                        ))
                        break
                
                # Try common patterns
                field_type = CommonPatterns.detect_field_type(source_field)
                
                if field_type == "customer_id" and entity_name != "Customer":
                    # Map to customer_id reference field
                    if "customer_id" in entity_fields:
                        mappings.append(MappingRule(
                            source_field=source_field,
                            target_entity=entity_name,
                            target_field="customer_id",
                            transformation=TransformationType.RENAME,
                            confidence=0.9,
                            description="Customer ID pattern match"
                        ))
                
                elif field_type == "date":
                    # Find date fields in target entity
                    for target_field, field_def in entity_fields.items():
                        if "date" in target_field.lower():
                            mappings.append(MappingRule(
                                source_field=source_field,
                                target_entity=entity_name,
                                target_field=target_field,
                                transformation=TransformationType.CAST,
                                transform_params={"to_type": "date"},
                                confidence=0.8,
                                description="Date field pattern match"
                            ))
                            break
                
                elif field_type == "money":
                    # Map to money fields (arr, mrr, etc.)
                    money_fields = ["arr", "mrr", "price", "budget", "revenue"]
                    for target_field in money_fields:
                        if target_field in entity_fields:
                            mappings.append(MappingRule(
                                source_field=source_field,
                                target_entity=entity_name,
                                target_field=target_field,
                                transformation=TransformationType.CAST,
                                transform_params={"to_type": "integer"},
                                confidence=0.85,
                                description="Money field pattern match"
                            ))
                            break
        
        return mappings
    
    def apply_mapping(
        self,
        source_data: Dict[str, Any],
        mapping_rules: MappingRuleSet
    ) -> MappingResult:
        """Apply mapping rules to source data
        
        Args:
            source_data: Source data record
            mapping_rules: Mapping rules to apply
            
        Returns:
            Mapping result with transformed entities
        """
        result = MappingResult()
        mapped_fields = set()
        
        # Group rules by target entity
        entity_rules = {}
        for rule in mapping_rules.rules:
            if rule.target_entity not in entity_rules:
                entity_rules[rule.target_entity] = []
            entity_rules[rule.target_entity].append(rule)
        
        # Apply rules for each entity
        for entity_name, rules in entity_rules.items():
            entity_data = {}
            
            for rule in rules:
                try:
                    value = rule.apply(source_data, self.transform_lib)
                    if value is not None:
                        entity_data[rule.target_field] = value
                        
                        # Track mapped fields
                        if isinstance(rule.source_field, str):
                            mapped_fields.add(rule.source_field)
                        else:
                            mapped_fields.update(rule.source_field)
                
                except Exception as e:
                    result.errors.append(
                        f"Error applying rule for {rule.source_field} -> "
                        f"{entity_name}.{rule.target_field}: {str(e)}"
                    )
            
            # Validate entity data
            validation_errors = validate_entity_data(entity_name, entity_data)
            
            if validation_errors:
                result.warnings.extend([
                    f"{entity_name}: {error}" for error in validation_errors
                ])
            
            # Only add entity if it has required fields
            required_fields = get_required_fields(entity_name)
            if all(field in entity_data for field in required_fields):
                if entity_name not in result.entities:
                    result.entities[entity_name] = []
                result.entities[entity_name].append(entity_data)
            else:
                missing = [f for f in required_fields if f not in entity_data]
                result.warnings.append(
                    f"Skipping {entity_name}: missing required fields {missing}"
                )
        
        # Track unmapped fields
        result.unmapped_fields = [
            field for field in source_data
            if field not in mapped_fields
        ]
        
        # Calculate statistics
        result.statistics = {
            "total_source_fields": len(source_data),
            "mapped_fields": len(mapped_fields),
            "unmapped_fields": len(result.unmapped_fields),
            "entities_created": {
                name: len(records) 
                for name, records in result.entities.items()
            }
        }
        
        return result
    
    def apply_mapping_batch(
        self,
        source_records: List[Dict[str, Any]],
        mapping_rules: MappingRuleSet,
        continue_on_error: bool = True
    ) -> MappingResult:
        """Apply mapping rules to multiple records
        
        Args:
            source_records: List of source data records
            mapping_rules: Mapping rules to apply
            continue_on_error: Whether to continue on mapping errors
            
        Returns:
            Combined mapping result
        """
        combined_result = MappingResult()
        
        for idx, record in enumerate(source_records):
            try:
                record_result = self.apply_mapping(record, mapping_rules)
                
                # Merge results
                for entity_name, entities in record_result.entities.items():
                    if entity_name not in combined_result.entities:
                        combined_result.entities[entity_name] = []
                    combined_result.entities[entity_name].extend(entities)
                
                combined_result.errors.extend([
                    f"Record {idx}: {error}" for error in record_result.errors
                ])
                combined_result.warnings.extend([
                    f"Record {idx}: {warning}" for warning in record_result.warnings
                ])
                
                # Update unmapped fields (union of all)
                combined_result.unmapped_fields = list(
                    set(combined_result.unmapped_fields) | 
                    set(record_result.unmapped_fields)
                )
                
            except Exception as e:
                error_msg = f"Failed to map record {idx}: {str(e)}"
                combined_result.errors.append(error_msg)
                if not continue_on_error:
                    raise Exception(error_msg)
        
        # Update statistics
        combined_result.statistics = {
            "total_records": len(source_records),
            "successful_records": len(source_records) - len(combined_result.errors),
            "total_entities_created": {
                name: len(records)
                for name, records in combined_result.entities.items()
            },
            "unmapped_fields_count": len(combined_result.unmapped_fields)
        }
        
        return combined_result
    
    def save_mapping_rules(
        self,
        rule_set: MappingRuleSet,
        filepath: str
    ):
        """Save mapping rules to file"""
        data = {
            "name": rule_set.name,
            "description": rule_set.description,
            "metadata": rule_set.metadata,
            "rules": [
                {
                    "source_field": rule.source_field,
                    "target_entity": rule.target_entity,
                    "target_field": rule.target_field,
                    "transformation": rule.transformation.value,
                    "transform_params": rule.transform_params,
                    "confidence": rule.confidence,
                    "description": rule.description
                }
                for rule in rule_set.rules
            ]
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_mapping_rules(self, filepath: str) -> MappingRuleSet:
        """Load mapping rules from file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        rule_set = MappingRuleSet(
            name=data["name"],
            description=data.get("description", ""),
            metadata=data.get("metadata", {})
        )
        
        for rule_data in data["rules"]:
            rule = MappingRule(
                source_field=rule_data["source_field"],
                target_entity=rule_data["target_entity"],
                target_field=rule_data["target_field"],
                transformation=TransformationType(rule_data["transformation"]),
                transform_params=rule_data.get("transform_params", {}),
                confidence=rule_data.get("confidence", 1.0),
                description=rule_data.get("description", "")
            )
            rule_set.add_rule(rule)
        
        return rule_set
    
    def validate_mapping(
        self,
        source_schema: Dict[str, Any],
        mapping_rules: MappingRuleSet,
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Validate mapping rules against source schema
        
        Returns:
            Validation report with issues and recommendations
        """
        report = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "coverage": {},
            "recommendations": []
        }
        
        # Check if all source fields in rules exist
        schema_errors = mapping_rules.validate(source_schema)
        report["errors"].extend(schema_errors)
        
        # Check coverage of required target fields
        for entity_name, fields in SPYRO_ENTITIES.items():
            required_fields = get_required_fields(entity_name)
            mapped_fields = set()
            
            for rule in mapping_rules.get_rules_for_entity(entity_name):
                mapped_fields.add(rule.target_field)
            
            missing_required = set(required_fields) - mapped_fields
            
            if missing_required:
                report["warnings"].append(
                    f"{entity_name}: Missing mappings for required fields: {missing_required}"
                )
            
            report["coverage"][entity_name] = {
                "required_fields": len(required_fields),
                "mapped_required": len(set(required_fields) & mapped_fields),
                "total_fields": len(fields),
                "mapped_total": len(mapped_fields)
            }
        
        # Test with sample data if provided
        if sample_data:
            test_result = self.apply_mapping_batch(
                sample_data[:5],  # Test with first 5 records
                mapping_rules
            )
            
            if test_result.errors:
                report["errors"].extend(test_result.errors[:10])  # Limit errors
            if test_result.warnings:
                report["warnings"].extend(test_result.warnings[:10])
        
        # Generate recommendations
        if report["errors"] or report["warnings"]:
            report["valid"] = False
            report["recommendations"].append(
                "Review and fix mapping errors before applying to production data"
            )
        
        return report