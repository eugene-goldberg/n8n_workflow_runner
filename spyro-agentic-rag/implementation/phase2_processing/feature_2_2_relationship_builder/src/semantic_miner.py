"""Semantic relationship mining from text"""

import asyncio
import logging
import re
from collections import defaultdict
from typing import Dict, List, Optional, Set, Tuple, Any
import spacy
from spacy.matcher import Matcher

from .models import (
    Entity,
    EntityMention,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    TemporalAspect,
    RelationshipDiscoveryContext
)

logger = logging.getLogger(__name__)


class SemanticRelationshipMiner:
    """Extract relationships from text using NLP"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize semantic miner
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._get_default_config()
        self._nlp = None
        self._matcher = None
        self._relationship_patterns = self._load_relationship_patterns()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "spacy_model": "en_core_web_sm",
            "confidence_threshold": 0.7,
            "llm_enabled": True,
            "llm_model": "gpt-4",
            "batch_size": 10,
            "context_window": 50,  # chars around entity mention
            "relationship_patterns": {
                "enable_pattern_matching": True,
                "enable_dependency_parsing": True,
                "enable_llm_extraction": True
            },
            "performance": {
                "max_text_length": 10000,
                "cache_extractions": True
            }
        }
    
    @property
    def nlp(self):
        """Lazy load spaCy model"""
        if self._nlp is None:
            try:
                self._nlp = spacy.load(self.config["spacy_model"])
            except OSError:
                logger.warning(f"Model {self.config['spacy_model']} not found, using default")
                self._nlp = spacy.blank("en")
            
            # Add entity ruler for better entity recognition
            if "entity_ruler" not in self._nlp.pipe_names:
                ruler = self._nlp.add_pipe("entity_ruler", before="ner")
        
        return self._nlp
    
    def _load_relationship_patterns(self) -> List[Dict[str, Any]]:
        """Load relationship extraction patterns"""
        return [
            # Work relationships
            {
                "pattern": r"(\w+)\s+(works?\s+with|collaborates?\s+with)\s+(\w+)",
                "type": RelationshipType.WORKS_WITH,
                "bidirectional": True
            },
            {
                "pattern": r"(\w+)\s+(manages?|leads?|supervises?)\s+(\w+)",
                "type": RelationshipType.MANAGES,
                "bidirectional": False
            },
            {
                "pattern": r"(\w+)\s+(reports?\s+to|works?\s+for)\s+(\w+)",
                "type": RelationshipType.REPORTS_TO,
                "bidirectional": False
            },
            
            # Responsibility relationships
            {
                "pattern": r"(\w+)\s+(?:is\s+)?responsible\s+for\s+(\w+)",
                "type": RelationshipType.RESPONSIBLE_FOR,
                "bidirectional": False
            },
            {
                "pattern": r"(\w+)\s+owns?\s+(\w+)",
                "type": RelationshipType.OWNS,
                "bidirectional": False
            },
            
            # Impact relationships
            {
                "pattern": r"(\w+)\s+(impacts?|affects?|influences?)\s+(\w+)",
                "type": RelationshipType.IMPACTS,
                "bidirectional": False
            },
            {
                "pattern": r"(\w+)\s+(depends?\s+on|relies?\s+on)\s+(\w+)",
                "type": RelationshipType.DEPENDS_ON,
                "bidirectional": False
            },
            
            # General relationships
            {
                "pattern": r"(\w+)\s+(?:is\s+)?(?:related|connected)\s+to\s+(\w+)",
                "type": RelationshipType.RELATED_TO,
                "bidirectional": True
            }
        ]
    
    async def mine_from_text(
        self,
        text: str,
        entities: List[Entity],
        document_metadata: Optional[Dict[str, Any]] = None,
        context: Optional[RelationshipDiscoveryContext] = None
    ) -> List[Relationship]:
        """Extract relationships from text
        
        Args:
            text: Text to analyze
            entities: Known entities to look for
            document_metadata: Optional document metadata
            context: Optional discovery context
            
        Returns:
            List of discovered relationships
        """
        if not text or not entities:
            return []
        
        context = context or RelationshipDiscoveryContext()
        
        # Truncate text if too long
        if len(text) > self.config["performance"]["max_text_length"]:
            text = text[:self.config["performance"]["max_text_length"]]
        
        # Find entity mentions in text
        mentions = await self._find_entity_mentions(text, entities)
        
        if len(mentions) < 2:
            return []  # Need at least 2 entities for relationships
        
        relationships = []
        
        # Use different extraction methods
        if self.config["relationship_patterns"]["enable_pattern_matching"]:
            pattern_rels = await self._extract_pattern_relationships(text, mentions)
            relationships.extend(pattern_rels)
        
        if self.config["relationship_patterns"]["enable_dependency_parsing"]:
            dep_rels = await self._extract_dependency_relationships(text, mentions)
            relationships.extend(dep_rels)
        
        if self.config["relationship_patterns"]["enable_llm_extraction"] and context.enable_llm:
            llm_rels = await self._extract_llm_relationships(text, mentions)
            relationships.extend(llm_rels)
        
        # Deduplicate and filter
        relationships = self._deduplicate_relationships(relationships)
        relationships = [
            rel for rel in relationships
            if rel.confidence >= self.config["confidence_threshold"]
            and context.should_include_relationship(rel)
        ]
        
        # Add document metadata
        if document_metadata:
            for rel in relationships:
                rel.metadata["document"] = document_metadata
        
        return relationships
    
    async def _find_entity_mentions(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[EntityMention]:
        """Find entity mentions in text"""
        mentions = []
        
        # Create entity lookup
        entity_lookup = {}
        for entity in entities:
            # Add entity name variations
            name = entity.get_name()
            entity_lookup[name.lower()] = entity
            
            # Add common variations
            if " " in name:
                # Add acronym
                acronym = "".join(word[0].upper() for word in name.split())
                entity_lookup[acronym.lower()] = entity
                
                # Add last word (common for companies)
                last_word = name.split()[-1]
                if len(last_word) > 3:
                    entity_lookup[last_word.lower()] = entity
        
        # Process text with spaCy
        doc = self.nlp(text.lower())
        
        # Find mentions using exact matching
        for token in doc:
            if token.text in entity_lookup:
                entity = entity_lookup[token.text]
                mention = EntityMention(
                    entity_id=entity.id,
                    entity_type=entity.type,
                    surface_form=token.text,
                    start_pos=token.idx,
                    end_pos=token.idx + len(token.text),
                    confidence=1.0
                )
                mentions.append(mention)
        
        # Find mentions using noun phrases
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.strip()
            if chunk_text in entity_lookup:
                entity = entity_lookup[chunk_text]
                mention = EntityMention(
                    entity_id=entity.id,
                    entity_type=entity.type,
                    surface_form=chunk.text,
                    start_pos=chunk.start_char,
                    end_pos=chunk.end_char,
                    confidence=0.9
                )
                mentions.append(mention)
        
        # Deduplicate overlapping mentions
        mentions = self._deduplicate_mentions(mentions)
        
        return mentions
    
    def _deduplicate_mentions(self, mentions: List[EntityMention]) -> List[EntityMention]:
        """Remove overlapping entity mentions"""
        if not mentions:
            return mentions
        
        # Sort by start position
        mentions.sort(key=lambda m: (m.start_pos, -m.confidence))
        
        deduped = []
        last_end = -1
        
        for mention in mentions:
            if mention.start_pos >= last_end:
                deduped.append(mention)
                last_end = mention.end_pos
        
        return deduped
    
    async def _extract_pattern_relationships(
        self,
        text: str,
        mentions: List[EntityMention]
    ) -> List[Relationship]:
        """Extract relationships using regex patterns"""
        relationships = []
        
        # Create mention position index
        mention_by_pos = {}
        for mention in mentions:
            for pos in range(mention.start_pos, mention.end_pos):
                mention_by_pos[pos] = mention
        
        # Apply each pattern
        for pattern_def in self._relationship_patterns:
            pattern = pattern_def["pattern"]
            rel_type = pattern_def["type"]
            bidirectional = pattern_def["bidirectional"]
            
            # Find matches
            for match in re.finditer(pattern, text, re.IGNORECASE):
                # Check if match positions correspond to entity mentions
                source_start = match.start(1)
                target_start = match.start(3) if len(match.groups()) >= 3 else match.start(2)
                
                source_mention = mention_by_pos.get(source_start)
                target_mention = mention_by_pos.get(target_start)
                
                if source_mention and target_mention and source_mention != target_mention:
                    # Get entities
                    source_entity = self._get_entity_by_id(source_mention.entity_id, mentions)
                    target_entity = self._get_entity_by_id(target_mention.entity_id, mentions)
                    
                    if source_entity and target_entity:
                        rel = Relationship(
                            source=source_entity,
                            target=target_entity,
                            relationship_type=rel_type,
                            direction=(RelationshipDirection.BIDIRECTIONAL 
                                     if bidirectional 
                                     else RelationshipDirection.UNIDIRECTIONAL),
                            strength=RelationshipStrength.MODERATE,
                            confidence=0.8,
                            evidence=[f"Pattern match: '{match.group()}'"],
                            temporal_aspect=TemporalAspect.PRESENT
                        )
                        relationships.append(rel)
        
        return relationships
    
    async def _extract_dependency_relationships(
        self,
        text: str,
        mentions: List[EntityMention]
    ) -> List[Relationship]:
        """Extract relationships using dependency parsing"""
        relationships = []
        
        # Process text with spaCy
        doc = self.nlp(text)
        
        # Create mention token mapping
        mention_tokens = {}
        for mention in mentions:
            for token in doc:
                if (token.idx >= mention.start_pos and 
                    token.idx < mention.end_pos):
                    mention_tokens[token.i] = mention
        
        # Look for dependency patterns
        for token in doc:
            if token.i not in mention_tokens:
                continue
            
            source_mention = mention_tokens[token.i]
            
            # Check dependencies
            for child in token.children:
                if child.i in mention_tokens:
                    target_mention = mention_tokens[child.i]
                    
                    # Determine relationship based on dependency
                    rel_type = self._dep_to_relationship_type(token, child)
                    if rel_type:
                        source_entity = self._get_entity_by_id(source_mention.entity_id, mentions)
                        target_entity = self._get_entity_by_id(target_mention.entity_id, mentions)
                        
                        if source_entity and target_entity:
                            rel = Relationship(
                                source=source_entity,
                                target=target_entity,
                                relationship_type=rel_type,
                                direction=RelationshipDirection.UNIDIRECTIONAL,
                                strength=RelationshipStrength.MODERATE,
                                confidence=0.7,
                                evidence=[
                                    f"Dependency: {token.text} -{child.dep_}-> {child.text}"
                                ],
                                temporal_aspect=TemporalAspect.PRESENT
                            )
                            relationships.append(rel)
        
        return relationships
    
    def _dep_to_relationship_type(
        self,
        head: Any,
        child: Any
    ) -> Optional[RelationshipType]:
        """Map dependency relation to relationship type"""
        dep = child.dep_
        
        # Subject-verb-object patterns
        if dep in ["dobj", "pobj"] and head.pos_ == "VERB":
            verb_lemma = head.lemma_.lower()
            
            if verb_lemma in ["manage", "lead", "supervise"]:
                return RelationshipType.MANAGES
            elif verb_lemma in ["report", "work"]:
                return RelationshipType.REPORTS_TO
            elif verb_lemma in ["own", "possess"]:
                return RelationshipType.OWNS
            elif verb_lemma in ["impact", "affect", "influence"]:
                return RelationshipType.IMPACTS
            elif verb_lemma in ["depend", "rely"]:
                return RelationshipType.DEPENDS_ON
        
        # Prepositional patterns
        elif dep == "prep" and head.pos_ in ["NOUN", "PROPN"]:
            prep_text = child.text.lower()
            if prep_text in ["with", "alongside"]:
                return RelationshipType.COLLABORATES_WITH
            elif prep_text == "under":
                return RelationshipType.REPORTS_TO
            elif prep_text == "for":
                return RelationshipType.RESPONSIBLE_FOR
        
        return None
    
    async def _extract_llm_relationships(
        self,
        text: str,
        mentions: List[EntityMention]
    ) -> List[Relationship]:
        """Extract relationships using LLM"""
        # Placeholder for LLM integration
        # This would typically call an LLM API to extract relationships
        relationships = []
        
        if not self.config["llm_enabled"]:
            return relationships
        
        # For now, return empty list
        # TODO: Implement LLM extraction when LLM service is available
        logger.info("LLM relationship extraction not yet implemented")
        
        return relationships
    
    def _deduplicate_relationships(
        self,
        relationships: List[Relationship]
    ) -> List[Relationship]:
        """Deduplicate relationships"""
        seen = set()
        deduped = []
        
        for rel in relationships:
            key = (
                rel.source.id,
                rel.target.id,
                rel.relationship_type.value
            )
            
            if key not in seen:
                seen.add(key)
                deduped.append(rel)
            else:
                # Merge evidence
                for existing in deduped:
                    if (existing.source.id == rel.source.id and
                        existing.target.id == rel.target.id and
                        existing.relationship_type == rel.relationship_type):
                        existing.evidence.extend(rel.evidence)
                        existing.confidence = max(existing.confidence, rel.confidence)
                        break
        
        return deduped
    
    def _get_entity_by_id(
        self,
        entity_id: str,
        mentions: List[EntityMention]
    ) -> Optional[Entity]:
        """Get entity by ID from mentions"""
        # This is a placeholder - in real implementation,
        # we'd have an entity lookup or pass entities with mentions
        # For now, create a simple entity
        mention = next((m for m in mentions if m.entity_id == entity_id), None)
        if mention:
            return Entity(
                id=entity_id,
                type=mention.entity_type,
                attributes={"name": mention.surface_form}
            )
        return None
    
    async def extract_from_documents(
        self,
        documents: List[Dict[str, Any]],
        entities: List[Entity],
        context: Optional[RelationshipDiscoveryContext] = None
    ) -> List[Relationship]:
        """Extract relationships from multiple documents
        
        Args:
            documents: List of documents with 'text' and optional metadata
            entities: Known entities
            context: Optional discovery context
            
        Returns:
            List of discovered relationships
        """
        all_relationships = []
        
        # Process documents in batches
        batch_size = self.config["batch_size"]
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Extract from each document in parallel
            tasks = []
            for doc in batch:
                text = doc.get("text", "")
                metadata = {k: v for k, v in doc.items() if k != "text"}
                
                task = self.mine_from_text(text, entities, metadata, context)
                tasks.append(task)
            
            batch_relationships = await asyncio.gather(*tasks)
            for relationships in batch_relationships:
                all_relationships.extend(relationships)
        
        return all_relationships
    
    def get_relationship_context(
        self,
        text: str,
        relationship: Relationship,
        mentions: List[EntityMention]
    ) -> str:
        """Get text context around a relationship
        
        Args:
            text: Original text
            relationship: Relationship to get context for
            mentions: Entity mentions in text
            
        Returns:
            Context string
        """
        # Find mentions for source and target
        source_mentions = [
            m for m in mentions 
            if m.entity_id == relationship.source.id
        ]
        target_mentions = [
            m for m in mentions
            if m.entity_id == relationship.target.id
        ]
        
        if not source_mentions or not target_mentions:
            return ""
        
        # Find closest mentions
        min_distance = float('inf')
        best_source = None
        best_target = None
        
        for s_mention in source_mentions:
            for t_mention in target_mentions:
                distance = abs(s_mention.start_pos - t_mention.start_pos)
                if distance < min_distance:
                    min_distance = distance
                    best_source = s_mention
                    best_target = t_mention
        
        if not best_source or not best_target:
            return ""
        
        # Extract context
        context_start = max(
            0,
            min(best_source.start_pos, best_target.start_pos) - self.config["context_window"]
        )
        context_end = min(
            len(text),
            max(best_source.end_pos, best_target.end_pos) + self.config["context_window"]
        )
        
        return text[context_start:context_end]