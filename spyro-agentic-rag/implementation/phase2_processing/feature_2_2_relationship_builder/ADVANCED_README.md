# Feature 2.2: Advanced Relationship Builder

## Overview
The Relationship Builder discovers and constructs relationships between entities using multiple strategies including explicit ID matching, semantic inference, temporal correlation, and graph pattern recognition.

## Status
🔴 **Not Started**

## Specifications

### Size
Large (5-6 days) - Extended to Extra Large (7-8 days) with advanced features

### Dependencies
- Feature 2.1 (Entity Extractor)

### Core Capabilities

#### 1. Explicit Relationship Detection
- ID-based relationship matching
- Foreign key resolution
- Parent-child hierarchies
- Reference field mapping

#### 2. Semantic Relationship Inference
- LLM-based relationship discovery
- Natural language relationship extraction
- Implicit connection identification
- Confidence scoring

#### 3. Temporal Relationship Analysis
- Time-based correlation
- Event sequence analysis
- Lag identification
- Causality inference

#### 4. Multi-Hop Relationship Discovery
- Path finding between entities
- Transitive relationship identification
- Hidden dependency discovery
- Relationship chain analysis

#### 5. Graph Pattern Recognition
- Hub detection
- Community identification
- Triangle patterns (collaboration)
- Chain patterns (dependencies)

## Implementation Components

### 1. Base Relationship Builder
```python
class RelationshipBuilder:
    """Core relationship building functionality"""
    
    async def build_relationships(self, entities: List[Entity]) -> List[Relationship]:
        # Explicit relationships
        # Semantic relationships
        # Temporal relationships
        # Hierarchical relationships
        # Deduplication
```

### 2. Multi-Hop Discoverer
```python
class MultiHopRelationshipDiscoverer:
    """Find complex multi-entity relationships"""
    
    async def discover_multi_hop(self, entities: List[Entity], max_hops: int = 3):
        # Build entity graph
        # Find meaningful paths
        # Analyze path significance
        # Score relationships
```

### 3. Temporal Analyzer
```python
class TemporalRelationshipAnalyzer:
    """Discover time-based relationships"""
    
    async def analyze_temporal_patterns(self, entities: List[Entity], events: List[Event]):
        # Extract time series
        # Calculate correlations
        # Identify lag patterns
        # Infer causality
```

### 4. Semantic Miner
```python
class SemanticRelationshipMiner:
    """Extract relationships from text"""
    
    async def mine_from_text(self, documents: List[Document], entities: List[Entity]):
        # Entity mention detection
        # Relationship extraction
        # Evidence collection
        # Confidence scoring
```

### 5. Pattern Recognizer
```python
class GraphPatternRecognizer:
    """Identify graph patterns"""
    
    async def recognize_patterns(self, graph: nx.Graph) -> List[GraphPattern]:
        # Hub detection
        # Community detection
        # Triangle patterns
        # Chain patterns
        # Anomaly detection
```

## Advanced Algorithms

### Multi-Hop Path Analysis
```python
async def analyze_path_significance(self, path: List[Entity]) -> PathAnalysis:
    """Determine if a multi-hop path represents a meaningful relationship"""
    
    # Calculate path strength
    edge_strengths = []
    for i in range(len(path) - 1):
        strength = await self._calculate_edge_strength(path[i], path[i+1])
        edge_strengths.append(strength)
    
    # Aggregate path score
    path_score = self._aggregate_path_score(edge_strengths)
    
    # Use LLM for interpretation
    interpretation = await self.llm.interpret_path(
        path=path,
        edge_strengths=edge_strengths,
        context=self.business_context
    )
    
    return PathAnalysis(
        path=path,
        score=path_score,
        interpretation=interpretation,
        actionable_insight=interpretation.get("business_impact")
    )
```

### Temporal Correlation Detection
```python
async def detect_temporal_correlations(self, 
                                     entity1: Entity, 
                                     entity2: Entity,
                                     time_window: int = 90) -> TemporalCorrelation:
    """Find temporal correlations between entities"""
    
    # Extract event sequences
    events1 = await self.get_entity_events(entity1, time_window)
    events2 = await self.get_entity_events(entity2, time_window)
    
    # Calculate correlation metrics
    correlation = self._calculate_correlation(events1, events2)
    
    # Detect lag
    optimal_lag = self._find_optimal_lag(events1, events2)
    
    # Test for causality
    causality = await self._test_granger_causality(events1, events2, optimal_lag)
    
    return TemporalCorrelation(
        entity1=entity1,
        entity2=entity2,
        correlation_coefficient=correlation,
        optimal_lag_days=optimal_lag,
        causality_score=causality,
        confidence=self._calculate_confidence(correlation, causality)
    )
```

### Semantic Relationship Extraction
```python
async def extract_semantic_relationships(self, text: str, entities: List[Entity]) -> List[Relationship]:
    """Extract relationships from natural language text"""
    
    # Create entity mention index
    mentions = self._find_entity_mentions(text, entities)
    
    # Use LLM for relationship extraction
    prompt = f"""
    Extract relationships between entities in this text:
    
    Text: {text}
    
    Entities found:
    {[{"id": m.entity_id, "text": m.surface_form, "type": m.entity_type} for m in mentions]}
    
    For each relationship, identify:
    1. Source entity
    2. Target entity  
    3. Relationship type (e.g., WORKS_WITH, DEPENDS_ON, MANAGES)
    4. Direction (unidirectional or bidirectional)
    5. Supporting evidence from text
    6. Confidence score (0-1)
    7. Temporal aspect if any (past, present, future)
    8. Strength indicator (strong, moderate, weak)
    """
    
    extracted = await self.llm.extract_relationships(prompt)
    
    # Validate and create relationships
    relationships = []
    for rel in extracted["relationships"]:
        validated = await self._validate_relationship(rel, mentions, text)
        if validated.confidence > self.confidence_threshold:
            relationships.append(validated)
    
    return relationships
```

### Graph Pattern Detection
```python
async def detect_collaboration_triangles(self, graph: nx.Graph) -> List[CollaborationPattern]:
    """Detect triangle patterns indicating collaboration"""
    
    triangles = []
    
    # Find all triangles in graph
    for triangle in nx.enumerate_all_cliques(graph):
        if len(triangle) == 3:
            # Analyze triangle significance
            pattern = await self._analyze_triangle(graph, triangle)
            
            if pattern.indicates_collaboration:
                triangles.append(CollaborationPattern(
                    entities=triangle,
                    pattern_type="collaboration_triangle",
                    strength=pattern.collaboration_strength,
                    evidence=pattern.supporting_evidence
                ))
    
    return triangles
```

## Relationship Types

### Explicit Relationships
```yaml
# config/relationship_rules.yaml
explicit_rules:
  - source_type: "SaaSSubscription"
    field: "customer_id"
    target_type: "Customer"
    relationship: "BELONGS_TO"
    
  - source_type: "Team"
    field: "manager_id"
    target_type: "Person"
    relationship: "MANAGED_BY"
    
  - source_type: "Project"
    field: "team_id"
    target_type: "Team"
    relationship: "ASSIGNED_TO"
```

### Inferred Relationships
- IMPACTS (Risk → Customer)
- COLLABORATES_WITH (Team ↔ Team)
- INFLUENCES (Objective → Metric)
- PRECEDES (Event → Event)
- CORRELATES_WITH (Metric ↔ Metric)

### Multi-Hop Relationships
- INDIRECTLY_AFFECTS (Customer → Team via Project)
- CASCADES_TO (Risk → Risk via Dependencies)
- INFLUENCES_THROUGH (Objective → Customer via Product)

## Testing Strategy

### Unit Tests
```python
# Test explicit relationship detection
async def test_explicit_id_relationships():
    builder = RelationshipBuilder()
    
    entities = [
        Entity(type="Customer", id="c1", attributes={"name": "TechCorp"}),
        Entity(type="Subscription", id="s1", attributes={"customer_id": "c1"})
    ]
    
    relationships = await builder.build_explicit_relationships(entities)
    assert any(r.relationship_type == "BELONGS_TO" for r in relationships)

# Test multi-hop discovery
async def test_multi_hop_discovery():
    discoverer = MultiHopRelationshipDiscoverer()
    
    # Create connected entities
    entities = create_connected_entity_graph()
    
    multi_hop = await discoverer.discover_multi_hop(entities, max_hops=3)
    
    # Should find Customer → Team relationship via Project
    customer_team = next(
        r for r in multi_hop 
        if r.source.type == "Customer" and r.target.type == "Team"
    )
    assert customer_team is not None
    assert len(customer_team.path) > 2

# Test temporal correlation
async def test_temporal_correlation():
    analyzer = TemporalRelationshipAnalyzer()
    
    # Create entities with temporal data
    risk = Entity(type="Risk", id="r1", attributes={"identified_date": "2024-01-15"})
    churn = Entity(type="ChurnEvent", id="ch1", attributes={"date": "2024-03-15"})
    
    correlation = await analyzer.analyze_temporal_patterns([risk, churn], [])
    
    assert correlation.optimal_lag_days == 60  # 2 months
    assert correlation.causality_score > 0.7
```

### Integration Tests
```python
# Test full relationship building pipeline
async def test_complete_relationship_pipeline():
    pipeline = RelationshipPipeline()
    
    # Load test data with various relationship types
    entities = load_test_entities("complex_graph.json")
    documents = load_test_documents("entity_mentions.json")
    events = load_test_events("temporal_events.json")
    
    relationships = await pipeline.build_all_relationships(
        entities=entities,
        documents=documents,
        events=events
    )
    
    # Verify all relationship types found
    rel_types = set(r.relationship_type for r in relationships)
    assert "BELONGS_TO" in rel_types  # Explicit
    assert "COLLABORATES_WITH" in rel_types  # Semantic
    assert "PRECEDES" in rel_types  # Temporal
    assert "INDIRECTLY_AFFECTS" in rel_types  # Multi-hop
```

### Performance Tests
```python
# Test relationship building at scale
async def test_large_graph_performance():
    builder = RelationshipBuilder()
    
    # Generate large entity set
    entities = generate_entities(count=10000, connectivity=0.1)
    
    start = time.time()
    relationships = await builder.build_relationships(entities)
    duration = time.time() - start
    
    assert duration < 60  # Should complete in under 1 minute
    assert len(relationships) > 1000  # Should find many relationships
    
    # Verify memory usage
    memory_usage = get_memory_usage()
    assert memory_usage < 1_000_000_000  # Less than 1GB
```

## Acceptance Criteria

### Core Requirements
- [ ] Detects explicit ID-based relationships
- [ ] Infers semantic relationships from text
- [ ] Identifies temporal correlations
- [ ] Discovers multi-hop connections
- [ ] Provides confidence scores

### Advanced Requirements
- [ ] Recognizes graph patterns
- [ ] Handles bidirectional relationships
- [ ] Resolves relationship conflicts
- [ ] Maintains relationship provenance
- [ ] Supports incremental updates

### Performance Requirements
- [ ] Processes 10K entities in < 60 seconds
- [ ] Scales to millions of relationships
- [ ] Efficient graph traversal
- [ ] Optimized LLM usage

## Configuration

```yaml
# config/relationship_builder.yaml
relationship_discovery:
  explicit:
    enable: true
    rules_file: "config/relationship_rules.yaml"
    
  semantic:
    enable: true
    confidence_threshold: 0.7
    llm_model: "gpt-4"
    batch_size: 10
    
  temporal:
    enable: true
    correlation_window_days: 90
    min_correlation: 0.6
    causality_test: "granger"
    
  multi_hop:
    enable: true
    max_hops: 3
    min_path_strength: 0.5
    
  patterns:
    enable: true
    detect_hubs: true
    detect_communities: true
    min_community_size: 3
    
performance:
  parallel_workers: 4
  cache_relationships: true
  cache_ttl_seconds: 3600
  batch_llm_calls: true
```

## Common Relationship Patterns

### Business Patterns
1. **Customer Success Triangle**: Customer ↔ CSM ↔ Product
2. **Risk Cascade**: Risk → Project → Team → Customer
3. **Revenue Chain**: Customer → Subscription → Product → Revenue
4. **Support Pattern**: Ticket → Customer → Product → Team

### Technical Patterns
1. **Dependency Chain**: Service → API → Database
2. **Team Collaboration**: Team ↔ Project ↔ Team
3. **Feature Impact**: Feature → Usage → Customer → Revenue

## Next Steps

1. Implement base RelationshipBuilder class
2. Add explicit relationship rules engine
3. Implement semantic extraction with LLM
4. Build temporal correlation analyzer
5. Create multi-hop path finder
6. Add graph pattern recognition
7. Optimize for large-scale graphs