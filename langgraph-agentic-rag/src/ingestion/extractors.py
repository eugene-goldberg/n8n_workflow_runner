"""Entity and relation extraction for knowledge graph construction."""

import logging
from typing import List, Dict, Any, Tuple

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import JsonOutputParser

from config.settings import settings

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """You are an expert at extracting entities and relationships from text for knowledge graph construction.

Given the following text, extract:
1. Entities: Important concepts, people, organizations, products, etc.
2. Relationships: How entities are connected

Follow this schema:
- Entity types: Person, Organization, Product, Technology, Concept, Location, Event
- Relationship types: WORKS_FOR, CREATED, USES, RELATES_TO, LOCATED_IN, PARTICIPATES_IN, MENTIONS

Text to analyze:
{text}

Return a JSON object with:
{{
  "entities": [
    {{"name": "entity_name", "type": "EntityType", "properties": {{"key": "value"}}}}
  ],
  "relationships": [
    {{"source": "entity1_name", "relation": "RELATION_TYPE", "target": "entity2_name", "properties": {{"key": "value"}}}}
  ]
}}

Be conservative - only extract clear, factual information."""


class EntityRelationExtractor:
    """Extract entities and relationships from text."""
    
    def __init__(self):
        """Initialize the extractor."""
        self.llm = ChatOpenAI(
            api_key=settings.openai.api_key,
            model=settings.openai.model,
            temperature=0  # Deterministic extraction
        )
        self.parser = JsonOutputParser()
    
    async def extract(self, text: str) -> Dict[str, Any]:
        """Extract entities and relationships from text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Dict containing entities and relationships
        """
        try:
            messages = [
                SystemMessage(content=EXTRACTION_PROMPT.format(text=text))
            ]
            
            response = await self.llm.ainvoke(messages)
            result = self.parser.parse(response.content)
            
            # Validate and clean the result
            entities = result.get("entities", [])
            relationships = result.get("relationships", [])
            
            # Ensure required fields
            for entity in entities:
                if "name" not in entity or "type" not in entity:
                    logger.warning(f"Invalid entity: {entity}")
                    entities.remove(entity)
                entity["properties"] = entity.get("properties", {})
            
            for rel in relationships:
                if "source" not in rel or "relation" not in rel or "target" not in rel:
                    logger.warning(f"Invalid relationship: {rel}")
                    relationships.remove(rel)
                rel["properties"] = rel.get("properties", {})
            
            logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships")
            return {
                "entities": entities,
                "relationships": relationships
            }
            
        except Exception as e:
            logger.error(f"Error in extraction: {e}")
            return {"entities": [], "relationships": []}
    
    def deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate entities based on name.
        
        Args:
            entities: List of entity dictionaries
            
        Returns:
            Deduplicated list of entities
        """
        seen = {}
        deduped = []
        
        for entity in entities:
            name = entity["name"].lower()
            if name not in seen:
                seen[name] = entity
                deduped.append(entity)
            else:
                # Merge properties
                seen[name]["properties"].update(entity.get("properties", {}))
        
        return deduped