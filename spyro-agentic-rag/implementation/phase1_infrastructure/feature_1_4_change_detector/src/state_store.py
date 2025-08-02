"""State storage implementations for change detection"""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, List
import asyncio
import aiofiles
import orjson

from .models import EntityState, StateSnapshot


class StateStore(ABC):
    """Abstract base class for state storage"""
    
    @abstractmethod
    async def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """Save a state snapshot"""
        pass
    
    @abstractmethod
    async def get_latest_snapshot(self, entity_type: str) -> Optional[StateSnapshot]:
        """Get the most recent snapshot for an entity type"""
        pass
    
    @abstractmethod
    async def get_entity_state(self, entity_type: str, entity_id: str) -> Optional[EntityState]:
        """Get state for a specific entity"""
        pass
    
    @abstractmethod
    async def list_snapshots(self, entity_type: str, limit: int = 10) -> List[StateSnapshot]:
        """List available snapshots for an entity type"""
        pass
    
    @abstractmethod
    async def delete_old_snapshots(self, entity_type: str, keep_count: int = 5) -> int:
        """Delete old snapshots, keeping the most recent ones"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Clear all stored state"""
        pass


class InMemoryStateStore(StateStore):
    """In-memory state storage for testing and development"""
    
    def __init__(self):
        """Initialize in-memory store"""
        self._snapshots: Dict[str, List[StateSnapshot]] = {}  # entity_type -> [snapshots]
        self._lock = asyncio.Lock()
    
    async def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """Save a state snapshot"""
        async with self._lock:
            if snapshot.entity_type not in self._snapshots:
                self._snapshots[snapshot.entity_type] = []
            
            self._snapshots[snapshot.entity_type].append(snapshot)
            
            # Sort by timestamp
            self._snapshots[snapshot.entity_type].sort(
                key=lambda s: s.timestamp, 
                reverse=True
            )
    
    async def get_latest_snapshot(self, entity_type: str) -> Optional[StateSnapshot]:
        """Get the most recent snapshot for an entity type"""
        async with self._lock:
            snapshots = self._snapshots.get(entity_type, [])
            return snapshots[0] if snapshots else None
    
    async def get_entity_state(self, entity_type: str, entity_id: str) -> Optional[EntityState]:
        """Get state for a specific entity"""
        snapshot = await self.get_latest_snapshot(entity_type)
        if snapshot:
            return snapshot.get_entity(entity_id)
        return None
    
    async def list_snapshots(self, entity_type: str, limit: int = 10) -> List[StateSnapshot]:
        """List available snapshots for an entity type"""
        async with self._lock:
            snapshots = self._snapshots.get(entity_type, [])
            return snapshots[:limit]
    
    async def delete_old_snapshots(self, entity_type: str, keep_count: int = 5) -> int:
        """Delete old snapshots, keeping the most recent ones"""
        async with self._lock:
            if entity_type not in self._snapshots:
                return 0
            
            snapshots = self._snapshots[entity_type]
            if len(snapshots) <= keep_count:
                return 0
            
            deleted_count = len(snapshots) - keep_count
            self._snapshots[entity_type] = snapshots[:keep_count]
            return deleted_count
    
    async def clear(self) -> None:
        """Clear all stored state"""
        async with self._lock:
            self._snapshots.clear()


class FileStateStore(StateStore):
    """File-based persistent state storage"""
    
    def __init__(self, base_dir: str):
        """Initialize file-based store
        
        Args:
            base_dir: Base directory for storing state files
        """
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)
        self._lock = asyncio.Lock()
    
    def _get_entity_dir(self, entity_type: str) -> str:
        """Get directory for entity type"""
        path = os.path.join(self.base_dir, entity_type)
        os.makedirs(path, exist_ok=True)
        return path
    
    def _get_snapshot_filename(self, timestamp: datetime) -> str:
        """Get filename for snapshot"""
        return f"snapshot_{timestamp.strftime('%Y%m%d_%H%M%S_%f')}.json"
    
    async def save_snapshot(self, snapshot: StateSnapshot) -> None:
        """Save a state snapshot"""
        async with self._lock:
            entity_dir = self._get_entity_dir(snapshot.entity_type)
            filename = self._get_snapshot_filename(snapshot.timestamp)
            filepath = os.path.join(entity_dir, filename)
            
            # Use orjson for fast serialization
            data = orjson.dumps(snapshot.to_dict())
            
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(data)
    
    async def get_latest_snapshot(self, entity_type: str) -> Optional[StateSnapshot]:
        """Get the most recent snapshot for an entity type"""
        snapshots = await self.list_snapshots(entity_type, limit=1)
        return snapshots[0] if snapshots else None
    
    async def get_entity_state(self, entity_type: str, entity_id: str) -> Optional[EntityState]:
        """Get state for a specific entity"""
        snapshot = await self.get_latest_snapshot(entity_type)
        if snapshot:
            return snapshot.get_entity(entity_id)
        return None
    
    async def list_snapshots(self, entity_type: str, limit: int = 10) -> List[StateSnapshot]:
        """List available snapshots for an entity type"""
        async with self._lock:
            entity_dir = self._get_entity_dir(entity_type)
            
            # Get all snapshot files
            files = []
            for filename in os.listdir(entity_dir):
                if filename.startswith("snapshot_") and filename.endswith(".json"):
                    files.append(filename)
            
            # Sort by filename (which includes timestamp)
            files.sort(reverse=True)
            
            # Load snapshots
            snapshots = []
            for filename in files[:limit]:
                filepath = os.path.join(entity_dir, filename)
                
                async with aiofiles.open(filepath, 'rb') as f:
                    data = await f.read()
                    snapshot_dict = orjson.loads(data)
                    snapshots.append(StateSnapshot.from_dict(snapshot_dict))
            
            return snapshots
    
    async def delete_old_snapshots(self, entity_type: str, keep_count: int = 5) -> int:
        """Delete old snapshots, keeping the most recent ones"""
        async with self._lock:
            entity_dir = self._get_entity_dir(entity_type)
            
            # Get all snapshot files
            files = []
            for filename in os.listdir(entity_dir):
                if filename.startswith("snapshot_") and filename.endswith(".json"):
                    files.append(filename)
            
            # Sort by filename (newest first)
            files.sort(reverse=True)
            
            # Delete old files
            deleted_count = 0
            for filename in files[keep_count:]:
                filepath = os.path.join(entity_dir, filename)
                os.remove(filepath)
                deleted_count += 1
            
            return deleted_count
    
    async def clear(self) -> None:
        """Clear all stored state"""
        async with self._lock:
            # Remove all files and directories
            import shutil
            if os.path.exists(self.base_dir):
                shutil.rmtree(self.base_dir)
                os.makedirs(self.base_dir, exist_ok=True)