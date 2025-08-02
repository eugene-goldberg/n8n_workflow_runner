"""Data models for change detection"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum


class ChangeType(Enum):
    """Types of changes that can be detected"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class ChangeSignificance(Enum):
    """Significance levels for changes"""
    TRIVIAL = "trivial"      # < 0.1
    LOW = "low"              # 0.1 - 0.3
    MEDIUM = "medium"        # 0.3 - 0.7
    HIGH = "high"            # 0.7 - 0.9
    CRITICAL = "critical"    # > 0.9


@dataclass
class Change:
    """Represents a detected change in data"""
    entity_type: str
    entity_id: str
    operation: ChangeType
    fields_changed: List[str] = field(default_factory=list)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    significance: float = 0.5
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def significance_level(self) -> ChangeSignificance:
        """Get significance level based on score"""
        if self.significance < 0.1:
            return ChangeSignificance.TRIVIAL
        elif self.significance < 0.3:
            return ChangeSignificance.LOW
        elif self.significance < 0.7:
            return ChangeSignificance.MEDIUM
        elif self.significance < 0.9:
            return ChangeSignificance.HIGH
        else:
            return ChangeSignificance.CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "operation": self.operation.value,
            "fields_changed": self.fields_changed,
            "old_values": self.old_values,
            "new_values": self.new_values,
            "timestamp": self.timestamp.isoformat(),
            "significance": self.significance,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Change':
        """Create from dictionary"""
        return cls(
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            operation=ChangeType(data["operation"]),
            fields_changed=data.get("fields_changed", []),
            old_values=data.get("old_values", {}),
            new_values=data.get("new_values", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            significance=data.get("significance", 0.5),
            metadata=data.get("metadata", {})
        )


@dataclass
class EntityState:
    """Represents the state of an entity at a point in time"""
    entity_type: str
    entity_id: str
    data: Dict[str, Any]
    last_modified: datetime
    version: int = 1
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "data": self.data,
            "last_modified": self.last_modified.isoformat(),
            "version": self.version,
            "checksum": self.checksum
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EntityState':
        """Create from dictionary"""
        return cls(
            entity_type=data["entity_type"],
            entity_id=data["entity_id"],
            data=data["data"],
            last_modified=datetime.fromisoformat(data["last_modified"]),
            version=data.get("version", 1),
            checksum=data.get("checksum")
        )


@dataclass
class StateSnapshot:
    """Snapshot of all entities at a point in time"""
    timestamp: datetime
    entity_type: str
    entities: Dict[str, EntityState]  # entity_id -> EntityState
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def entity_count(self) -> int:
        """Get number of entities in snapshot"""
        return len(self.entities)
    
    def get_entity(self, entity_id: str) -> Optional[EntityState]:
        """Get entity by ID"""
        return self.entities.get(entity_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "entity_type": self.entity_type,
            "entities": {
                eid: estate.to_dict() 
                for eid, estate in self.entities.items()
            },
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StateSnapshot':
        """Create from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            entity_type=data["entity_type"],
            entities={
                eid: EntityState.from_dict(estate_data)
                for eid, estate_data in data["entities"].items()
            },
            metadata=data.get("metadata", {})
        )