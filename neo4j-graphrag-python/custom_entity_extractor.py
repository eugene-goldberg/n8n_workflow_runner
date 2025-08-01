#!/usr/bin/env python3
"""
Custom Entity Extractor for SpyroSolutions with property validation
Ensures that extracted entities have the correct properties and formats
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import json
import logging
from dataclasses import dataclass
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.experimental.components.entity_relation_extractor import LLMEntityRelationExtractor
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class EntitySchema:
    """Schema definition for an entity type"""
    label: str
    required_properties: List[str]
    optional_properties: List[str]
    property_validators: Dict[str, callable]

class SpyroEntityValidator:
    """Validates entities according to SpyroSolutions schema"""
    
    def __init__(self):
        self.schemas = self._create_schemas()
    
    def _create_schemas(self) -> Dict[str, EntitySchema]:
        """Define validation schemas for each entity type"""
        
        def validate_arr(value: str) -> bool:
            """Validate ARR format (e.g., $5M, $100K, $3.2M)"""
            return bool(re.match(r'^\$[\d.]+[KMB]?$', value))
        
        def validate_score(value: Any) -> bool:
            """Validate score is between 0-100"""
            try:
                score = float(value)
                return 0 <= score <= 100
            except:
                return False
        
        def validate_risk_level(value: str) -> bool:
            """Validate risk level"""
            return value.lower() in ['high', 'medium', 'low']
        
        def validate_integer(value: Any) -> bool:
            """Validate integer value"""
            try:
                int(value)
                return True
            except:
                return False
        
        schemas = {
            "Customer": EntitySchema(
                label="Customer",
                required_properties=["name"],
                optional_properties=["industry", "segment"],
                property_validators={"name": lambda x: isinstance(x, str) and len(x) > 0}
            ),
            "Product": EntitySchema(
                label="Product",
                required_properties=["name"],
                optional_properties=["description", "category"],
                property_validators={"name": lambda x: isinstance(x, str) and len(x) > 0}
            ),
            "Project": EntitySchema(
                label="Project",
                required_properties=["name"],
                optional_properties=["status", "deadline"],
                property_validators={
                    "name": lambda x: isinstance(x, str) and len(x) > 0,
                    "status": lambda x: x in ["planning", "active", "completed", "on-hold"]
                }
            ),
            "Team": EntitySchema(
                label="Team",
                required_properties=["name"],
                optional_properties=["size", "department"],
                property_validators={
                    "name": lambda x: isinstance(x, str) and len(x) > 0,
                    "size": validate_integer
                }
            ),
            "SaaSSubscription": EntitySchema(
                label="SaaSSubscription",
                required_properties=["plan", "ARR"],
                optional_properties=["start_date", "renewal_date"],
                property_validators={
                    "plan": lambda x: isinstance(x, str) and len(x) > 0,
                    "ARR": validate_arr
                }
            ),
            "Risk": EntitySchema(
                label="Risk",
                required_properties=["level"],
                optional_properties=["type", "description", "mitigation"],
                property_validators={
                    "level": validate_risk_level
                }
            ),
            "OperationalCost": EntitySchema(
                label="OperationalCost",
                required_properties=["cost"],
                optional_properties=["category", "period"],
                property_validators={
                    "cost": validate_arr
                }
            ),
            "CustomerSuccessScore": EntitySchema(
                label="CustomerSuccessScore",
                required_properties=["score"],
                optional_properties=["health_status", "trend"],
                property_validators={
                    "score": validate_score,
                    "health_status": lambda x: x in ["healthy", "at-risk", "critical"]
                }
            )
        }
        
        return schemas
    
    def validate_entity(self, entity: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate an entity against its schema
        Returns (is_valid, list_of_errors)
        """
        errors = []
        
        # Check if entity type is known
        entity_type = entity.get("type")
        if entity_type not in self.schemas:
            return False, [f"Unknown entity type: {entity_type}"]
        
        schema = self.schemas[entity_type]
        properties = entity.get("properties", {})
        
        # Check required properties
        for prop in schema.required_properties:
            if prop not in properties or properties[prop] is None:
                errors.append(f"Missing required property '{prop}' for {entity_type}")
        
        # Validate property values
        for prop, value in properties.items():
            if prop in schema.property_validators:
                validator = schema.property_validators[prop]
                if not validator(value):
                    errors.append(f"Invalid value '{value}' for property '{prop}' in {entity_type}")
        
        return len(errors) == 0, errors
    
    def fix_entity(self, entity: Dict[str, Any]) -> Dict[str, Any]:
        """Attempt to fix common entity issues"""
        entity_type = entity.get("type")
        if entity_type not in self.schemas:
            return entity
        
        schema = self.schemas[entity_type]
        properties = entity.get("properties", {})
        
        # Fix risk levels
        if entity_type == "Risk" and "level" in properties:
            level = str(properties["level"]).lower()
            if level in ["high", "medium", "low"]:
                properties["level"] = level.capitalize()
        
        # Fix ARR format
        if "ARR" in properties:
            arr = properties["ARR"]
            # Add $ if missing
            if isinstance(arr, str) and not arr.startswith("$"):
                properties["ARR"] = f"${arr}"
        
        # Fix cost format
        if "cost" in properties:
            cost = properties["cost"]
            if isinstance(cost, str) and not cost.startswith("$"):
                properties["cost"] = f"${cost}"
        
        # Fix team size to integer
        if entity_type == "Team" and "size" in properties:
            try:
                properties["size"] = int(properties["size"])
            except:
                pass
        
        # Fix score to float
        if entity_type == "CustomerSuccessScore" and "score" in properties:
            try:
                properties["score"] = float(properties["score"])
            except:
                pass
        
        entity["properties"] = properties
        return entity


class CustomEntityExtractor:
    """
    Custom entity extractor with validation and property extraction
    """
    
    def __init__(self, llm: Optional[OpenAILLM] = None):
        self.llm = llm or OpenAILLM(
            model_name="gpt-4o",
            model_params={
                "temperature": 0,
                "response_format": {"type": "json_object"}
            }
        )
        self.validator = SpyroEntityValidator()
        
    def create_extraction_prompt(self) -> str:
        """Create a detailed prompt for entity extraction"""
        return """
Extract entities and relationships from the following text according to the SpyroSolutions schema.

ENTITY TYPES AND REQUIRED PROPERTIES:

1. Customer (required: name)
   - Extract organization/company names
   - Example: "TechCorp Industries", "GlobalBank Financial"

2. Product (required: name)
   - Extract product or service names
   - Example: "SpyroCloud Platform", "SpyroSecure"

3. Project (required: name)
   - Extract project names
   - Example: "Project Apollo", "Migration Initiative"

4. Team (required: name, optional: size as integer)
   - Extract team names and sizes
   - Example: {"name": "AI/ML Team", "size": 30}

5. SaaSSubscription (required: plan, ARR)
   - Extract subscription plan names and Annual Recurring Revenue
   - ARR must be in format: $[number][K/M/B]
   - Example: {"plan": "Enterprise Plus", "ARR": "$5M"}

6. Risk (required: level)
   - Extract risk levels: High, Medium, or Low
   - Include type and description if mentioned
   - Example: {"level": "Medium", "type": "Churn Risk", "description": "considering competitors"}

7. OperationalCost (required: cost)
   - Extract cost amounts in $ format
   - Example: {"cost": "$3.2M"}

8. CustomerSuccessScore (required: score)
   - Extract numeric scores (0-100)
   - Include health status if mentioned
   - Example: {"score": 85.5, "health_status": "healthy"}

RELATIONSHIP TYPES:
- SUBSCRIBES_TO (Customer -> SaaSSubscription)
- HAS_RISK (Customer -> Risk)
- USES (Customer -> Product)
- ASSIGNED_TO_TEAM (Product -> Team)
- HAS_OPERATIONAL_COST (Project -> OperationalCost)
- HAS_SUCCESS_SCORE (Customer -> CustomerSuccessScore)

EXTRACTION RULES:
1. Extract exact names and values from the text
2. Preserve monetary values exactly as stated (e.g., "$5M ARR")
3. Convert team sizes to integers
4. Normalize risk levels to High/Medium/Low
5. Extract relationships based on context

Return a JSON object with:
{
    "entities": [
        {
            "type": "EntityType",
            "properties": {
                "property1": "value1",
                "property2": "value2"
            }
        }
    ],
    "relationships": [
        {
            "source": {"type": "SourceType", "name": "SourceName"},
            "target": {"type": "TargetType", "name": "TargetName"},
            "type": "RELATIONSHIP_TYPE"
        }
    ]
}

Text to analyze:
"""
    
    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities with validation"""
        prompt = self.create_extraction_prompt() + text
        
        try:
            # Get LLM response
            response = await self.llm.ainvoke(prompt)
            
            # Parse JSON response - handle different response formats
            response_text = ""
            if hasattr(response, 'content'):
                response_text = response.content
            elif hasattr(response, 'text'):
                response_text = response.text
            else:
                response_text = str(response)
            
            # Log the response for debugging
            logger.debug(f"LLM Response: {response_text}")
            
            # Try to parse JSON
            result = json.loads(response_text)
            
            # Validate and fix entities
            validated_entities = []
            validation_errors = []
            
            for entity in result.get("entities", []):
                # Fix common issues
                fixed_entity = self.validator.fix_entity(entity)
                
                # Validate
                is_valid, errors = self.validator.validate_entity(fixed_entity)
                
                if is_valid:
                    validated_entities.append(fixed_entity)
                else:
                    validation_errors.extend(errors)
                    # Still include the entity but log the errors
                    validated_entities.append(fixed_entity)
                    logger.warning(f"Entity validation errors: {errors}")
            
            result["entities"] = validated_entities
            
            if validation_errors:
                result["validation_errors"] = validation_errors
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {"entities": [], "relationships": [], "error": str(e)}
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return {"entities": [], "relationships": [], "error": str(e)}


def main():
    """Test the custom entity extractor"""
    
    # Sample text
    text = """
    TechCorp Industries is our largest customer with an Enterprise Plus subscription 
    worth $5M ARR. They have a medium risk level due to considering competitive solutions.
    
    The AI/ML Team with 30 engineers is assigned to work on SpyroCloud Platform.
    
    Project Apollo has operational costs of $3.2M and is critical for our Q4 objectives.
    
    GlobalBank Financial has a customer success score of 92.5 and is in healthy status.
    """
    
    import asyncio
    
    async def test_extraction():
        extractor = CustomEntityExtractor()
        result = await extractor.extract_entities(text)
        
        print("Extracted Entities:")
        print(json.dumps(result, indent=2))
        
        # Test validation separately
        validator = SpyroEntityValidator()
        
        test_entities = [
            {
                "type": "Customer",
                "properties": {"name": "TechCorp Industries"}
            },
            {
                "type": "SaaSSubscription",
                "properties": {"plan": "Enterprise Plus", "ARR": "5M"}  # Missing $
            },
            {
                "type": "Risk",
                "properties": {"level": "medium"}  # Should be capitalized
            },
            {
                "type": "Team",
                "properties": {"name": "AI/ML Team", "size": "30"}  # String instead of int
            }
        ]
        
        print("\n\nValidation Tests:")
        for entity in test_entities:
            fixed = validator.fix_entity(entity)
            is_valid, errors = validator.validate_entity(fixed)
            print(f"\nEntity: {entity}")
            print(f"Fixed: {fixed}")
            print(f"Valid: {is_valid}")
            if errors:
                print(f"Errors: {errors}")
    
    asyncio.run(test_extraction())


if __name__ == "__main__":
    main()