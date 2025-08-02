"""Tests for change detector"""

import pytest
from datetime import datetime, timedelta
from freezegun import freeze_time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.change_detector import ChangeDetector
from src.state_store import InMemoryStateStore
from src.models import Change, ChangeType
from src.significance_rules import SignificanceEvaluator


class TestChangeDetector:
    """Test cases for ChangeDetector"""
    
    @pytest.fixture
    def detector(self):
        """Create change detector with in-memory store"""
        store = InMemoryStateStore()
        return ChangeDetector(store, significance_threshold=0.0)
    
    @pytest.mark.asyncio
    async def test_detect_creates(self, detector):
        """Test detecting new entities"""
        # First run with initial data
        initial_data = [
            {"id": "cust_001", "name": "Customer 1", "status": "active"},
            {"id": "cust_002", "name": "Customer 2", "status": "active"}
        ]
        
        changes = await detector.detect_changes("Customer", initial_data)
        
        # All should be creates
        assert len(changes) == 2
        assert all(c.operation == ChangeType.CREATE for c in changes)
        assert changes[0].entity_id == "cust_001"
        assert changes[0].new_values["name"] == "Customer 1"
    
    @pytest.mark.asyncio
    async def test_detect_updates(self, detector):
        """Test detecting updates to existing entities"""
        # Initial data
        initial_data = [
            {"id": "cust_001", "name": "Customer 1", "status": "active"},
            {"id": "cust_002", "name": "Customer 2", "status": "active"}
        ]
        await detector.detect_changes("Customer", initial_data)
        
        # Updated data
        updated_data = [
            {"id": "cust_001", "name": "Customer 1 Updated", "status": "active"},
            {"id": "cust_002", "name": "Customer 2", "status": "inactive"}
        ]
        
        changes = await detector.detect_changes("Customer", updated_data)
        
        # Should detect 2 updates
        assert len(changes) == 2
        assert all(c.operation == ChangeType.UPDATE for c in changes)
        
        # Check first update
        change1 = next(c for c in changes if c.entity_id == "cust_001")
        assert "name" in change1.fields_changed
        assert change1.old_values["name"] == "Customer 1"
        assert change1.new_values["name"] == "Customer 1 Updated"
        
        # Check second update
        change2 = next(c for c in changes if c.entity_id == "cust_002")
        assert "status" in change2.fields_changed
        assert change2.old_values["status"] == "active"
        assert change2.new_values["status"] == "inactive"
    
    @pytest.mark.asyncio
    async def test_detect_deletes(self, detector):
        """Test detecting deleted entities"""
        # Initial data
        initial_data = [
            {"id": "cust_001", "name": "Customer 1"},
            {"id": "cust_002", "name": "Customer 2"},
            {"id": "cust_003", "name": "Customer 3"}
        ]
        await detector.detect_changes("Customer", initial_data)
        
        # Remove one entity
        updated_data = [
            {"id": "cust_001", "name": "Customer 1"},
            {"id": "cust_003", "name": "Customer 3"}
        ]
        
        changes = await detector.detect_changes("Customer", updated_data)
        
        # Should detect 1 delete
        assert len(changes) == 1
        assert changes[0].operation == ChangeType.DELETE
        assert changes[0].entity_id == "cust_002"
        assert changes[0].old_values["name"] == "Customer 2"
    
    @pytest.mark.asyncio
    async def test_mixed_changes(self, detector):
        """Test detecting mixed create/update/delete"""
        # Initial data
        initial_data = [
            {"id": "1", "name": "Entity 1"},
            {"id": "2", "name": "Entity 2"}
        ]
        await detector.detect_changes("Entity", initial_data)
        
        # Mixed changes
        updated_data = [
            {"id": "1", "name": "Entity 1 Updated"},  # Update
            {"id": "3", "name": "Entity 3"}           # Create
            # Entity 2 deleted
        ]
        
        changes = await detector.detect_changes("Entity", updated_data)
        
        assert len(changes) == 3
        
        # Check each type
        creates = [c for c in changes if c.operation == ChangeType.CREATE]
        updates = [c for c in changes if c.operation == ChangeType.UPDATE]
        deletes = [c for c in changes if c.operation == ChangeType.DELETE]
        
        assert len(creates) == 1
        assert creates[0].entity_id == "3"
        
        assert len(updates) == 1
        assert updates[0].entity_id == "1"
        
        assert len(deletes) == 1
        assert deletes[0].entity_id == "2"
    
    @pytest.mark.asyncio
    async def test_no_changes(self, detector):
        """Test when no changes occur"""
        # Initial data
        data = [
            {"id": "1", "name": "Entity 1", "value": 100},
            {"id": "2", "name": "Entity 2", "value": 200}
        ]
        await detector.detect_changes("Entity", data)
        
        # Same data again
        changes = await detector.detect_changes("Entity", data)
        
        assert len(changes) == 0
    
    @pytest.mark.asyncio
    async def test_significance_filtering(self):
        """Test filtering by significance threshold"""
        store = InMemoryStateStore()
        detector = ChangeDetector(store, significance_threshold=0.7)
        
        # Initial data
        initial_data = [
            {"id": "1", "name": "Customer", "status": "active", "score": 100}
        ]
        await detector.detect_changes("Customer", initial_data)
        
        # Update with mixed significance
        updated_data = [
            {"id": "1", "name": "Customer Updated", "status": "churned", "score": 101}
        ]
        
        changes = await detector.detect_changes("Customer", updated_data)
        
        # Should filter out low significance changes
        # Status change should be significant, score change should not
        assert len(changes) > 0
        # All returned changes should have high significance
        assert all(c.significance >= 0.7 for c in changes)
    
    @pytest.mark.asyncio
    async def test_custom_id_field(self, detector):
        """Test using custom ID field"""
        # Data with custom ID field
        data = [
            {"customer_id": "C001", "name": "Customer 1"},
            {"customer_id": "C002", "name": "Customer 2"}
        ]
        
        changes = await detector.detect_changes(
            "Customer",
            data,
            id_field="customer_id"
        )
        
        assert len(changes) == 2
        assert changes[0].entity_id in ["C001", "C002"]
    
    @pytest.mark.asyncio
    async def test_bulk_changes(self, detector):
        """Test detecting changes for multiple entity types"""
        data_by_type = {
            "Customer": [
                {"id": "c1", "name": "Customer 1"}
            ],
            "Product": [
                {"id": "p1", "name": "Product 1"},
                {"id": "p2", "name": "Product 2"}
            ]
        }
        
        all_changes = await detector.detect_bulk_changes(data_by_type)
        
        assert "Customer" in all_changes
        assert "Product" in all_changes
        assert len(all_changes["Customer"]) == 1
        assert len(all_changes["Product"]) == 2
    
    @pytest.mark.asyncio
    async def test_missing_id_field(self, detector):
        """Test handling missing ID field"""
        # Data without ID
        data = [
            {"name": "No ID Entity", "value": 100}
        ]
        
        # Should handle gracefully
        changes = await detector.detect_changes("Entity", data)
        
        # No valid entities to track
        assert len(changes) == 0
    
    @pytest.mark.asyncio
    async def test_checksum_optimization(self, detector):
        """Test that checksum prevents unnecessary comparisons"""
        # Large data set
        initial_data = [
            {
                "id": str(i),
                "field1": f"value{i}",
                "field2": i * 100,
                "field3": i % 2 == 0,
                "field4": f"long_text_{i}" * 10
            }
            for i in range(100)
        ]
        
        await detector.detect_changes("LargeEntity", initial_data)
        
        # Change only one entity
        updated_data = initial_data.copy()
        updated_data[50] = {
            "id": "50",
            "field1": "CHANGED",
            "field2": 5000,
            "field3": True,
            "field4": "changed_text" * 10
        }
        
        changes = await detector.detect_changes("LargeEntity", updated_data)
        
        # Should detect only one change
        assert len(changes) == 1
        assert changes[0].entity_id == "50"
        assert "field1" in changes[0].fields_changed
    
    @pytest.mark.asyncio
    async def test_entity_history(self, detector):
        """Test getting entity history"""
        # Create multiple versions
        for i in range(5):
            data = [{
                "id": "entity_1",
                "version": i,
                "status": "active" if i < 3 else "inactive"
            }]
            await detector.detect_changes("Entity", data)
        
        # Get history
        history = await detector.get_entity_history("Entity", "entity_1", limit=10)
        
        # Should have changes (creates and updates)
        assert len(history) > 0
        
        # First should be create
        assert any(c.operation == ChangeType.CREATE for c in history)
        
        # Should have status change
        status_changes = [
            c for c in history
            if c.operation == ChangeType.UPDATE and "status" in c.fields_changed
        ]
        assert len(status_changes) > 0
    
    @pytest.mark.asyncio
    async def test_rollback_to_snapshot(self, detector):
        """Test rolling back to previous snapshot"""
        # Create multiple snapshots
        timestamps = []
        for i in range(5):
            with freeze_time(datetime(2024, 1, 15, 10, i)):
                data = [
                    {"id": f"entity_{j}", "version": i}
                    for j in range(i + 1)
                ]
                await detector.detect_changes("Entity", data)
                timestamps.append(datetime(2024, 1, 15, 10, i))
        
        # Rollback to third snapshot
        target_time = timestamps[2]
        entities_restored, snapshots_removed = await detector.rollback_to_snapshot(
            "Entity", target_time
        )
        
        assert entities_restored == 3  # Third snapshot had 3 entities
        assert snapshots_removed >= 2  # Should remove newer snapshots
        
        # Verify current state matches rollback target
        current_snapshot = await detector.state_store.get_latest_snapshot("Entity")
        assert current_snapshot.entity_count == 3
    
    @pytest.mark.asyncio
    async def test_performance_large_dataset(self, detector):
        """Test performance with large dataset"""
        # Create large dataset
        large_data = [
            {
                "id": f"entity_{i:06d}",
                "name": f"Entity {i}",
                "value": i,
                "category": f"cat_{i % 10}",
                "active": i % 2 == 0
            }
            for i in range(10000)
        ]
        
        # Initial load
        import time
        start = time.time()
        changes = await detector.detect_changes("LargeDataset", large_data)
        initial_time = time.time() - start
        
        assert len(changes) == 10000
        assert initial_time < 5.0  # Should complete within 5 seconds
        
        # Update 100 entities - create a deep copy to ensure changes are detected
        import copy
        updated_data = copy.deepcopy(large_data)
        for i in range(100):
            updated_data[i * 100]["value"] = -1
        
        start = time.time()
        changes = await detector.detect_changes("LargeDataset", updated_data)
        update_time = time.time() - start
        
        assert len(changes) == 100
        assert update_time < 2.0  # Updates should be faster
    
    @pytest.mark.asyncio
    async def test_calculate_significance_flag(self, detector):
        """Test disabling significance calculation"""
        # Initial data
        initial_data = [{"id": "1", "value": 100}]
        await detector.detect_changes("Entity", initial_data)
        
        # Update without significance calculation
        updated_data = [{"id": "1", "value": 200}]
        changes = await detector.detect_changes(
            "Entity",
            updated_data,
            calculate_significance=False
        )
        
        assert len(changes) == 1
        # Default significance should be used
        assert changes[0].significance == 0.5