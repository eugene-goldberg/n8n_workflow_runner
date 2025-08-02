"""Relationship Builder module for discovering and constructing entity relationships"""

# Core models can be imported directly
from .models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    TemporalAspect,
    PathAnalysis,
    TemporalCorrelation,
    GraphPattern,
    CollaborationPattern,
    RelationshipRule,
    RelationshipDiscoveryContext,
    Event,
    EntityMention
)

# Implementation modules should be imported lazily to avoid dependency issues
__all__ = [
    "Entity",
    "Relationship",
    "RelationshipType",
    "RelationshipDirection",
    "RelationshipStrength",
    "TemporalAspect",
    "PathAnalysis",
    "TemporalCorrelation",
    "GraphPattern",
    "CollaborationPattern",
    "RelationshipRule",
    "RelationshipDiscoveryContext",
    "Event",
    "EntityMention",
    "RelationshipBuilder",
    "MultiHopRelationshipDiscoverer",
    "TemporalRelationshipAnalyzer",
    "SemanticRelationshipMiner",
    "GraphPatternRecognizer"
]

# Lazy imports for implementation modules
def __getattr__(name):
    if name == "RelationshipBuilder":
        from .relationship_builder import RelationshipBuilder
        return RelationshipBuilder
    elif name == "MultiHopRelationshipDiscoverer":
        from .multi_hop_discoverer import MultiHopRelationshipDiscoverer
        return MultiHopRelationshipDiscoverer
    elif name == "TemporalRelationshipAnalyzer":
        from .temporal_analyzer import TemporalRelationshipAnalyzer
        return TemporalRelationshipAnalyzer
    elif name == "SemanticRelationshipMiner":
        from .semantic_miner import SemanticRelationshipMiner
        return SemanticRelationshipMiner
    elif name == "GraphPatternRecognizer":
        from .pattern_recognizer import GraphPatternRecognizer
        return GraphPatternRecognizer
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")