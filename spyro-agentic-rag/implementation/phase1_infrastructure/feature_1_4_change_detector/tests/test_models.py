"""Tests for data models"""

import pytest
from datetime import datetime
from freezegun import freeze_time

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import Change, ChangeType, ChangeSignificance, EntityState, StateSnapshot


class TestChange:
    """Test cases for Change model"""
    
    def test_change_creation(self):
        """Test creating a change"""
        change = Change(
            entity_type="Customer",
            entity_id="cust_001",
            operation=ChangeType.UPDATE,
            fields_changed=["name", "status"],
            old_values={"name": "Old Corp", "status": "active"},
            new_values={"name": "New Corp", "status": "inactive"},
            significance=0.8
        )
        
        assert change.entity_type == "Customer"
        assert change.entity_id == "cust_001"
        assert change.operation == ChangeType.UPDATE
        assert len(change.fields_changed) == 2
        assert change.significance == 0.8
    
    def test_significance_level(self):
        """Test significance level categorization"""
        # Trivial
        change = Change("Customer", "1", ChangeType.UPDATE, significance=0.05)
        assert change.significance_level == ChangeSignificance.TRIVIAL
        
        # Low
        change.significance = 0.2
        assert change.significance_level == ChangeSignificance.LOW
        
        # Medium
        change.significance = 0.5
        assert change.significance_level == ChangeSignificance.MEDIUM
        
        # High
        change.significance = 0.8
        assert change.significance_level == ChangeSignificance.HIGH
        
        # Critical
        change.significance = 0.95
        assert change.significance_level == ChangeSignificance.CRITICAL
    
    def test_change_to_dict(self):
        """Test converting change to dictionary"""
        fixed_time = datetime(2024, 1, 15, 10, 30, 0)
        change = Change(
            entity_type="Customer",
            entity_id="cust_001",
            operation=ChangeType.CREATE,
            fields_changed=["name"],
            new_values={"name": "Test Corp"},
            timestamp=fixed_time,
            metadata={"source": "api"}
        )
        
        data = change.to_dict()
        assert data["entity_type"] == "Customer"
        assert data["entity_id"] == "cust_001"
        assert data["operation"] == "create"
        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert data["metadata"]["source"] == "api"
    
    def test_change_from_dict(self):
        """Test creating change from dictionary"""
        data = {
            "entity_type": "Product",
            "entity_id": "prod_001",
            "operation": "update",
            "fields_changed": ["price"],
            "old_values": {"price": 100},
            "new_values": {"price": 120},
            "timestamp": "2024-01-15T10:30:00",
            "significance": 0.7
        }
        
        change = Change.from_dict(data)
        assert change.entity_type == "Product"
        assert change.entity_id == "prod_001"
        assert change.operation == ChangeType.UPDATE
        assert change.old_values["price"] == 100
        assert change.new_values["price"] == 120
        assert change.significance == 0.7


class TestEntityState:
    """Test cases for EntityState model"""
    
    @freeze_time("2024-01-15 10:30:00")
    def test_entity_state_creation(self):
        """Test creating entity state"""
        state = EntityState(
            entity_type="Customer",
            entity_id="cust_001",
            data={"name": "Test Corp", "status": "active"},
            last_modified=datetime.now(),
            version=2,
            checksum="abc123"
        )
        
        assert state.entity_type == "Customer"
        assert state.entity_id == "cust_001"
        assert state.data["name"] == "Test Corp"
        assert state.version == 2
        assert state.checksum == "abc123"
    
    def test_entity_state_serialization(self):
        """Test entity state serialization"""
        state = EntityState(
            entity_type="Product",
            entity_id="prod_001",
            data={"name": "Widget", "price": 99.99},
            last_modified=datetime(2024, 1, 15, 10, 30)
        )
        
        # To dict
        data = state.to_dict()
        assert data["entity_type"] == "Product"
        assert data["data"]["price"] == 99.99
        assert data["last_modified"] == "2024-01-15T10:30:00"
        
        # From dict
        restored = EntityState.from_dict(data)
        assert restored.entity_id == state.entity_id
        assert restored.data == state.data
        assert restored.last_modified == state.last_modified


class TestStateSnapshot:
    """Test cases for StateSnapshot model"""
    
    @freeze_time("2024-01-15 10:30:00")
    def test_snapshot_creation(self):
        """Test creating state snapshot"""
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
            entities=entities,
            metadata={"source": "api"}
        )
        
        assert snapshot.entity_count == 2
        assert snapshot.entity_type == "Customer"
        assert snapshot.metadata["source"] == "api"
    
    def test_get_entity(self):
        """Test getting entity from snapshot"""
        entity = EntityState(
            entity_type="Customer",
            entity_id="cust_001",
            data={"name": "Test"},
            last_modified=datetime.now()
        )
        
        snapshot = StateSnapshot(
            timestamp=datetime.now(),
            entity_type="Customer",
            entities={"cust_001": entity}
        )
        
        # Existing entity
        retrieved = snapshot.get_entity("cust_001")
        assert retrieved is not None
        assert retrieved.data["name"] == "Test"
        
        # Non-existing entity
        assert snapshot.get_entity("cust_999") is None
    
    def test_snapshot_serialization(self):
        """Test snapshot serialization"""
        entities = {
            "prod_001": EntityState(
                entity_type="Product",
                entity_id="prod_001",
                data={"name": "Product 1", "price": 100},
                last_modified=datetime(2024, 1, 15, 10, 0)
            )
        }
        
        snapshot = StateSnapshot(
            timestamp=datetime(2024, 1, 15, 10, 30),
            entity_type="Product",
            entities=entities
        )
        
        # To dict
        data = snapshot.to_dict()
        assert data["entity_type"] == "Product"
        assert data["timestamp"] == "2024-01-15T10:30:00"
        assert "prod_001" in data["entities"]
        
        # From dict
        restored = StateSnapshot.from_dict(data)
        assert restored.entity_count == 1
        assert restored.timestamp == snapshot.timestamp
        assert "prod_001" in restored.entities