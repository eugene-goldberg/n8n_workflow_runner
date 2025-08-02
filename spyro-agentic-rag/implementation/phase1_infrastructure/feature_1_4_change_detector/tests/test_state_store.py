"""Tests for state storage implementations"""

import pytest
import pytest_asyncio
import tempfile
import os
from datetime import datetime, timedelta
import asyncio

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.state_store import InMemoryStateStore, FileStateStore
from src.models import EntityState, StateSnapshot


class TestInMemoryStateStore:
    """Test cases for in-memory state store"""
    
    @pytest.fixture
    def store(self):
        """Create a fresh store for each test"""
        return InMemoryStateStore()
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_snapshot(self, store):
        """Test saving and retrieving snapshots"""
        # Create snapshot
        entities = {
            "cust_001": EntityState(
                entity_type="Customer",
                entity_id="cust_001",
                data={"name": "Test Customer"},
                last_modified=datetime.now()
            )
        }
        
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Customer",
            entities=entities
        )
        
        # Save snapshot
        await store.save_snapshot(snapshot)
        
        # Retrieve latest
        retrieved = await store.get_latest_snapshot("Customer")
        assert retrieved is not None
        assert retrieved.entity_count == 1
        assert "cust_001" in retrieved.entities
    
    @pytest.mark.asyncio
    async def test_multiple_snapshots(self, store):
        """Test handling multiple snapshots"""
        # Save multiple snapshots
        for i in range(5):
            snapshot = StateSnapshot(
                timestamp=datetime.now() + timedelta(seconds=i),
                entity_type="Customer",
                entities={
                    f"cust_{j:03d}": EntityState(
                        entity_type="Customer",
                        entity_id=f"cust_{j:03d}",
                        data={"name": f"Customer {j}", "version": i},
                        last_modified=datetime.now()
                    )
                    for j in range(i + 1)
                }
            )
            await store.save_snapshot(snapshot)
            await asyncio.sleep(0.01)  # Ensure different timestamps
        
        # Get latest
        latest = await store.get_latest_snapshot("Customer")
        assert latest.entity_count == 5
        
        # List snapshots
        snapshots = await store.list_snapshots("Customer", limit=3)
        assert len(snapshots) == 3
        # Should be ordered newest first
        assert snapshots[0].entity_count > snapshots[1].entity_count
    
    @pytest.mark.asyncio
    async def test_get_entity_state(self, store):
        """Test getting specific entity state"""
        # Save snapshot with multiple entities
        entities = {
            "cust_001": EntityState(
                entity_type="Customer",
                entity_id="cust_001",
                data={"name": "Customer 1"},
                last_modified=datetime.now()
            ),
            "cust_002": EntityState(
                entity_type="Customer",
                entity_id="cust_002",
                data={"name": "Customer 2"},
                last_modified=datetime.now()
            )
        }
        
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Customer",
            entities=entities
        )
        await store.save_snapshot(snapshot)
        
        # Get specific entity
        entity = await store.get_entity_state("Customer", "cust_002")
        assert entity is not None
        assert entity.data["name"] == "Customer 2"
        
        # Non-existing entity
        entity = await store.get_entity_state("Customer", "cust_999")
        assert entity is None
    
    @pytest.mark.asyncio
    async def test_delete_old_snapshots(self, store):
        """Test deleting old snapshots"""
        # Save 10 snapshots
        for i in range(10):
            snapshot = StateSnapshot(
                timestamp=datetime.now() + timedelta(seconds=i),
                entity_type="Customer",
                entities={}
            )
            await store.save_snapshot(snapshot)
        
        # Delete old, keeping 3
        deleted = await store.delete_old_snapshots("Customer", keep_count=3)
        assert deleted == 7
        
        # Verify only 3 remain
        remaining = await store.list_snapshots("Customer", limit=20)
        assert len(remaining) == 3
    
    @pytest.mark.asyncio
    async def test_clear_store(self, store):
        """Test clearing all data"""
        # Save data
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Customer",
            entities={}
        )
        await store.save_snapshot(snapshot)
        
        # Clear
        await store.clear()
        
        # Verify empty
        latest = await store.get_latest_snapshot("Customer")
        assert latest is None


class TestFileStateStore:
    """Test cases for file-based state store"""
    
    @pytest_asyncio.fixture
    async def store(self):
        """Create a temporary file store"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileStateStore(tmpdir)
            yield store
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_snapshot(self, store):
        """Test saving and retrieving snapshots from files"""
        # Create snapshot
        entities = {
            "prod_001": EntityState(
                entity_type="Product",
                entity_id="prod_001",
                data={"name": "Test Product", "price": 99.99},
                last_modified=datetime.now()
            )
        }
        
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Product",
            entities=entities
        )
        
        # Save snapshot
        await store.save_snapshot(snapshot)
        
        # Verify file exists
        entity_dir = os.path.join(store.base_dir, "Product")
        assert os.path.exists(entity_dir)
        files = os.listdir(entity_dir)
        assert len(files) == 1
        assert files[0].startswith("snapshot_")
        
        # Retrieve latest
        retrieved = await store.get_latest_snapshot("Product")
        assert retrieved is not None
        assert retrieved.entity_count == 1
        assert "prod_001" in retrieved.entities
        assert retrieved.entities["prod_001"].data["price"] == 99.99
    
    @pytest.mark.asyncio
    async def test_persistence_across_instances(self, store):
        """Test data persists across store instances"""
        # Save data
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Customer",
            entities={
                "cust_001": EntityState(
                    entity_type="Customer",
                    entity_id="cust_001",
                    data={"name": "Persistent Customer"},
                    last_modified=datetime.now()
                )
            }
        )
        await store.save_snapshot(snapshot)
        
        # Create new store instance with same directory
        new_store = FileStateStore(store.base_dir)
        
        # Retrieve data
        retrieved = await new_store.get_latest_snapshot("Customer")
        assert retrieved is not None
        assert retrieved.entities["cust_001"].data["name"] == "Persistent Customer"
    
    @pytest.mark.asyncio
    async def test_concurrent_access(self, store):
        """Test concurrent snapshot saves"""
        async def save_snapshot(index):
            snapshot = StateSnapshot(
                timestamp=datetime.now() + timedelta(seconds=index),
                entity_type="Customer",
                entities={
                    f"cust_{index}": EntityState(
                        entity_type="Customer",
                        entity_id=f"cust_{index}",
                        data={"index": index},
                        last_modified=datetime.now()
                    )
                }
            )
            await store.save_snapshot(snapshot)
        
        # Save multiple snapshots concurrently
        await asyncio.gather(*[save_snapshot(i) for i in range(5)])
        
        # Verify all saved
        snapshots = await store.list_snapshots("Customer", limit=10)
        assert len(snapshots) == 5
    
    @pytest.mark.asyncio
    async def test_delete_old_snapshots_files(self, store):
        """Test that old snapshot files are actually deleted"""
        # Save multiple snapshots
        for i in range(5):
            snapshot = StateSnapshot(
                timestamp=datetime.now() + timedelta(seconds=i),
                entity_type="Customer",
                entities={}
            )
            await store.save_snapshot(snapshot)
            await asyncio.sleep(0.01)
        
        # Count files before deletion
        entity_dir = os.path.join(store.base_dir, "Customer")
        files_before = len(os.listdir(entity_dir))
        assert files_before == 5
        
        # Delete old snapshots
        deleted = await store.delete_old_snapshots("Customer", keep_count=2)
        assert deleted == 3
        
        # Count files after deletion
        files_after = len(os.listdir(entity_dir))
        assert files_after == 2
    
    @pytest.mark.asyncio
    async def test_clear_removes_files(self, store):
        """Test that clear actually removes all files"""
        # Save data
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Customer",
            entities={}
        )
        await store.save_snapshot(snapshot)
        
        # Verify files exist
        assert os.path.exists(os.path.join(store.base_dir, "Customer"))
        
        # Clear
        await store.clear()
        
        # Verify directory is empty
        assert os.path.exists(store.base_dir)
        assert len(os.listdir(store.base_dir)) == 0