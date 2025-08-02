"""Temporal relationship analysis"""

import asyncio
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from scipy import stats
import pandas as pd

from .models import (
    Entity,
    Event,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    TemporalCorrelation,
    TemporalAspect,
    RelationshipDiscoveryContext
)

logger = logging.getLogger(__name__)


class TemporalRelationshipAnalyzer:
    """Discover time-based relationships between entities"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize temporal analyzer
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._get_default_config()
        self._correlation_cache: Dict[Tuple[str, str], TemporalCorrelation] = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "correlation_window_days": 90,
            "min_correlation": 0.6,
            "causality_test": "granger",
            "lag_detection": {
                "max_lag_days": 30,
                "lag_step_days": 1
            },
            "event_aggregation": {
                "method": "daily",  # daily, weekly, monthly
                "fill_method": "forward"
            },
            "significance_level": 0.05,
            "min_events_required": 10
        }
    
    async def analyze_temporal_patterns(
        self,
        entities: List[Entity],
        events: List[Event],
        context: Optional[RelationshipDiscoveryContext] = None
    ) -> List[Relationship]:
        """Analyze temporal patterns to discover relationships
        
        Args:
            entities: List of entities
            events: List of temporal events
            context: Optional discovery context
            
        Returns:
            List of discovered temporal relationships
        """
        if not entities or not events:
            return []
        
        context = context or RelationshipDiscoveryContext()
        
        # Group events by entity
        entity_events = self._group_events_by_entity(events)
        
        # Filter entities with sufficient events
        active_entities = [
            e for e in entities
            if len(entity_events.get(e.id, [])) >= self.config["min_events_required"]
        ]
        
        if len(active_entities) < 2:
            return []
        
        # Discover temporal relationships
        relationships = []
        
        # Process entity pairs
        for i, entity1 in enumerate(active_entities):
            for entity2 in active_entities[i+1:]:
                # Analyze temporal correlation
                correlation = await self._analyze_entity_correlation(
                    entity1,
                    entity2,
                    entity_events[entity1.id],
                    entity_events[entity2.id]
                )
                
                if correlation and correlation.is_significant(self.config["min_correlation"]):
                    # Create relationship(s) from correlation
                    rels = self._create_temporal_relationships(correlation)
                    
                    for rel in rels:
                        if context.should_include_relationship(rel):
                            relationships.append(rel)
        
        return relationships
    
    def _group_events_by_entity(self, events: List[Event]) -> Dict[str, List[Event]]:
        """Group events by entity ID"""
        grouped = defaultdict(list)
        
        for event in events:
            grouped[event.entity_id].append(event)
        
        # Sort events by timestamp
        for entity_id in grouped:
            grouped[entity_id].sort(key=lambda e: e.timestamp)
        
        return dict(grouped)
    
    async def _analyze_entity_correlation(
        self,
        entity1: Entity,
        entity2: Entity,
        events1: List[Event],
        events2: List[Event]
    ) -> Optional[TemporalCorrelation]:
        """Analyze temporal correlation between two entities"""
        # Check cache
        cache_key = (entity1.id, entity2.id)
        if cache_key in self._correlation_cache:
            return self._correlation_cache[cache_key]
        
        # Convert events to time series
        ts1 = self._events_to_time_series(events1)
        ts2 = self._events_to_time_series(events2)
        
        if ts1.empty or ts2.empty:
            return None
        
        # Align time series
        ts1_aligned, ts2_aligned = self._align_time_series(ts1, ts2)
        
        if len(ts1_aligned) < self.config["min_events_required"]:
            return None
        
        # Calculate correlation
        correlation_coef = self._calculate_correlation(ts1_aligned, ts2_aligned)
        
        # Find optimal lag
        optimal_lag = await self._find_optimal_lag(ts1_aligned, ts2_aligned)
        
        # Test for causality
        causality_score = await self._test_causality(
            ts1_aligned,
            ts2_aligned,
            optimal_lag
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            correlation_coef,
            causality_score,
            len(ts1_aligned)
        )
        
        correlation = TemporalCorrelation(
            entity1=entity1,
            entity2=entity2,
            correlation_coefficient=correlation_coef,
            optimal_lag_days=optimal_lag,
            causality_score=causality_score,
            confidence=confidence,
            time_window_days=self.config["correlation_window_days"],
            events_analyzed=len(ts1_aligned)
        )
        
        # Cache result
        self._correlation_cache[cache_key] = correlation
        
        return correlation
    
    def _events_to_time_series(self, events: List[Event]) -> pd.Series:
        """Convert events to time series"""
        if not events:
            return pd.Series()
        
        # Create series from events
        data = {}
        for event in events:
            date = event.timestamp.date()
            value = event.value if event.value is not None else 1.0
            
            if date in data:
                # Aggregate values for same date
                if self.config["event_aggregation"]["method"] == "sum":
                    data[date] += value
                elif self.config["event_aggregation"]["method"] == "mean":
                    data[date] = (data[date] + value) / 2
                else:  # count
                    data[date] += 1
            else:
                data[date] = value
        
        # Create pandas series
        series = pd.Series(data).sort_index()
        
        # Fill missing dates
        if len(series) > 1:
            date_range = pd.date_range(
                start=series.index.min(),
                end=series.index.max(),
                freq='D'
            )
            series = series.reindex(date_range)
            
            # Fill missing values
            if self.config["event_aggregation"]["fill_method"] == "forward":
                series = series.fillna(method='ffill')
            elif self.config["event_aggregation"]["fill_method"] == "zero":
                series = series.fillna(0)
            else:
                series = series.interpolate()
        
        return series
    
    def _align_time_series(
        self,
        ts1: pd.Series,
        ts2: pd.Series
    ) -> Tuple[pd.Series, pd.Series]:
        """Align two time series to same date range"""
        # Find common date range
        start_date = max(ts1.index.min(), ts2.index.min())
        end_date = min(ts1.index.max(), ts2.index.max())
        
        # Apply correlation window
        window_days = self.config["correlation_window_days"]
        if (end_date - start_date).days > window_days:
            start_date = end_date - timedelta(days=window_days)
        
        # Slice to common range
        mask1 = (ts1.index >= start_date) & (ts1.index <= end_date)
        mask2 = (ts2.index >= start_date) & (ts2.index <= end_date)
        
        return ts1[mask1], ts2[mask2]
    
    def _calculate_correlation(self, ts1: pd.Series, ts2: pd.Series) -> float:
        """Calculate Pearson correlation coefficient"""
        if len(ts1) < 2 or len(ts2) < 2:
            return 0.0
        
        try:
            # Remove NaN values
            mask = ~(ts1.isna() | ts2.isna())
            ts1_clean = ts1[mask]
            ts2_clean = ts2[mask]
            
            if len(ts1_clean) < 2:
                return 0.0
            
            correlation, _ = stats.pearsonr(ts1_clean, ts2_clean)
            return float(correlation)
            
        except Exception as e:
            logger.warning(f"Failed to calculate correlation: {e}")
            return 0.0
    
    async def _find_optimal_lag(
        self,
        ts1: pd.Series,
        ts2: pd.Series
    ) -> int:
        """Find optimal lag between time series"""
        max_lag = self.config["lag_detection"]["max_lag_days"]
        lag_step = self.config["lag_detection"]["lag_step_days"]
        
        best_lag = 0
        best_correlation = abs(self._calculate_correlation(ts1, ts2))
        
        # Test different lags
        for lag in range(-max_lag, max_lag + 1, lag_step):
            if lag == 0:
                continue
            
            # Shift series
            if lag > 0:
                ts1_shifted = ts1.shift(lag)
            else:
                ts1_shifted = ts1.shift(lag)
            
            # Calculate correlation with lag
            correlation = abs(self._calculate_correlation(ts1_shifted, ts2))
            
            if correlation > best_correlation:
                best_correlation = correlation
                best_lag = lag
        
        return best_lag
    
    async def _test_causality(
        self,
        ts1: pd.Series,
        ts2: pd.Series,
        lag: int
    ) -> float:
        """Test for causality between time series"""
        if self.config["causality_test"] == "granger":
            return await self._granger_causality_test(ts1, ts2, lag)
        else:
            # Simple lag correlation as causality proxy
            if lag == 0:
                return 0.5  # No clear causality
            
            # Shift series based on lag
            if lag > 0:
                # ts1 leads ts2
                ts1_shifted = ts1.shift(lag)
                correlation = abs(self._calculate_correlation(ts1_shifted, ts2))
            else:
                # ts2 leads ts1
                ts2_shifted = ts2.shift(-lag)
                correlation = abs(self._calculate_correlation(ts1, ts2_shifted))
            
            # Convert correlation to causality score
            return min(correlation * 1.2, 1.0)
    
    async def _granger_causality_test(
        self,
        ts1: pd.Series,
        ts2: pd.Series,
        lag: int
    ) -> float:
        """Perform Granger causality test"""
        try:
            from statsmodels.tsa.stattools import grangercausalitytests
            
            # Prepare data
            data = pd.DataFrame({
                'x': ts1.values,
                'y': ts2.values
            }).dropna()
            
            if len(data) < 20:  # Minimum for meaningful test
                return 0.5
            
            # Run test
            max_lag = max(1, abs(lag))
            results = grangercausalitytests(
                data[['x', 'y']],
                maxlag=max_lag,
                verbose=False
            )
            
            # Get p-value for optimal lag
            p_value = results[max_lag][0]['ssr_ftest'][1]
            
            # Convert p-value to causality score
            if p_value < self.config["significance_level"]:
                return 1.0 - p_value
            else:
                return 0.5 - p_value * 0.5
                
        except Exception as e:
            logger.warning(f"Granger causality test failed: {e}")
            # Fall back to simple method
            return await self._test_causality(ts1, ts2, lag)
    
    def _calculate_confidence(
        self,
        correlation: float,
        causality: float,
        num_points: int
    ) -> float:
        """Calculate confidence score for temporal relationship"""
        # Base confidence on correlation strength
        base_confidence = abs(correlation)
        
        # Adjust for causality
        causality_factor = 0.5 + (causality * 0.5)
        
        # Adjust for sample size
        size_factor = min(1.0, num_points / 50.0)
        
        # Combined confidence
        confidence = base_confidence * causality_factor * size_factor
        
        return min(1.0, confidence)
    
    def _create_temporal_relationships(
        self,
        correlation: TemporalCorrelation
    ) -> List[Relationship]:
        """Create relationships from temporal correlation"""
        relationships = []
        
        # Determine relationship type and direction
        if correlation.is_causal():
            # Create causal relationship
            if correlation.optimal_lag_days > 0:
                # Entity1 precedes Entity2
                rel = Relationship(
                    source=correlation.entity1,
                    target=correlation.entity2,
                    relationship_type=RelationshipType.PRECEDES,
                    direction=RelationshipDirection.UNIDIRECTIONAL,
                    strength=self._correlation_to_strength(correlation),
                    confidence=correlation.confidence,
                    evidence=[
                        f"Temporal correlation: {correlation.correlation_coefficient:.2f}",
                        f"Optimal lag: {correlation.optimal_lag_days} days",
                        f"Causality score: {correlation.causality_score:.2f}"
                    ],
                    temporal_aspect=TemporalAspect.ONGOING,
                    metadata={
                        "temporal_correlation": correlation.__dict__
                    }
                )
                relationships.append(rel)
                
                # Add INFLUENCES relationship for strong causality
                if correlation.causality_score > 0.8:
                    influence_rel = Relationship(
                        source=correlation.entity1,
                        target=correlation.entity2,
                        relationship_type=RelationshipType.INFLUENCES,
                        direction=RelationshipDirection.UNIDIRECTIONAL,
                        strength=self._correlation_to_strength(correlation),
                        confidence=correlation.confidence * 0.9,
                        evidence=[
                            f"Strong causal influence detected",
                            f"Lag: {correlation.optimal_lag_days} days"
                        ],
                        temporal_aspect=TemporalAspect.ONGOING
                    )
                    relationships.append(influence_rel)
            
            elif correlation.optimal_lag_days < 0:
                # Entity2 precedes Entity1
                rel = Relationship(
                    source=correlation.entity2,
                    target=correlation.entity1,
                    relationship_type=RelationshipType.PRECEDES,
                    direction=RelationshipDirection.UNIDIRECTIONAL,
                    strength=self._correlation_to_strength(correlation),
                    confidence=correlation.confidence,
                    evidence=[
                        f"Temporal correlation: {correlation.correlation_coefficient:.2f}",
                        f"Optimal lag: {abs(correlation.optimal_lag_days)} days",
                        f"Causality score: {correlation.causality_score:.2f}"
                    ],
                    temporal_aspect=TemporalAspect.ONGOING,
                    metadata={
                        "temporal_correlation": correlation.__dict__
                    }
                )
                relationships.append(rel)
        
        else:
            # Non-causal correlation
            rel = Relationship(
                source=correlation.entity1,
                target=correlation.entity2,
                relationship_type=RelationshipType.CORRELATES_WITH,
                direction=RelationshipDirection.BIDIRECTIONAL,
                strength=self._correlation_to_strength(correlation),
                confidence=correlation.confidence,
                evidence=[
                    f"Temporal correlation: {correlation.correlation_coefficient:.2f}",
                    f"No clear causality detected"
                ],
                temporal_aspect=TemporalAspect.ONGOING,
                metadata={
                    "temporal_correlation": correlation.__dict__
                }
            )
            relationships.append(rel)
        
        return relationships
    
    def _correlation_to_strength(self, correlation: TemporalCorrelation) -> RelationshipStrength:
        """Convert correlation to relationship strength"""
        abs_corr = abs(correlation.correlation_coefficient)
        
        if abs_corr >= 0.8:
            return RelationshipStrength.STRONG
        elif abs_corr >= 0.6:
            return RelationshipStrength.MODERATE
        else:
            return RelationshipStrength.WEAK
    
    async def detect_temporal_clusters(
        self,
        events: List[Event],
        window_days: int = 7
    ) -> List[Tuple[datetime, List[Event]]]:
        """Detect temporal clusters of events
        
        Args:
            events: List of events
            window_days: Window size for clustering
            
        Returns:
            List of (cluster_time, cluster_events) tuples
        """
        if not events:
            return []
        
        # Sort events by timestamp
        sorted_events = sorted(events, key=lambda e: e.timestamp)
        
        clusters = []
        current_cluster = [sorted_events[0]]
        cluster_start = sorted_events[0].timestamp
        
        for event in sorted_events[1:]:
            # Check if event is within window of cluster start
            if (event.timestamp - cluster_start).days <= window_days:
                current_cluster.append(event)
            else:
                # Save current cluster and start new one
                if len(current_cluster) >= 3:  # Minimum cluster size
                    cluster_time = cluster_start + timedelta(
                        days=(current_cluster[-1].timestamp - cluster_start).days / 2
                    )
                    clusters.append((cluster_time, current_cluster))
                
                current_cluster = [event]
                cluster_start = event.timestamp
        
        # Add final cluster
        if len(current_cluster) >= 3:
            cluster_time = cluster_start + timedelta(
                days=(current_cluster[-1].timestamp - cluster_start).days / 2
            )
            clusters.append((cluster_time, current_cluster))
        
        return clusters
    
    def clear_cache(self):
        """Clear correlation cache"""
        self._correlation_cache.clear()