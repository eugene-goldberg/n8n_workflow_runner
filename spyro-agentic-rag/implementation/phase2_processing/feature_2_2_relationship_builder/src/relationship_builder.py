"""Core relationship building functionality"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple, Any
import yaml

from .models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    RelationshipRule,
    RelationshipDiscoveryContext,
    TemporalAspect
)

logger = logging.getLogger(__name__)


class RelationshipBuilder:
    """Core relationship building functionality"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize relationship builder
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.rules = self._load_rules()
        self._relationship_cache: Dict[str, Relationship] = {}
        
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from file"""
        if not config_path:
            config_path = "config/relationship_builder.yaml"
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {config_path}, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "relationship_discovery": {
                "explicit": {
                    "enable": True,
                    "rules_file": "config/relationship_rules.yaml"
                },
                "semantic": {
                    "enable": True,
                    "confidence_threshold": 0.7
                },
                "temporal": {
                    "enable": True,
                    "correlation_window_days": 90
                },
                "deduplication": {
                    "enable": True,
                    "merge_strategy": "highest_confidence"
                }
            },
            "performance": {
                "parallel_workers": 4,
                "cache_relationships": True,
                "batch_size": 100
            }
        }
    
    def _load_rules(self) -> List[RelationshipRule]:
        """Load explicit relationship rules"""
        rules_file = self.config.get("relationship_discovery", {}).get("explicit", {}).get("rules_file")
        if not rules_file:
            return self._get_default_rules()
        
        try:
            with open(rules_file, 'r') as f:
                rules_data = yaml.safe_load(f)
                return self._parse_rules(rules_data)
        except FileNotFoundError:
            logger.warning(f"Rules file not found at {rules_file}, using defaults")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> List[RelationshipRule]:
        """Get default relationship rules"""
        return [
            RelationshipRule(
                source_type="Subscription",
                field="customer_id",
                target_type="Customer",
                relationship=RelationshipType.BELONGS_TO
            ),
            RelationshipRule(
                source_type="Team",
                field="manager_id",
                target_type="Person",
                relationship=RelationshipType.MANAGED_BY
            ),
            RelationshipRule(
                source_type="Project",
                field="team_id",
                target_type="Team",
                relationship=RelationshipType.ASSIGNED_TO
            ),
            RelationshipRule(
                source_type="Risk",
                field="customer_id",
                target_type="Customer",
                relationship=RelationshipType.IMPACTS
            )
        ]
    
    def _parse_rules(self, rules_data: Dict[str, Any]) -> List[RelationshipRule]:
        """Parse rules from configuration data"""
        rules = []
        for rule_dict in rules_data.get("explicit_rules", []):
            try:
                rule = RelationshipRule(
                    source_type=rule_dict["source_type"],
                    field=rule_dict["field"],
                    target_type=rule_dict["target_type"],
                    relationship=RelationshipType(rule_dict["relationship"]),
                    bidirectional=rule_dict.get("bidirectional", False),
                    required=rule_dict.get("required", True)
                )
                rules.append(rule)
            except (KeyError, ValueError) as e:
                logger.error(f"Failed to parse rule: {e}")
        
        return rules
    
    async def build_relationships(
        self,
        entities: List[Entity],
        context: Optional[RelationshipDiscoveryContext] = None
    ) -> List[Relationship]:
        """Build all relationships between entities
        
        Args:
            entities: List of entities to analyze
            context: Optional discovery context
            
        Returns:
            List of discovered relationships
        """
        if not entities:
            return []
        
        context = context or RelationshipDiscoveryContext()
        relationships = []
        
        # Build entity index for faster lookup
        entity_index = self._build_entity_index(entities)
        
        # Discover different types of relationships
        tasks = []
        
        if self.config["relationship_discovery"]["explicit"]["enable"]:
            tasks.append(self._build_explicit_relationships(entities, entity_index, context))
        
        if self.config["relationship_discovery"]["semantic"]["enable"]:
            tasks.append(self._build_semantic_relationships(entities, context))
        
        if self.config["relationship_discovery"]["temporal"]["enable"]:
            tasks.append(self._build_temporal_relationships(entities, context))
        
        # Run discovery tasks in parallel
        if tasks:
            discovered_sets = await asyncio.gather(*tasks)
            for discovered in discovered_sets:
                relationships.extend(discovered)
        
        # Deduplicate relationships
        if self.config["relationship_discovery"]["deduplication"]["enable"]:
            relationships = self._deduplicate_relationships(relationships)
        
        # Filter based on context
        relationships = [
            rel for rel in relationships
            if context.should_include_relationship(rel)
        ]
        
        # Cache relationships if enabled
        if self.config["performance"]["cache_relationships"]:
            for rel in relationships:
                cache_key = f"{rel.source.id}-{rel.target.id}-{rel.relationship_type.value}"
                self._relationship_cache[cache_key] = rel
        
        return relationships
    
    def _build_entity_index(self, entities: List[Entity]) -> Dict[str, Dict[str, Entity]]:
        """Build index for fast entity lookup by type and ID"""
        index = defaultdict(dict)
        for entity in entities:
            index[entity.type][entity.id] = entity
            
            # Also index by source IDs
            for source, source_id in entity.source_ids.items():
                index[entity.type][source_id] = entity
        
        return dict(index)
    
    async def _build_explicit_relationships(
        self,
        entities: List[Entity],
        entity_index: Dict[str, Dict[str, Entity]],
        context: RelationshipDiscoveryContext
    ) -> List[Relationship]:
        """Build explicit ID-based relationships"""
        relationships = []
        
        for entity in entities:
            for rule in self.rules:
                if not rule.matches(entity):
                    continue
                
                # Get target ID from entity attributes
                target_id = entity.attributes.get(rule.field)
                if not target_id:
                    continue
                
                # Find target entity
                target_entity = entity_index.get(rule.target_type, {}).get(target_id)
                if not target_entity:
                    if rule.required:
                        logger.warning(
                            f"Target entity not found: {rule.target_type} {target_id} "
                            f"referenced by {entity.type} {entity.id}"
                        )
                    continue
                
                # Create relationship
                rel = Relationship(
                    source=entity,
                    target=target_entity,
                    relationship_type=rule.relationship,
                    direction=(RelationshipDirection.BIDIRECTIONAL 
                              if rule.bidirectional 
                              else RelationshipDirection.UNIDIRECTIONAL),
                    strength=RelationshipStrength.STRONG,
                    confidence=1.0,  # Explicit relationships have high confidence
                    evidence=[f"Explicit reference via {rule.field}"],
                    temporal_aspect=TemporalAspect.PRESENT
                )
                
                relationships.append(rel)
                
                # Create reverse relationship if bidirectional
                if rule.bidirectional:
                    reverse_type = self._get_reverse_relationship_type(rule.relationship)
                    if reverse_type:
                        reverse_rel = Relationship(
                            source=target_entity,
                            target=entity,
                            relationship_type=reverse_type,
                            direction=RelationshipDirection.BIDIRECTIONAL,
                            strength=RelationshipStrength.STRONG,
                            confidence=1.0,
                            evidence=[f"Reverse of {rule.field} reference"],
                            temporal_aspect=TemporalAspect.PRESENT
                        )
                        relationships.append(reverse_rel)
        
        return relationships
    
    async def _build_semantic_relationships(
        self,
        entities: List[Entity],
        context: RelationshipDiscoveryContext
    ) -> List[Relationship]:
        """Build semantic relationships (placeholder for semantic miner integration)"""
        # This will be implemented when SemanticRelationshipMiner is ready
        relationships = []
        
        # For now, add some simple semantic relationships based on entity attributes
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Check for same team membership
                if (entity1.type == "Person" and entity2.type == "Person" and
                    entity1.attributes.get("team") == entity2.attributes.get("team") and
                    entity1.attributes.get("team") is not None):
                    
                    rel = Relationship(
                        source=entity1,
                        target=entity2,
                        relationship_type=RelationshipType.WORKS_WITH,
                        direction=RelationshipDirection.BIDIRECTIONAL,
                        strength=RelationshipStrength.MODERATE,
                        confidence=0.8,
                        evidence=["Same team membership"],
                        temporal_aspect=TemporalAspect.PRESENT
                    )
                    relationships.append(rel)
        
        return relationships
    
    async def _build_temporal_relationships(
        self,
        entities: List[Entity],
        context: RelationshipDiscoveryContext
    ) -> List[Relationship]:
        """Build temporal relationships (placeholder for temporal analyzer integration)"""
        # This will be implemented when TemporalRelationshipAnalyzer is ready
        relationships = []
        
        # For now, add simple temporal relationships based on dates
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i+1:]:
                # Check for temporal precedence
                date1 = entity1.attributes.get("created_date") or entity1.attributes.get("start_date")
                date2 = entity2.attributes.get("created_date") or entity2.attributes.get("start_date")
                
                if date1 and date2:
                    try:
                        dt1 = datetime.fromisoformat(str(date1).replace('Z', '+00:00'))
                        dt2 = datetime.fromisoformat(str(date2).replace('Z', '+00:00'))
                        
                        if dt1 < dt2:
                            rel = Relationship(
                                source=entity1,
                                target=entity2,
                                relationship_type=RelationshipType.PRECEDES,
                                direction=RelationshipDirection.UNIDIRECTIONAL,
                                strength=RelationshipStrength.MODERATE,
                                confidence=0.7,
                                evidence=[f"Temporal order: {date1} before {date2}"],
                                temporal_aspect=TemporalAspect.PAST
                            )
                            relationships.append(rel)
                    except (ValueError, TypeError):
                        pass
        
        return relationships
    
    def _deduplicate_relationships(self, relationships: List[Relationship]) -> List[Relationship]:
        """Remove duplicate relationships"""
        seen = {}
        deduped = []
        
        strategy = self.config["relationship_discovery"]["deduplication"]["merge_strategy"]
        
        for rel in relationships:
            # Create unique key for relationship
            key = (
                rel.source.id,
                rel.target.id,
                rel.relationship_type.value,
                rel.direction.value
            )
            
            if key in seen:
                # Merge based on strategy
                existing = seen[key]
                if strategy == "highest_confidence":
                    if rel.confidence > existing.confidence:
                        seen[key] = rel
                        # Update in deduped list
                        idx = deduped.index(existing)
                        deduped[idx] = rel
                elif strategy == "merge_evidence":
                    # Merge evidence from both
                    existing.evidence.extend(rel.evidence)
                    existing.evidence = list(set(existing.evidence))
                    existing.confidence = max(existing.confidence, rel.confidence)
            else:
                seen[key] = rel
                deduped.append(rel)
        
        return deduped
    
    def _get_reverse_relationship_type(self, rel_type: RelationshipType) -> Optional[RelationshipType]:
        """Get reverse relationship type for bidirectional relationships"""
        reverse_mapping = {
            RelationshipType.PARENT_OF: RelationshipType.CHILD_OF,
            RelationshipType.CHILD_OF: RelationshipType.PARENT_OF,
            RelationshipType.MANAGES: RelationshipType.REPORTS_TO,
            RelationshipType.REPORTS_TO: RelationshipType.MANAGES,
            RelationshipType.OWNS: RelationshipType.BELONGS_TO,
            RelationshipType.BELONGS_TO: RelationshipType.OWNS
        }
        
        return reverse_mapping.get(rel_type)
    
    def get_relationships_for_entity(
        self,
        entity_id: str,
        rel_type: Optional[RelationshipType] = None,
        as_source: bool = True,
        as_target: bool = True
    ) -> List[Relationship]:
        """Get all relationships for a specific entity
        
        Args:
            entity_id: Entity ID to search for
            rel_type: Optional relationship type filter
            as_source: Include relationships where entity is source
            as_target: Include relationships where entity is target
            
        Returns:
            List of relationships involving the entity
        """
        relationships = []
        
        for rel in self._relationship_cache.values():
            # Check if entity is involved
            is_source = rel.source.id == entity_id
            is_target = rel.target.id == entity_id
            
            if not ((is_source and as_source) or (is_target and as_target)):
                continue
            
            # Check relationship type filter
            if rel_type and rel.relationship_type != rel_type:
                continue
            
            relationships.append(rel)
        
        return relationships
    
    def clear_cache(self):
        """Clear relationship cache"""
        self._relationship_cache.clear()