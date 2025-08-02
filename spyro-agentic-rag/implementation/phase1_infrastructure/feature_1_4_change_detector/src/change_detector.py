"""Main change detection implementation"""

import hashlib
import json
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple
import logging

from .models import Change, ChangeType, EntityState, StateSnapshot
from .state_store import StateStore
from .significance_rules import SignificanceEvaluator


logger = logging.getLogger(__name__)


class ChangeDetector:
    """Detects changes in data for incremental updates"""
    
    def __init__(
        self,
        state_store: StateStore,
        significance_evaluator: Optional[SignificanceEvaluator] = None,
        significance_threshold: float = 0.05
    ):
        """Initialize change detector
        
        Args:
            state_store: Store for entity state
            significance_evaluator: Evaluator for change significance
            significance_threshold: Minimum significance to report changes
        """
        self.state_store = state_store
        self.significance_evaluator = significance_evaluator or SignificanceEvaluator()
        self.significance_threshold = significance_threshold
    
    async def detect_changes(
        self,
        entity_type: str,
        new_data: List[Dict[str, Any]],
        id_field: str = "id",
        calculate_significance: bool = True
    ) -> List[Change]:
        """Detect changes by comparing new data with stored state
        
        Args:
            entity_type: Type of entities being compared
            new_data: New data to compare
            id_field: Field name containing entity ID
            calculate_significance: Whether to calculate significance scores
            
        Returns:
            List of detected changes
        """
        # Get current state
        current_snapshot = await self.state_store.get_latest_snapshot(entity_type)
        
        # Create new snapshot
        new_snapshot = self._create_snapshot(entity_type, new_data, id_field)
        
        # Detect changes
        changes = await self._compare_snapshots(
            current_snapshot,
            new_snapshot,
            calculate_significance
        )
        
        # Filter by significance if threshold is set
        if self.significance_threshold > 0:
            changes = [c for c in changes if c.significance >= self.significance_threshold]
        
        # Save new snapshot
        await self.state_store.save_snapshot(new_snapshot)
        
        logger.info(
            f"Detected {len(changes)} changes for {entity_type} "
            f"(threshold: {self.significance_threshold})"
        )
        
        return changes
    
    async def detect_bulk_changes(
        self,
        data_by_type: Dict[str, List[Dict[str, Any]]],
        id_field: str = "id"
    ) -> Dict[str, List[Change]]:
        """Detect changes for multiple entity types
        
        Args:
            data_by_type: Map of entity type to data list
            id_field: Field name containing entity ID
            
        Returns:
            Map of entity type to detected changes
        """
        all_changes = {}
        
        for entity_type, data in data_by_type.items():
            changes = await self.detect_changes(entity_type, data, id_field)
            all_changes[entity_type] = changes
        
        return all_changes
    
    def _create_snapshot(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        id_field: str
    ) -> StateSnapshot:
        """Create a snapshot from data"""
        entities = {}
        timestamp = datetime.now()
        
        for item in data:
            entity_id = item.get(id_field)
            if entity_id is None:
                logger.warning(f"Missing {id_field} in data: {item}")
                continue
            entity_id = str(entity_id)
            
            # Calculate checksum
            checksum = self._calculate_checksum(item)
            
            entities[entity_id] = EntityState(
                entity_type=entity_type,
                entity_id=entity_id,
                data=item,
                last_modified=timestamp,
                checksum=checksum
            )
        
        return StateSnapshot(
            timestamp=timestamp,
            entity_type=entity_type,
            entities=entities,
            metadata={"entity_count": len(entities)}
        )
    
    async def _compare_snapshots(
        self,
        old_snapshot: Optional[StateSnapshot],
        new_snapshot: StateSnapshot,
        calculate_significance: bool
    ) -> List[Change]:
        """Compare two snapshots to find changes"""
        changes = []
        
        if not old_snapshot:
            # All entities are new
            for entity_id, entity_state in new_snapshot.entities.items():
                change = Change(
                    entity_type=new_snapshot.entity_type,
                    entity_id=entity_id,
                    operation=ChangeType.CREATE,
                    fields_changed=list(entity_state.data.keys()),
                    old_values={},
                    new_values=entity_state.data,
                    timestamp=new_snapshot.timestamp
                )
                
                if calculate_significance:
                    change.significance = self.significance_evaluator.evaluate(change)
                
                changes.append(change)
            
            return changes
        
        # Get entity IDs
        old_ids = set(old_snapshot.entities.keys())
        new_ids = set(new_snapshot.entities.keys())
        
        # Find creates (new IDs)
        for entity_id in new_ids - old_ids:
            entity_state = new_snapshot.entities[entity_id]
            change = Change(
                entity_type=new_snapshot.entity_type,
                entity_id=entity_id,
                operation=ChangeType.CREATE,
                fields_changed=list(entity_state.data.keys()),
                old_values={},
                new_values=entity_state.data,
                timestamp=new_snapshot.timestamp
            )
            
            if calculate_significance:
                change.significance = self.significance_evaluator.evaluate(change)
            
            changes.append(change)
        
        # Find deletes (missing IDs)
        for entity_id in old_ids - new_ids:
            old_entity = old_snapshot.entities[entity_id]
            change = Change(
                entity_type=old_snapshot.entity_type,
                entity_id=entity_id,
                operation=ChangeType.DELETE,
                fields_changed=list(old_entity.data.keys()),
                old_values=old_entity.data,
                new_values={},
                timestamp=new_snapshot.timestamp
            )
            
            if calculate_significance:
                change.significance = self.significance_evaluator.evaluate(change)
            
            changes.append(change)
        
        # Find updates (common IDs)
        for entity_id in old_ids & new_ids:
            old_entity = old_snapshot.entities[entity_id]
            new_entity = new_snapshot.entities[entity_id]
            
            # Quick check using checksum
            if old_entity.checksum == new_entity.checksum:
                continue
            
            # Find changed fields
            fields_changed = []
            old_values = {}
            new_values = {}
            
            # Get all fields
            all_fields = set(old_entity.data.keys()) | set(new_entity.data.keys())
            
            for field in all_fields:
                old_value = old_entity.data.get(field)
                new_value = new_entity.data.get(field)
                
                if old_value != new_value:
                    fields_changed.append(field)
                    old_values[field] = old_value
                    new_values[field] = new_value
            
            if fields_changed:
                change = Change(
                    entity_type=new_snapshot.entity_type,
                    entity_id=entity_id,
                    operation=ChangeType.UPDATE,
                    fields_changed=fields_changed,
                    old_values=old_values,
                    new_values=new_values,
                    timestamp=new_snapshot.timestamp,
                    metadata={
                        "old_checksum": old_entity.checksum,
                        "new_checksum": new_entity.checksum
                    }
                )
                
                if calculate_significance:
                    change.significance = self.significance_evaluator.evaluate(change)
                
                changes.append(change)
        
        return changes
    
    def _calculate_checksum(self, data: Dict[str, Any]) -> str:
        """Calculate checksum for data"""
        # Sort keys for consistent ordering
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()
    
    async def get_entity_history(
        self,
        entity_type: str,
        entity_id: str,
        limit: int = 10
    ) -> List[Change]:
        """Get change history for a specific entity
        
        Args:
            entity_type: Type of entity
            entity_id: Entity ID
            limit: Maximum number of changes to return
            
        Returns:
            List of changes for the entity
        """
        # This would require storing changes, not just snapshots
        # For now, we can reconstruct by comparing snapshots
        snapshots = await self.state_store.list_snapshots(entity_type, limit + 1)
        
        if len(snapshots) < 2:
            return []
        
        changes = []
        
        # Compare consecutive snapshots
        for i in range(len(snapshots) - 1):
            newer = snapshots[i]
            older = snapshots[i + 1]
            
            newer_entity = newer.get_entity(entity_id)
            older_entity = older.get_entity(entity_id)
            
            # Skip if entity doesn't exist in either snapshot
            if not newer_entity and not older_entity:
                continue
            
            # Entity created
            if newer_entity and not older_entity:
                change = Change(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=ChangeType.CREATE,
                    fields_changed=list(newer_entity.data.keys()),
                    old_values={},
                    new_values=newer_entity.data,
                    timestamp=newer.timestamp
                )
                changes.append(change)
            
            # Entity deleted
            elif not newer_entity and older_entity:
                change = Change(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=ChangeType.DELETE,
                    fields_changed=list(older_entity.data.keys()),
                    old_values=older_entity.data,
                    new_values={},
                    timestamp=newer.timestamp
                )
                changes.append(change)
            
            # Entity updated
            elif newer_entity and older_entity:
                # Find changed fields
                fields_changed = []
                old_values = {}
                new_values = {}
                
                all_fields = set(older_entity.data.keys()) | set(newer_entity.data.keys())
                
                for field in all_fields:
                    old_value = older_entity.data.get(field)
                    new_value = newer_entity.data.get(field)
                    
                    if old_value != new_value:
                        fields_changed.append(field)
                        old_values[field] = old_value
                        new_values[field] = new_value
                
                if fields_changed:
                    change = Change(
                        entity_type=entity_type,
                        entity_id=entity_id,
                        operation=ChangeType.UPDATE,
                        fields_changed=fields_changed,
                        old_values=old_values,
                        new_values=new_values,
                        timestamp=newer.timestamp
                    )
                    changes.append(change)
            
            if len(changes) >= limit:
                break
        
        # Check if entity exists in the oldest snapshot (means it was created)
        if snapshots and len(changes) < limit:
            oldest_snapshot = snapshots[-1]
            oldest_entity = oldest_snapshot.get_entity(entity_id)
            if oldest_entity:
                # Entity existed in the oldest snapshot, so it was created
                change = Change(
                    entity_type=entity_type,
                    entity_id=entity_id,
                    operation=ChangeType.CREATE,
                    fields_changed=list(oldest_entity.data.keys()),
                    old_values={},
                    new_values=oldest_entity.data,
                    timestamp=oldest_snapshot.timestamp
                )
                changes.append(change)
        
        return changes[:limit]
    
    async def rollback_to_snapshot(
        self,
        entity_type: str,
        target_timestamp: datetime
    ) -> Tuple[int, int]:
        """Rollback to a specific snapshot
        
        Args:
            entity_type: Type of entities to rollback
            target_timestamp: Timestamp to rollback to
            
        Returns:
            Tuple of (entities_restored, snapshots_removed)
        """
        # Find the target snapshot
        snapshots = await self.state_store.list_snapshots(entity_type, limit=100)
        
        target_snapshot = None
        snapshots_to_remove = 0
        
        for i, snapshot in enumerate(snapshots):
            if snapshot.timestamp <= target_timestamp:
                target_snapshot = snapshot
                snapshots_to_remove = i
                break
        
        if not target_snapshot:
            raise ValueError(f"No snapshot found before {target_timestamp}")
        
        # Save the target snapshot as the latest
        target_snapshot.timestamp = datetime.now()
        await self.state_store.save_snapshot(target_snapshot)
        
        # Remove newer snapshots
        removed = await self.state_store.delete_old_snapshots(
            entity_type,
            keep_count=len(snapshots) - snapshots_to_remove
        )
        
        return target_snapshot.entity_count, removed