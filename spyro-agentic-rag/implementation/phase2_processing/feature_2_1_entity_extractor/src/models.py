"""Data models for entity extraction"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum
import uuid


class EntityType(str, Enum):
    """Supported entity types"""
    CUSTOMER = "Customer"
    PRODUCT = "Product"
    SUBSCRIPTION = "Subscription"
    TEAM = "Team"
    PROJECT = "Project"
    RISK = "Risk"
    OBJECTIVE = "Objective"
    UNKNOWN = "Unknown"


class ConfidenceLevel(str, Enum):
    """Confidence levels for entity detection/resolution"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class MappingRule:
    """Rule for mapping source field to entity attribute"""
    entity_type: str
    target_field: str
    transformation: Optional[str] = None
    required: bool = True
    default_value: Any = None


@dataclass
class Entity:
    """Represents an extracted entity"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EntityType = EntityType.UNKNOWN
    source_id: Optional[str] = None
    source_system: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0
    extracted_at: datetime = field(default_factory=datetime.now)
    
    # For multi-source resolution
    source_ids: Dict[str, str] = field(default_factory=dict)  # {system: id}
    merged_from: List[str] = field(default_factory=list)  # List of entity IDs
    
    def merge_with(self, other: "Entity") -> "Entity":
        """Merge this entity with another"""
        # Merge attributes (other takes precedence for conflicts)
        merged_attributes = {**self.attributes, **other.attributes}
        
        # Merge source IDs
        merged_source_ids = {**self.source_ids, **other.source_ids}
        if self.source_system and self.source_id:
            merged_source_ids[self.source_system] = self.source_id
        if other.source_system and other.source_id:
            merged_source_ids[other.source_system] = other.source_id
        
        # Track merged entities
        merged_from = list(set(self.merged_from + other.merged_from + [self.id, other.id]))
        
        # Create merged entity
        return Entity(
            type=self.type,
            attributes=merged_attributes,
            source_ids=merged_source_ids,
            merged_from=merged_from,
            confidence=max(self.confidence, other.confidence),
            metadata={
                **self.metadata,
                **other.metadata,
                "merge_timestamp": datetime.now().isoformat()
            }
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary"""
        return {
            "id": self.id,
            "type": self.type.value,
            "source_id": self.source_id,
            "source_system": self.source_system,
            "attributes": self.attributes,
            "metadata": self.metadata,
            "confidence": self.confidence,
            "extracted_at": self.extracted_at.isoformat(),
            "source_ids": self.source_ids,
            "merged_from": self.merged_from
        }


@dataclass
class DetectedEntity:
    """Entity detected from text"""
    text: str
    type: EntityType
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    detection_method: str = "pattern"  # pattern, llm, hybrid
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ValidationError:
    """Represents a validation error"""
    entity_id: str
    field: str
    error_type: str
    message: str
    severity: str = "error"  # error, warning
    suggested_fix: Optional[Any] = None


@dataclass
class ValidationResult:
    """Result of entity validation"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        return len(self.warnings) > 0


@dataclass
class EntityPattern:
    """Pattern for entity detection"""
    entity_type: EntityType
    pattern: str
    pattern_type: str = "regex"  # regex, keyword, phrase
    confidence: float = 0.8
    context_required: List[str] = field(default_factory=list)


@dataclass
class EnrichmentRule:
    """Rule for entity enrichment"""
    entity_type: EntityType
    field_name: str
    rule_type: str  # derived, lookup, conditional
    configuration: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResolutionCandidate:
    """Candidate entities for resolution"""
    entities: List[Entity]
    similarity_scores: Dict[str, float] = field(default_factory=dict)
    match_reasons: List[str] = field(default_factory=list)
    overall_confidence: float = 0.0


@dataclass
class ExtractionContext:
    """Context for entity extraction"""
    source_system: str
    extraction_timestamp: datetime = field(default_factory=datetime.now)
    mapping_rules: Dict[str, MappingRule] = field(default_factory=dict)
    validation_config: Dict[str, Any] = field(default_factory=dict)
    enrichment_config: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)