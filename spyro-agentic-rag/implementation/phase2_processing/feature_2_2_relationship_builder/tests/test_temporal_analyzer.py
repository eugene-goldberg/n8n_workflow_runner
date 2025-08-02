"""Tests for TemporalRelationshipAnalyzer"""

import pytest
import asyncio
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import (
    Entity,
    Event,
    Relationship,
    RelationshipType,
    TemporalCorrelation
)
from src.temporal_analyzer import TemporalRelationshipAnalyzer


class TestTemporalAnalyzer:
    """Test TemporalRelationshipAnalyzer functionality"""
    
    @pytest.fixture
    def analyzer(self):
        """Create TemporalRelationshipAnalyzer instance"""
        return TemporalRelationshipAnalyzer()
    
    @pytest.fixture
    def sample_entities(self):
        """Create sample entities for testing"""
        return [
            Entity(id="metric_001", type="Metric", attributes={"name": "Revenue"}),
            Entity(id="metric_002", type="Metric", attributes={"name": "Churn Rate"}),
            Entity(id="risk_001", type="Risk", attributes={"title": "Market Risk"}),
            Entity(id="cust_001", type="Customer", attributes={"name": "TechCorp"})
        ]
    
    @pytest.fixture
    def sample_events(self):
        """Create sample events with temporal patterns"""
        base_date = datetime(2024, 1, 1)
        events = []
        
        # Create correlated events for metric_001 and metric_002
        for i in range(30):
            date = base_date + timedelta(days=i)
            
            # Metric 1 events (leading indicator)
            events.append(Event(
                entity_id="metric_001",
                event_type="value_change",
                timestamp=date,
                value=100 + i * 2 + (i % 7) * 5  # Trend with weekly pattern
            ))
            
            # Metric 2 events (lagging by 7 days)
            if i >= 7:
                events.append(Event(
                    entity_id="metric_002",
                    event_type="value_change",
                    timestamp=date,
                    value=50 + (i-7) * 1.5 + ((i-7) % 7) * 3  # Similar pattern, delayed
                ))
        
        # Add some risk events
        risk_dates = [5, 12, 20, 25]
        for day in risk_dates:
            events.append(Event(
                entity_id="risk_001",
                event_type="risk_identified",
                timestamp=base_date + timedelta(days=day),
                value=1
            ))
        
        return events
    
    @pytest.mark.asyncio
    async def test_analyze_temporal_patterns(self, analyzer, sample_entities, sample_events):
        """Test temporal pattern analysis"""
        relationships = await analyzer.analyze_temporal_patterns(
            sample_entities,
            sample_events
        )
        
        assert len(relationships) > 0
        
        # Should find correlation between metrics
        metric_rels = [
            r for r in relationships
            if "metric_001" in {r.source.id, r.target.id} and
               "metric_002" in {r.source.id, r.target.id}
        ]
        assert len(metric_rels) > 0
    
    @pytest.mark.asyncio
    async def test_correlation_detection(self, analyzer, sample_entities, sample_events):
        """Test correlation detection between entities"""
        # Group events
        entity_events = analyzer._group_events_by_entity(sample_events)
        
        # Test correlation between metrics
        entity1 = sample_entities[0]  # metric_001
        entity2 = sample_entities[1]  # metric_002
        
        correlation = await analyzer._analyze_entity_correlation(
            entity1,
            entity2,
            entity_events["metric_001"],
            entity_events["metric_002"]
        )
        
        assert correlation is not None
        assert abs(correlation.correlation_coefficient) > 0.5  # Should be correlated
        assert correlation.optimal_lag_days > 0  # Should detect lag
    
    @pytest.mark.asyncio
    async def test_events_to_time_series(self, analyzer):
        """Test conversion of events to time series"""
        base_date = datetime(2024, 1, 1)
        events = [
            Event(entity_id="e1", event_type="test", timestamp=base_date, value=10),
            Event(entity_id="e1", event_type="test", timestamp=base_date + timedelta(days=1), value=20),
            Event(entity_id="e1", event_type="test", timestamp=base_date + timedelta(days=3), value=30),
        ]
        
        series = analyzer._events_to_time_series(events)
        
        assert isinstance(series, pd.Series)
        assert len(series) == 4  # Should fill missing day 2
        assert series.iloc[0] == 10
        assert series.iloc[1] == 20
        assert series.iloc[3] == 30
    
    @pytest.mark.asyncio
    async def test_optimal_lag_detection(self, analyzer):
        """Test optimal lag detection"""
        # Create two series with known lag
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        ts1 = pd.Series([i + (i % 7) for i in range(30)], index=dates)
        ts2 = ts1.shift(5)  # 5-day lag
        
        optimal_lag = await analyzer._find_optimal_lag(ts1, ts2)
        
        # Should detect approximately 5-day lag
        assert abs(optimal_lag - 5) <= 1
    
    @pytest.mark.asyncio
    async def test_causality_testing(self, analyzer):
        """Test causality testing between time series"""
        # Create causal relationship
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        ts1 = pd.Series(range(30), index=dates)
        ts2 = ts1.shift(3) * 0.8 + 5  # ts1 causes ts2 with lag
        
        causality_score = await analyzer._test_causality(ts1, ts2, lag=3)
        
        assert causality_score > 0.5  # Should indicate causality
    
    @pytest.mark.asyncio
    async def test_temporal_relationship_creation(self, analyzer):
        """Test creation of temporal relationships"""
        entity1 = Entity(id="e1", type="Event")
        entity2 = Entity(id="e2", type="Event")
        
        correlation = TemporalCorrelation(
            entity1=entity1,
            entity2=entity2,
            correlation_coefficient=0.8,
            optimal_lag_days=5,
            causality_score=0.9,
            confidence=0.85
        )
        
        relationships = analyzer._create_temporal_relationships(correlation)
        
        assert len(relationships) > 0
        
        # Should create PRECEDES relationship
        precedes_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.PRECEDES
        ]
        assert len(precedes_rels) > 0
        
        # Should create INFLUENCES for strong causality
        influence_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.INFLUENCES
        ]
        assert len(influence_rels) > 0
    
    @pytest.mark.asyncio
    async def test_non_causal_correlation(self, analyzer):
        """Test handling of non-causal correlations"""
        entity1 = Entity(id="e1", type="Metric")
        entity2 = Entity(id="e2", type="Metric")
        
        correlation = TemporalCorrelation(
            entity1=entity1,
            entity2=entity2,
            correlation_coefficient=0.7,
            optimal_lag_days=0,  # No lag
            causality_score=0.3,  # Low causality
            confidence=0.6
        )
        
        relationships = analyzer._create_temporal_relationships(correlation)
        
        # Should create CORRELATES_WITH relationship
        correlates_rels = [
            r for r in relationships
            if r.relationship_type == RelationshipType.CORRELATES_WITH
        ]
        assert len(correlates_rels) > 0
        assert correlates_rels[0].direction.value == "BIDIRECTIONAL"
    
    @pytest.mark.asyncio
    async def test_temporal_clustering(self, analyzer):
        """Test temporal event clustering"""
        base_date = datetime(2024, 1, 1)
        events = []
        
        # Create clusters of events
        cluster_days = [1, 2, 3, 10, 11, 12, 20, 21, 22]
        for day in cluster_days:
            for i in range(3):  # Multiple events per day
                events.append(Event(
                    entity_id=f"e_{day}_{i}",
                    event_type="cluster_event",
                    timestamp=base_date + timedelta(days=day, hours=i)
                ))
        
        clusters = await analyzer.detect_temporal_clusters(events, window_days=3)
        
        assert len(clusters) == 3  # Should find 3 clusters
        
        # Check cluster sizes
        for cluster_time, cluster_events in clusters:
            assert len(cluster_events) >= 3
    
    @pytest.mark.asyncio
    async def test_insufficient_events_handling(self, analyzer):
        """Test handling of insufficient events"""
        entities = [
            Entity(id="e1", type="E"),
            Entity(id="e2", type="E")
        ]
        
        # Too few events
        events = [
            Event(entity_id="e1", event_type="test", timestamp=datetime.now()),
            Event(entity_id="e2", event_type="test", timestamp=datetime.now())
        ]
        
        relationships = await analyzer.analyze_temporal_patterns(entities, events)
        
        # Should not create relationships with insufficient data
        assert len(relationships) == 0
    
    @pytest.mark.asyncio
    async def test_time_series_alignment(self, analyzer):
        """Test time series alignment"""
        # Create misaligned series
        ts1 = pd.Series(
            [1, 2, 3, 4, 5],
            index=pd.date_range('2024-01-01', periods=5)
        )
        ts2 = pd.Series(
            [10, 20, 30, 40, 50],
            index=pd.date_range('2024-01-03', periods=5)
        )
        
        aligned1, aligned2 = analyzer._align_time_series(ts1, ts2)
        
        # Should have same length and date range
        assert len(aligned1) == len(aligned2)
        assert aligned1.index.min() == aligned2.index.min()
        assert aligned1.index.max() == aligned2.index.max()
    
    @pytest.mark.asyncio
    async def test_correlation_caching(self, analyzer, sample_entities, sample_events):
        """Test correlation result caching"""
        entity_events = analyzer._group_events_by_entity(sample_events)
        
        entity1 = sample_entities[0]
        entity2 = sample_entities[1]
        
        # First call
        correlation1 = await analyzer._analyze_entity_correlation(
            entity1, entity2,
            entity_events["metric_001"],
            entity_events["metric_002"]
        )
        
        # Second call should use cache
        correlation2 = await analyzer._analyze_entity_correlation(
            entity1, entity2,
            entity_events["metric_001"],
            entity_events["metric_002"]
        )
        
        assert correlation1 is correlation2  # Same object from cache
        
        # Clear cache
        analyzer.clear_cache()
        assert len(analyzer._correlation_cache) == 0
    
    @pytest.mark.asyncio
    async def test_empty_inputs(self, analyzer):
        """Test with empty inputs"""
        # Empty entities
        result1 = await analyzer.analyze_temporal_patterns([], [])
        assert result1 == []
        
        # Empty events
        entities = [Entity(id="e1", type="E")]
        result2 = await analyzer.analyze_temporal_patterns(entities, [])
        assert result2 == []