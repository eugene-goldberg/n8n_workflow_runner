"""Entity type detection from unstructured text"""

import re
import logging
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import asyncio

from .models import EntityType, DetectedEntity, EntityPattern

logger = logging.getLogger(__name__)


class EntityTypeDetector:
    """Detects entity types from unstructured text"""
    
    def __init__(self):
        """Initialize detector with patterns"""
        self.patterns = self._load_default_patterns()
        self._detection_cache = {}
    
    async def detect_entities(
        self,
        text: str,
        entity_types: Optional[List[EntityType]] = None,
        use_llm: bool = False
    ) -> List[DetectedEntity]:
        """Detect entities in text
        
        Args:
            text: Text to analyze
            entity_types: Specific entity types to look for (None = all)
            use_llm: Whether to use LLM for enhanced detection
            
        Returns:
            List of detected entities
        """
        if not text:
            return []
        
        # Check cache
        cache_key = f"{text[:100]}_{entity_types}_{use_llm}"
        if cache_key in self._detection_cache:
            return self._detection_cache[cache_key]
        
        # Pattern-based detection
        detected = await self._pattern_detection(text, entity_types)
        
        # LLM-based detection if enabled
        if use_llm:
            llm_detected = await self._llm_detection(text, entity_types)
            detected = self._merge_detections(detected, llm_detected)
        
        # Post-process and validate
        detected = self._post_process_detections(detected, text)
        
        # Cache results
        self._detection_cache[cache_key] = detected
        
        return detected
    
    async def _pattern_detection(
        self,
        text: str,
        entity_types: Optional[List[EntityType]] = None
    ) -> List[DetectedEntity]:
        """Detect entities using regex patterns"""
        detected = []
        
        # Filter patterns by entity type if specified
        patterns_to_check = self.patterns
        if entity_types:
            patterns_to_check = [
                p for p in patterns_to_check
                if p.entity_type in entity_types
            ]
        
        # Apply each pattern
        for pattern in patterns_to_check:
            if pattern.pattern_type == "regex":
                matches = re.finditer(pattern.pattern, text, re.IGNORECASE)
                for match in matches:
                    # Check context if required
                    if pattern.context_required:
                        if not self._check_context(
                            text, 
                            match.start(), 
                            pattern.context_required
                        ):
                            continue
                    
                    detected.append(DetectedEntity(
                        text=match.group(0),
                        type=pattern.entity_type,
                        start_pos=match.start(),
                        end_pos=match.end(),
                        confidence=pattern.confidence,
                        detection_method="pattern",
                        metadata={"pattern": pattern.pattern}
                    ))
            
            elif pattern.pattern_type == "keyword":
                # Simple keyword matching
                keywords = pattern.pattern.split("|")
                for keyword in keywords:
                    keyword = keyword.strip()
                    start = 0
                    while True:
                        pos = text.lower().find(keyword.lower(), start)
                        if pos == -1:
                            break
                        
                        # Check word boundaries
                        if self._is_word_boundary(text, pos, pos + len(keyword)):
                            detected.append(DetectedEntity(
                                text=text[pos:pos + len(keyword)],
                                type=pattern.entity_type,
                                start_pos=pos,
                                end_pos=pos + len(keyword),
                                confidence=pattern.confidence,
                                detection_method="pattern",
                                metadata={"keyword": keyword}
                            ))
                        
                        start = pos + 1
        
        return detected
    
    async def _llm_detection(
        self,
        text: str,
        entity_types: Optional[List[EntityType]] = None
    ) -> List[DetectedEntity]:
        """Detect entities using LLM"""
        # Placeholder for LLM integration
        # Would call LLM service to identify entities
        logger.info(f"LLM detection requested for text: {text[:50]}...")
        return []
    
    def _merge_detections(
        self,
        detected1: List[DetectedEntity],
        detected2: List[DetectedEntity]
    ) -> List[DetectedEntity]:
        """Merge detections from different methods"""
        # Remove duplicates based on position overlap
        merged = detected1.copy()
        
        for entity2 in detected2:
            # Check if it overlaps with existing detections
            overlap = False
            for entity1 in detected1:
                if (entity1.start_pos <= entity2.start_pos < entity1.end_pos or
                    entity1.start_pos < entity2.end_pos <= entity1.end_pos):
                    # Overlapping - keep higher confidence
                    if entity2.confidence > entity1.confidence:
                        merged.remove(entity1)
                        merged.append(entity2)
                    overlap = True
                    break
            
            if not overlap:
                merged.append(entity2)
        
        return merged
    
    def _post_process_detections(
        self,
        detected: List[DetectedEntity],
        text: str
    ) -> List[DetectedEntity]:
        """Post-process and validate detections"""
        # Remove nested detections (keep longest)
        filtered = []
        
        for entity in detected:
            # Check if it's nested within another detection
            is_nested = False
            for other in detected:
                if (entity != other and
                    other.start_pos <= entity.start_pos and
                    other.end_pos >= entity.end_pos and
                    other.end_pos - other.start_pos > entity.end_pos - entity.start_pos):
                    is_nested = True
                    break
            
            if not is_nested:
                filtered.append(entity)
        
        # Sort by position
        filtered.sort(key=lambda e: e.start_pos)
        
        return filtered
    
    def _check_context(
        self,
        text: str,
        position: int,
        required_context: List[str]
    ) -> bool:
        """Check if required context words are near the position"""
        # Look for context words within 50 characters
        context_window = 50
        start = max(0, position - context_window)
        end = min(len(text), position + context_window)
        
        context_text = text[start:end].lower()
        
        for context_word in required_context:
            if context_word.lower() in context_text:
                return True
        
        return False
    
    def _is_word_boundary(self, text: str, start: int, end: int) -> bool:
        """Check if the match is at word boundaries"""
        # Check start boundary
        if start > 0 and text[start - 1].isalnum():
            return False
        
        # Check end boundary
        if end < len(text) and text[end].isalnum():
            return False
        
        return True
    
    def _load_default_patterns(self) -> List[EntityPattern]:
        """Load default entity detection patterns"""
        return [
            # Customer patterns
            EntityPattern(
                entity_type=EntityType.CUSTOMER,
                pattern=r'\b(?:customer|client|account)\s+([A-Z]\w+(?:\s+[A-Z]\w+)*)',
                pattern_type="regex",
                confidence=0.8
            ),
            EntityPattern(
                entity_type=EntityType.CUSTOMER,
                pattern=r'([A-Z]\w+(?:\s+[A-Z]\w+)*)\s+(?:Inc|Corp|LLC|Ltd|Limited|Company|Co\.?)\b',
                pattern_type="regex",
                confidence=0.9
            ),
            
            # Team patterns
            EntityPattern(
                entity_type=EntityType.TEAM,
                pattern=r'(?:the\s+)?(\w+)\s+(?:team|department|group|division)\b',
                pattern_type="regex",
                confidence=0.85
            ),
            EntityPattern(
                entity_type=EntityType.TEAM,
                pattern="engineering|sales|marketing|support|platform|infrastructure|data|product",
                pattern_type="keyword",
                confidence=0.7,
                context_required=["team", "department", "group"]
            ),
            
            # Product patterns
            EntityPattern(
                entity_type=EntityType.PRODUCT,
                pattern=r'\b(?:product|service|offering|solution)\s+([A-Z]\w+(?:\s+\w+)*)',
                pattern_type="regex",
                confidence=0.75
            ),
            EntityPattern(
                entity_type=EntityType.PRODUCT,
                pattern=r'\b([A-Z]\w+(?:Cloud|Platform|Suite|Pro|Enterprise|Service))\b',
                pattern_type="regex",
                confidence=0.8
            ),
            
            # Risk patterns
            EntityPattern(
                entity_type=EntityType.RISK,
                pattern=r'(?:risk|threat|vulnerability|issue|concern)(?:\s+(?:of|with|regarding))?\s+([^.!?]+)',
                pattern_type="regex",
                confidence=0.8,
                context_required=["identified", "mitigated", "addressed", "high", "critical"]
            ),
            
            # Objective patterns
            EntityPattern(
                entity_type=EntityType.OBJECTIVE,
                pattern=r'(?:objective|goal|target|milestone)\s+(?:to\s+)?([^.!?]+)',
                pattern_type="regex",
                confidence=0.75
            ),
            EntityPattern(
                entity_type=EntityType.OBJECTIVE,
                pattern=r'(?:Q[1-4]|FY\d{2,4})\s+(?:revenue|growth|expansion|retention)',
                pattern_type="regex",
                confidence=0.85
            ),
            
            # Subscription patterns
            EntityPattern(
                entity_type=EntityType.SUBSCRIPTION,
                pattern=r'(?:subscription|contract|agreement)\s+(?:#|ID:?\s*)?([A-Z0-9-]+)',
                pattern_type="regex",
                confidence=0.8
            ),
        ]
    
    def add_pattern(self, pattern: EntityPattern):
        """Add a custom pattern"""
        self.patterns.append(pattern)
        self._detection_cache.clear()
    
    def remove_pattern(self, pattern_text: str):
        """Remove a pattern by its pattern text"""
        self.patterns = [
            p for p in self.patterns
            if p.pattern != pattern_text
        ]
        self._detection_cache.clear()
    
    def clear_cache(self):
        """Clear detection cache"""
        self._detection_cache.clear()