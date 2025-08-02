"""LLM-based schema mapping (mock implementation for testing)"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
import re

from .mapping_rules import MappingRule, TransformationType
from .entity_models import SPYRO_ENTITIES


logger = logging.getLogger(__name__)


class LLMMapper:
    """Mock LLM mapper for testing - simulates intelligent mapping"""
    
    def __init__(self, model_name: str = "gpt-4"):
        """Initialize LLM mapper
        
        Args:
            model_name: Name of the model to use (mocked)
        """
        self.model_name = model_name
        self._init_mapping_knowledge()
    
    def _init_mapping_knowledge(self):
        """Initialize mapping knowledge base"""
        # Common field name variations and their mappings
        self.field_mappings = {
            # Customer mappings
            "company": ("Customer", "name", 0.95),
            "company_name": ("Customer", "name", 0.98),
            "organization": ("Customer", "name", 0.9),
            "org_name": ("Customer", "name", 0.9),
            "account_name": ("Customer", "name", 0.85),
            "annual_revenue": ("Customer", "arr", 0.9),
            "yearly_revenue": ("Customer", "arr", 0.85),
            "company_size": ("Customer", "size", 0.9),
            "segment": ("Customer", "size", 0.8),
            "tier": ("Customer", "size", 0.75),
            "vertical": ("Customer", "industry", 0.85),
            "sector": ("Customer", "industry", 0.8),
            "business_type": ("Customer", "industry", 0.75),
            "num_employees": ("Customer", "employee_count", 0.95),
            "headcount": ("Customer", "employee_count", 0.9),
            "staff_size": ("Customer", "employee_count", 0.85),
            "customer_health": ("Customer", "health_score", 0.9),
            "health_score": ("Customer", "health_score", 0.95),
            "health": ("Customer", "health_score", 0.85),
            "churn_risk": ("Customer", "churn_risk", 0.9),
            "risk_level": ("Customer", "churn_risk", 0.85),
            
            # Product mappings
            "product_name": ("Product", "name", 0.98),
            "offering": ("Product", "name", 0.8),
            "service": ("Product", "name", 0.75),
            "product_type": ("Product", "category", 0.9),
            "product_category": ("Product", "category", 0.95),
            "classification": ("Product", "category", 0.8),
            "capabilities": ("Product", "features", 0.85),
            "functionality": ("Product", "features", 0.8),
            "product_version": ("Product", "version", 0.95),
            "release": ("Product", "version", 0.8),
            
            # Subscription mappings
            "subscription_id": ("Subscription", "id", 0.98),
            "contract_id": ("Subscription", "id", 0.85),
            "monthly_revenue": ("Subscription", "mrr", 0.95),
            "monthly_recurring": ("Subscription", "mrr", 0.9),
            "mrr_amount": ("Subscription", "mrr", 0.98),
            "annual_contract_value": ("Subscription", "arr", 0.9),
            "acv": ("Subscription", "arr", 0.95),
            "contract_start": ("Subscription", "start_date", 0.9),
            "effective_date": ("Subscription", "start_date", 0.85),
            "contract_end": ("Subscription", "end_date", 0.9),
            "expiration_date": ("Subscription", "end_date", 0.85),
            "subscription_status": ("Subscription", "status", 0.95),
            "contract_status": ("Subscription", "status", 0.85),
            
            # Team mappings
            "team_name": ("Team", "name", 0.98),
            "department": ("Team", "name", 0.8),
            "team_size": ("Team", "size", 0.95),
            "member_count": ("Team", "size", 0.9),
            "team_lead": ("Team", "manager", 0.9),
            "manager_name": ("Team", "manager", 0.95),
            "supervisor": ("Team", "manager", 0.85),
            "area": ("Team", "focus_area", 0.8),
            "specialization": ("Team", "focus_area", 0.85),
            
            # Project mappings
            "project_name": ("Project", "name", 0.98),
            "initiative": ("Project", "name", 0.8),
            "project_type": ("Project", "type", 0.95),
            "category": ("Project", "type", 0.8),
            "project_status": ("Project", "status", 0.95),
            "phase": ("Project", "status", 0.8),
            "kickoff_date": ("Project", "start_date", 0.85),
            "launch_date": ("Project", "start_date", 0.8),
            "completion_date": ("Project", "end_date", 0.85),
            "deadline": ("Project", "end_date", 0.8),
            "allocated_budget": ("Project", "budget", 0.9),
            "funding": ("Project", "budget", 0.8)
        }
        
        # Transformation detection patterns
        self.transform_patterns = {
            "date": ["date", "time", "created", "updated", "modified", "start", "end"],
            "money": ["revenue", "price", "cost", "amount", "budget", "mrr", "arr"],
            "enum": ["status", "state", "type", "category", "level", "priority"],
            "array": ["list", "items", "features", "tags", "skills"]
        }
    
    async def generate_mappings(
        self,
        unmapped_fields: Dict[str, Any],
        target_entities: List[str],
        sample_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[MappingRule]:
        """Generate mapping rules using mock LLM
        
        Args:
            unmapped_fields: Fields that need mapping
            target_entities: Target entities to consider
            sample_data: Sample data for context
            
        Returns:
            List of generated mapping rules
        """
        await asyncio.sleep(0.1)  # Simulate API delay
        
        mappings = []
        
        for field_name, field_info in unmapped_fields.items():
            # Check direct mapping knowledge
            field_lower = field_name.lower()
            
            # Try exact match first
            if field_lower in self.field_mappings:
                entity, target_field, confidence = self.field_mappings[field_lower]
                if entity in target_entities:
                    transformation = self._detect_transformation(field_name, field_info)
                    
                    mappings.append(MappingRule(
                        source_field=field_name,
                        target_entity=entity,
                        target_field=target_field,
                        transformation=transformation["type"],
                        transform_params=transformation["params"],
                        confidence=confidence,
                        description=f"LLM mapping: {field_name} -> {entity}.{target_field}"
                    ))
                    continue
            
            # Try partial matches
            best_match = self._find_best_match(field_lower, target_entities)
            if best_match:
                entity, target_field, confidence = best_match
                transformation = self._detect_transformation(field_name, field_info)
                
                mappings.append(MappingRule(
                    source_field=field_name,
                    target_entity=entity,
                    target_field=target_field,
                    transformation=transformation["type"],
                    transform_params=transformation["params"],
                    confidence=confidence * 0.8,  # Lower confidence for partial matches
                    description=f"LLM mapping (partial): {field_name} -> {entity}.{target_field}"
                ))
        
        return mappings
    
    def _find_best_match(
        self,
        field_name: str,
        target_entities: List[str]
    ) -> Optional[Tuple[str, str, float]]:
        """Find best match using similarity"""
        best_match = None
        best_score = 0.0
        
        # Check each known mapping
        for known_field, (entity, target_field, base_confidence) in self.field_mappings.items():
            if entity not in target_entities:
                continue
            
            # Calculate similarity score
            score = self._calculate_similarity(field_name, known_field)
            
            if score > best_score and score > 0.6:  # Minimum threshold
                best_score = score
                best_match = (entity, target_field, base_confidence * score)
        
        return best_match
    
    def _calculate_similarity(self, field1: str, field2: str) -> float:
        """Calculate field name similarity"""
        # Simple token-based similarity
        tokens1 = set(re.findall(r'\w+', field1.lower()))
        tokens2 = set(re.findall(r'\w+', field2.lower()))
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        # Jaccard similarity
        jaccard = len(intersection) / len(union)
        
        # Bonus for matching key tokens
        key_tokens = {"id", "name", "date", "status", "type", "amount"}
        key_matches = len((tokens1 & tokens2) & key_tokens)
        
        return min(1.0, jaccard + (key_matches * 0.1))
    
    def _detect_transformation(
        self,
        field_name: str,
        field_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Detect required transformation based on field characteristics"""
        field_lower = field_name.lower()
        
        # Check for date fields
        for pattern in self.transform_patterns["date"]:
            if pattern in field_lower:
                return {
                    "type": TransformationType.CAST,
                    "params": {"to_type": "date"}
                }
        
        # Check for money fields  
        for pattern in self.transform_patterns["money"]:
            if pattern in field_lower:
                return {
                    "type": TransformationType.CAST,
                    "params": {"to_type": "integer"}
                }
        
        # Check for enum fields
        for pattern in self.transform_patterns["enum"]:
            if pattern in field_lower:
                # Would need actual values to create proper mapping
                return {
                    "type": TransformationType.DIRECT,
                    "params": {}
                }
        
        # Check for array fields
        for pattern in self.transform_patterns["array"]:
            if pattern in field_lower:
                return {
                    "type": TransformationType.SPLIT,
                    "params": {"separator": ","}
                }
        
        # Default to direct mapping
        return {
            "type": TransformationType.DIRECT,
            "params": {}
        }
    
    async def improve_mapping(
        self,
        current_mapping: MappingRule,
        feedback: str,
        sample_values: Optional[List[Any]] = None
    ) -> MappingRule:
        """Improve a mapping based on feedback (mock implementation)"""
        await asyncio.sleep(0.05)  # Simulate API delay
        
        # Mock improvement - in real implementation would use LLM
        improved = MappingRule(
            source_field=current_mapping.source_field,
            target_entity=current_mapping.target_entity,
            target_field=current_mapping.target_field,
            transformation=current_mapping.transformation,
            transform_params=current_mapping.transform_params,
            confidence=min(1.0, current_mapping.confidence + 0.1),
            description=f"{current_mapping.description} (improved based on feedback)"
        )
        
        # Simulate learning from feedback
        if "wrong type" in feedback.lower():
            improved.transformation = TransformationType.CAST
            improved.transform_params["to_type"] = "string"
        elif "missing" in feedback.lower():
            improved.transformation = TransformationType.CONSTANT
            improved.transform_params["value"] = "default"
        
        return improved