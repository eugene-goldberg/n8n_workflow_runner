"""Data models for relationship builder"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Set, Tuple
from uuid import uuid4


class RelationshipType(str, Enum):
    """Types of relationships between entities"""
    # Explicit relationships
    BELONGS_TO = "BELONGS_TO"
    MANAGED_BY = "MANAGED_BY"
    ASSIGNED_TO = "ASSIGNED_TO"
    OWNS = "OWNS"
    PARENT_OF = "PARENT_OF"
    CHILD_OF = "CHILD_OF"
    
    # Inferred relationships
    IMPACTS = "IMPACTS"
    COLLABORATES_WITH = "COLLABORATES_WITH"
    INFLUENCES = "INFLUENCES"
    PRECEDES = "PRECEDES"
    FOLLOWS = "FOLLOWS"
    CORRELATES_WITH = "CORRELATES_WITH"
    DEPENDS_ON = "DEPENDS_ON"
    
    # Multi-hop relationships
    INDIRECTLY_AFFECTS = "INDIRECTLY_AFFECTS"
    CASCADES_TO = "CASCADES_TO"
    INFLUENCES_THROUGH = "INFLUENCES_THROUGH"
    CONNECTED_VIA = "CONNECTED_VIA"
    
    # Semantic relationships
    WORKS_WITH = "WORKS_WITH"
    REPORTS_TO = "REPORTS_TO"
    RESPONSIBLE_FOR = "RESPONSIBLE_FOR"
    RELATED_TO = "RELATED_TO"
    
    # Pattern-based relationships
    HUB_OF = "HUB_OF"
    MEMBER_OF_COMMUNITY = "MEMBER_OF_COMMUNITY"
    CENTRAL_TO = "CENTRAL_TO"


class RelationshipDirection(str, Enum):
    """Direction of relationship"""
    UNIDIRECTIONAL = "UNIDIRECTIONAL"
    BIDIRECTIONAL = "BIDIRECTIONAL"


class RelationshipStrength(str, Enum):
    """Strength of relationship"""
    STRONG = "STRONG"
    MODERATE = "MODERATE"
    WEAK = "WEAK"


class TemporalAspect(str, Enum):
    """Temporal aspect of relationship"""
    PAST = "PAST"
    PRESENT = "PRESENT"
    FUTURE = "FUTURE"
    ONGOING = "ONGOING"


@dataclass
class Entity:
    """Simple entity representation for relationship building"""
    id: str
    type: str
    attributes: Dict[str, Any] = field(default_factory=dict)
    source_ids: Dict[str, str] = field(default_factory=dict)
    
    def get_name(self) -> str:
        """Get entity name from attributes"""
        return self.attributes.get("name", self.id)


@dataclass
class Relationship:
    """Represents a relationship between two entities"""
    id: str = field(default_factory=lambda: str(uuid4()))
    source: Entity = None
    target: Entity = None
    relationship_type: RelationshipType = None
    direction: RelationshipDirection = RelationshipDirection.UNIDIRECTIONAL
    strength: RelationshipStrength = RelationshipStrength.MODERATE
    confidence: float = 0.8
    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    discovered_at: datetime = field(default_factory=datetime.now)
    temporal_aspect: Optional[TemporalAspect] = None
    
    # For multi-hop relationships
    path: Optional[List[Entity]] = None
    path_length: Optional[int] = None
    
    def __post_init__(self):
        """Calculate path length if path is provided"""
        if self.path:
            self.path_length = len(self.path)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert relationship to dictionary"""
        return {
            "id": self.id,
            "source_id": self.source.id if self.source else None,
            "source_type": self.source.type if self.source else None,
            "target_id": self.target.id if self.target else None,
            "target_type": self.target.type if self.target else None,
            "relationship_type": self.relationship_type.value if self.relationship_type else None,
            "direction": self.direction.value,
            "strength": self.strength.value,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "discovered_at": self.discovered_at.isoformat(),
            "temporal_aspect": self.temporal_aspect.value if self.temporal_aspect else None,
            "path_length": self.path_length
        }


@dataclass
class PathAnalysis:
    """Analysis of a multi-hop path between entities"""
    path: List[Entity]
    score: float
    interpretation: str
    actionable_insight: Optional[str] = None
    edge_strengths: List[float] = field(default_factory=list)
    bottlenecks: List[Tuple[Entity, Entity]] = field(default_factory=list)
    
    def get_weakest_link(self) -> Optional[Tuple[Entity, Entity]]:
        """Get the weakest link in the path"""
        if not self.edge_strengths or len(self.edge_strengths) < 1:
            return None
        
        min_strength = min(self.edge_strengths)
        min_index = self.edge_strengths.index(min_strength)
        
        if min_index < len(self.path) - 1:
            return (self.path[min_index], self.path[min_index + 1])
        return None


@dataclass
class TemporalCorrelation:
    """Temporal correlation between two entities"""
    entity1: Entity
    entity2: Entity
    correlation_coefficient: float
    optimal_lag_days: int
    causality_score: float
    confidence: float
    time_window_days: int = 90
    events_analyzed: int = 0
    
    def is_causal(self, threshold: float = 0.7) -> bool:
        """Check if correlation is likely causal"""
        return self.causality_score >= threshold
    
    def is_significant(self, threshold: float = 0.6) -> bool:
        """Check if correlation is statistically significant"""
        return abs(self.correlation_coefficient) >= threshold


@dataclass
class GraphPattern:
    """Detected graph pattern"""
    pattern_type: str
    entities: List[Entity]
    centrality_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get_central_entity(self) -> Optional[Entity]:
        """Get the most central entity in the pattern"""
        if not self.centrality_scores:
            return None
        
        max_entity_id = max(self.centrality_scores, key=self.centrality_scores.get)
        return next((e for e in self.entities if e.id == max_entity_id), None)


@dataclass
class CollaborationPattern(GraphPattern):
    """Specific pattern indicating collaboration"""
    collaboration_strength: float = 0.0
    supporting_evidence: List[str] = field(default_factory=list)
    collaboration_type: Optional[str] = None
    
    @property
    def indicates_collaboration(self) -> bool:
        """Check if pattern indicates collaboration"""
        return self.collaboration_strength > 0.5


@dataclass
class RelationshipRule:
    """Rule for explicit relationship detection"""
    source_type: str
    field: str
    target_type: str
    relationship: RelationshipType
    bidirectional: bool = False
    required: bool = True
    
    def matches(self, entity: Entity) -> bool:
        """Check if rule matches entity"""
        return (entity.type == self.source_type and 
                self.field in entity.attributes and
                entity.attributes[self.field] is not None)


@dataclass
class RelationshipDiscoveryContext:
    """Context for relationship discovery"""
    business_context: Optional[str] = None
    time_range: Optional[Tuple[datetime, datetime]] = None
    focus_entities: Optional[Set[str]] = None
    exclude_types: Set[RelationshipType] = field(default_factory=set)
    min_confidence: float = 0.5
    enable_llm: bool = True
    
    def should_include_relationship(self, rel: Relationship) -> bool:
        """Check if relationship should be included based on context"""
        if rel.confidence < self.min_confidence:
            return False
        
        if rel.relationship_type in self.exclude_types:
            return False
        
        if self.focus_entities:
            entity_ids = {rel.source.id, rel.target.id}
            if not entity_ids.intersection(self.focus_entities):
                return False
        
        return True


@dataclass
class Event:
    """Event for temporal analysis"""
    entity_id: str
    event_type: str
    timestamp: datetime
    value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def days_between(self, other: "Event") -> int:
        """Calculate days between events"""
        delta = abs(self.timestamp - other.timestamp)
        return delta.days


@dataclass
class EntityMention:
    """Entity mention in text"""
    entity_id: str
    entity_type: str
    surface_form: str
    start_pos: int
    end_pos: int
    confidence: float = 1.0
    
    @property
    def span(self) -> Tuple[int, int]:
        """Get mention span"""
        return (self.start_pos, self.end_pos)