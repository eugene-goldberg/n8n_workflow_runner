"""Multi-source entity resolution functionality"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import asyncio
from rapidfuzz import fuzz
from collections import defaultdict

from .models import Entity, EntityType, ResolutionCandidate, ConfidenceLevel

logger = logging.getLogger(__name__)


class MultiSourceEntityResolver:
    """Resolves duplicate entities across multiple data sources"""
    
    def __init__(
        self,
        similarity_threshold: float = 0.85,
        use_llm_validation: bool = False,
        merge_strategy: str = "most_complete"
    ):
        """Initialize resolver
        
        Args:
            similarity_threshold: Minimum similarity score for matching
            use_llm_validation: Whether to use LLM for complex matches
            merge_strategy: Strategy for merging entities
                - most_complete: Use entity with most attributes
                - most_recent: Use most recently updated
                - weighted: Weighted merge based on source reliability
        """
        self.similarity_threshold = similarity_threshold
        self.use_llm_validation = use_llm_validation
        self.merge_strategy = merge_strategy
        self._resolution_cache = {}
    
    async def resolve_entities(
        self,
        entities: List[Entity],
        group_by_type: bool = True
    ) -> List[Entity]:
        """Resolve duplicate entities
        
        Args:
            entities: List of entities to resolve
            group_by_type: Whether to group by entity type first
            
        Returns:
            List of resolved entities
        """
        if not entities:
            return []
        
        # Group by entity type if requested
        if group_by_type:
            grouped = defaultdict(list)
            for entity in entities:
                grouped[entity.type].append(entity)
            
            resolved = []
            for entity_type, type_entities in grouped.items():
                resolved.extend(await self._resolve_entity_group(type_entities))
            
            return resolved
        else:
            return await self._resolve_entity_group(entities)
    
    async def _resolve_entity_group(self, entities: List[Entity]) -> List[Entity]:
        """Resolve a group of entities of the same type"""
        if len(entities) <= 1:
            return entities
        
        # Find duplicate candidates
        candidates = await self._find_duplicate_candidates(entities)
        
        # Merge duplicate entities
        resolved_entities = []
        processed_ids = set()
        
        for candidate in candidates:
            # Skip if already processed
            entity_ids = {e.id for e in candidate.entities}
            if entity_ids & processed_ids:
                continue
            
            # Resolve candidate group
            resolved = await self._resolve_candidate_group(candidate)
            resolved_entities.append(resolved)
            processed_ids.update(entity_ids)
        
        # Add entities that weren't part of any candidate group
        for entity in entities:
            if entity.id not in processed_ids:
                resolved_entities.append(entity)
        
        return resolved_entities
    
    async def _find_duplicate_candidates(
        self,
        entities: List[Entity]
    ) -> List[ResolutionCandidate]:
        """Find potential duplicate entities"""
        candidates = []
        processed = set()
        
        for i, entity1 in enumerate(entities):
            if entity1.id in processed:
                continue
            
            candidate_entities = [entity1]
            similarity_scores = {}
            match_reasons = []
            
            for j, entity2 in enumerate(entities[i+1:], i+1):
                if entity2.id in processed:
                    continue
                
                # Calculate similarity
                score, reasons = await self._calculate_similarity(entity1, entity2)
                
                if score >= self.similarity_threshold:
                    candidate_entities.append(entity2)
                    similarity_scores[f"{entity1.id}-{entity2.id}"] = score
                    match_reasons.extend(reasons)
            
            # Create candidate if duplicates found
            if len(candidate_entities) > 1:
                candidates.append(ResolutionCandidate(
                    entities=candidate_entities,
                    similarity_scores=similarity_scores,
                    match_reasons=list(set(match_reasons)),
                    overall_confidence=max(similarity_scores.values())
                ))
                
                processed.update(e.id for e in candidate_entities)
        
        return candidates
    
    async def _calculate_similarity(
        self,
        entity1: Entity,
        entity2: Entity
    ) -> Tuple[float, List[str]]:
        """Calculate similarity between two entities"""
        scores = []
        reasons = []
        
        # Name similarity
        name1 = str(entity1.attributes.get("name", "")).lower()
        name2 = str(entity2.attributes.get("name", "")).lower()
        
        if name1 and name2:
            name_score = fuzz.token_sort_ratio(name1, name2) / 100
            scores.append(name_score)
            
            if name_score >= 0.9:
                reasons.append("name_match")
            elif name_score >= 0.8:
                reasons.append("name_similar")
        
        # ID matching (if from different sources)
        if entity1.source_system != entity2.source_system:
            # Check for cross-referenced IDs
            id1 = entity1.attributes.get("id", entity1.source_id)
            id2 = entity2.attributes.get("id", entity2.source_id)
            
            # Check if IDs reference each other
            if (entity1.attributes.get(f"{entity2.source_system}_id") == id2 or
                entity2.attributes.get(f"{entity1.source_system}_id") == id1):
                scores.append(1.0)
                reasons.append("cross_reference_id")
        
        # Email matching
        email1 = entity1.attributes.get("email", "").lower()
        email2 = entity2.attributes.get("email", "").lower()
        
        if email1 and email2 and email1 == email2:
            scores.append(1.0)
            reasons.append("email_match")
        
        # Domain matching (for customers)
        if entity1.type == EntityType.CUSTOMER:
            domain1 = self._extract_domain(entity1.attributes)
            domain2 = self._extract_domain(entity2.attributes)
            
            if domain1 and domain2 and domain1 == domain2:
                scores.append(0.9)
                reasons.append("domain_match")
        
        # Attribute overlap
        common_attrs = set(entity1.attributes.keys()) & set(entity2.attributes.keys())
        if common_attrs:
            matching_attrs = sum(
                1 for attr in common_attrs
                if entity1.attributes[attr] == entity2.attributes[attr]
            )
            attr_score = matching_attrs / len(common_attrs)
            scores.append(attr_score)
            
            if attr_score >= 0.8:
                reasons.append("high_attribute_match")
        
        # Calculate weighted average
        if scores:
            avg_score = sum(scores) / len(scores)
            
            # Boost score if multiple strong signals
            if len([s for s in scores if s >= 0.9]) >= 2:
                avg_score = min(1.0, avg_score * 1.1)
            
            return avg_score, reasons
        
        return 0.0, []
    
    async def _resolve_candidate_group(
        self,
        candidate: ResolutionCandidate
    ) -> Entity:
        """Resolve a group of candidate entities into one"""
        # Use LLM validation if configured and confidence is medium
        if (self.use_llm_validation and 
            0.7 <= candidate.overall_confidence < 0.95):
            llm_decision = await self._validate_with_llm(candidate)
            if not llm_decision:
                # LLM says they're not duplicates, return highest confidence
                return max(
                    candidate.entities,
                    key=lambda e: e.confidence
                )
        
        # Merge entities based on strategy
        if self.merge_strategy == "most_complete":
            return self._merge_most_complete(candidate.entities)
        elif self.merge_strategy == "most_recent":
            return self._merge_most_recent(candidate.entities)
        elif self.merge_strategy == "weighted":
            return self._merge_weighted(candidate.entities)
        else:
            # Default to first entity
            return candidate.entities[0]
    
    def _merge_most_complete(self, entities: List[Entity]) -> Entity:
        """Merge by selecting attributes from most complete entity"""
        # Sort by number of non-null attributes
        sorted_entities = sorted(
            entities,
            key=lambda e: len([v for v in e.attributes.values() if v is not None]),
            reverse=True
        )
        
        # Start with most complete
        merged = sorted_entities[0]
        
        # Merge others
        for entity in sorted_entities[1:]:
            merged = merged.merge_with(entity)
        
        return merged
    
    def _merge_most_recent(self, entities: List[Entity]) -> Entity:
        """Merge by preferring most recent data"""
        # Sort by extraction timestamp
        sorted_entities = sorted(
            entities,
            key=lambda e: e.extracted_at,
            reverse=True
        )
        
        # Start with most recent
        merged = sorted_entities[0]
        
        # Add missing attributes from older entities
        for entity in sorted_entities[1:]:
            for key, value in entity.attributes.items():
                if key not in merged.attributes or merged.attributes[key] is None:
                    merged.attributes[key] = value
            
            # Merge source IDs
            merged = merged.merge_with(entity)
        
        return merged
    
    def _merge_weighted(self, entities: List[Entity]) -> Entity:
        """Merge with source reliability weighting"""
        # Source reliability weights (could be configurable)
        source_weights = {
            "salesforce": 0.9,
            "gainsight": 0.85,
            "hubspot": 0.8,
            "manual": 0.7,
            "unknown": 0.5
        }
        
        # Sort by source weight
        sorted_entities = sorted(
            entities,
            key=lambda e: source_weights.get(e.source_system, 0.5),
            reverse=True
        )
        
        # Merge similar to most_recent but with weights
        merged = sorted_entities[0]
        
        for entity in sorted_entities[1:]:
            merged = merged.merge_with(entity)
        
        return merged
    
    async def _validate_with_llm(self, candidate: ResolutionCandidate) -> bool:
        """Use LLM to validate if entities are truly duplicates"""
        # This would integrate with an LLM service
        # For now, return True as placeholder
        logger.info(
            f"LLM validation requested for {len(candidate.entities)} entities"
        )
        return True
    
    def _extract_domain(self, attributes: Dict[str, Any]) -> Optional[str]:
        """Extract domain from entity attributes"""
        # Try email
        email = attributes.get("email", "")
        if "@" in email:
            return email.split("@")[1].lower()
        
        # Try website
        website = attributes.get("website", "")
        if website:
            # Simple domain extraction
            domain = website.lower()
            domain = domain.replace("https://", "").replace("http://", "")
            domain = domain.replace("www.", "")
            domain = domain.split("/")[0]
            return domain
        
        return None
    
    def clear_cache(self):
        """Clear resolution cache"""
        self._resolution_cache.clear()