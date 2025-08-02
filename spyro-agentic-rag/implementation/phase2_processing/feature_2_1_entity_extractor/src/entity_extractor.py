"""Core entity extraction functionality"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio

from .models import (
    Entity, EntityType, MappingRule, ValidationError, 
    ValidationResult, ExtractionContext
)
from .validators import EntityValidator

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Extracts entities from raw data using mapping rules"""
    
    def __init__(self, validator: Optional[EntityValidator] = None):
        """Initialize entity extractor
        
        Args:
            validator: Optional entity validator instance
        """
        self.validator = validator or EntityValidator()
        self._extraction_stats = {
            "total_extracted": 0,
            "validation_errors": 0,
            "auto_fixed": 0
        }
    
    async def extract_entities(
        self,
        raw_data: Dict[str, Any],
        mapping_rules: Dict[str, MappingRule],
        context: Optional[ExtractionContext] = None
    ) -> List[Entity]:
        """Extract entities from raw data
        
        Args:
            raw_data: Raw data dictionary
            mapping_rules: Field to entity mapping rules
            context: Optional extraction context
            
        Returns:
            List of extracted entities
        """
        context = context or ExtractionContext(source_system="unknown")
        
        # Group fields by entity type
        entities_data = self._group_by_entity_type(raw_data, mapping_rules)
        
        # Extract entities
        entities = []
        for entity_type, field_data in entities_data.items():
            entity = await self._extract_single_entity(
                entity_type, field_data, raw_data, context
            )
            if entity:
                entities.append(entity)
        
        # Validate entities
        validated_entities = []
        for entity in entities:
            validated = await self._validate_and_fix_entity(entity, context)
            if validated:
                validated_entities.append(validated)
        
        self._extraction_stats["total_extracted"] += len(validated_entities)
        return validated_entities
    
    async def extract_entities_bulk(
        self,
        records: List[Dict[str, Any]],
        mapping_rules: Dict[str, MappingRule],
        context: Optional[ExtractionContext] = None,
        batch_size: int = 100
    ) -> List[Entity]:
        """Extract entities from multiple records in batches
        
        Args:
            records: List of raw data records
            mapping_rules: Field to entity mapping rules
            context: Optional extraction context
            batch_size: Number of records to process concurrently
            
        Returns:
            List of extracted entities
        """
        all_entities = []
        
        # Process in batches
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self.extract_entities(record, mapping_rules, context)
                for record in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Collect successful extractions
            for result in batch_results:
                if isinstance(result, list):
                    all_entities.extend(result)
                elif isinstance(result, Exception):
                    logger.error(f"Extraction error: {result}")
        
        return all_entities
    
    def _group_by_entity_type(
        self,
        raw_data: Dict[str, Any],
        mapping_rules: Dict[str, MappingRule]
    ) -> Dict[EntityType, Dict[str, Any]]:
        """Group raw data fields by entity type"""
        grouped = {}
        
        for field, rule in mapping_rules.items():
            if field not in raw_data and rule.required:
                logger.warning(f"Required field '{field}' not found in raw data")
                continue
            
            entity_type = EntityType(rule.entity_type)
            if entity_type not in grouped:
                grouped[entity_type] = {}
            
            # Apply transformation if specified
            value = raw_data.get(field, rule.default_value)
            if value is not None and rule.transformation:
                value = self._apply_transformation(value, rule.transformation)
            
            grouped[entity_type][rule.target_field] = value
        
        return grouped
    
    async def _extract_single_entity(
        self,
        entity_type: EntityType,
        attributes: Dict[str, Any],
        raw_data: Dict[str, Any],
        context: ExtractionContext
    ) -> Optional[Entity]:
        """Extract a single entity"""
        # Skip if no attributes
        if not attributes:
            return None
        
        # Generate source ID if available
        source_id = None
        if "id" in attributes:
            source_id = f"{context.source_system}_{attributes['id']}"
        elif "id" in raw_data:
            source_id = f"{context.source_system}_{raw_data['id']}"
        
        # Create entity
        entity = Entity(
            type=entity_type,
            source_id=source_id,
            source_system=context.source_system,
            attributes=attributes,
            metadata={
                "extraction_timestamp": context.extraction_timestamp.isoformat(),
                "raw_record_keys": list(raw_data.keys())
            }
        )
        
        return entity
    
    async def _validate_and_fix_entity(
        self,
        entity: Entity,
        context: ExtractionContext
    ) -> Optional[Entity]:
        """Validate entity and attempt to fix errors"""
        # Validate entity
        validation_result = await self.validator.validate_entity(
            entity,
            context.validation_config.get(entity.type.value, {})
        )
        
        if validation_result.is_valid:
            return entity
        
        # Track validation errors
        self._extraction_stats["validation_errors"] += len(validation_result.errors)
        
        # Attempt to fix errors if configured
        if context.validation_config.get("auto_fix_errors", False):
            fixed_entity = await self._auto_fix_validation_errors(
                entity,
                validation_result
            )
            
            if fixed_entity:
                self._extraction_stats["auto_fixed"] += 1
                return fixed_entity
        
        # Log validation errors
        for error in validation_result.errors:
            logger.error(
                f"Validation error for entity {entity.id}: "
                f"{error.field} - {error.message}"
            )
        
        # Return entity with warnings if only warnings exist
        if not validation_result.has_errors and validation_result.has_warnings:
            return entity
        
        return None
    
    async def _auto_fix_validation_errors(
        self,
        entity: Entity,
        validation_result: ValidationResult
    ) -> Optional[Entity]:
        """Attempt to automatically fix validation errors"""
        # Create a copy of the entity
        fixed_entity = Entity(
            id=entity.id,
            type=entity.type,
            source_id=entity.source_id,
            source_system=entity.source_system,
            attributes=entity.attributes.copy(),
            metadata=entity.metadata.copy()
        )
        
        # Apply suggested fixes
        for error in validation_result.errors:
            if error.suggested_fix is not None:
                fixed_entity.attributes[error.field] = error.suggested_fix
                logger.info(
                    f"Auto-fixed {error.field} for entity {entity.id}: "
                    f"{error.suggested_fix}"
                )
        
        # Re-validate fixed entity
        revalidation = await self.validator.validate_entity(fixed_entity)
        
        if revalidation.is_valid:
            fixed_entity.metadata["auto_fixed"] = True
            fixed_entity.metadata["fixes_applied"] = [
                {
                    "field": error.field,
                    "original": entity.attributes.get(error.field),
                    "fixed": error.suggested_fix
                }
                for error in validation_result.errors
                if error.suggested_fix is not None
            ]
            return fixed_entity
        
        return None
    
    def _apply_transformation(self, value: Any, transformation: str) -> Any:
        """Apply transformation to a value"""
        try:
            if transformation == "uppercase":
                return str(value).upper()
            elif transformation == "lowercase":
                return str(value).lower()
            elif transformation == "strip":
                return str(value).strip()
            elif transformation == "int":
                return int(value)
            elif transformation == "float":
                return float(value)
            elif transformation == "bool":
                return bool(value)
            elif transformation.startswith("multiply:"):
                factor = float(transformation.split(":")[1])
                return float(value) * factor
            elif transformation.startswith("divide:"):
                divisor = float(transformation.split(":")[1])
                return float(value) / divisor if divisor != 0 else 0
            else:
                logger.warning(f"Unknown transformation: {transformation}")
                return value
        except Exception as e:
            logger.error(f"Transformation error: {e}")
            return value
    
    def get_extraction_stats(self) -> Dict[str, int]:
        """Get extraction statistics"""
        return self._extraction_stats.copy()
    
    def reset_stats(self):
        """Reset extraction statistics"""
        self._extraction_stats = {
            "total_extracted": 0,
            "validation_errors": 0,
            "auto_fixed": 0
        }