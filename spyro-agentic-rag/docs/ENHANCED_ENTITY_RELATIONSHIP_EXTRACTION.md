# Enhanced Entity and Relationship Extraction Capabilities

## Overview
This document provides enhanced details for the entity extraction and relationship identification capabilities that are critical to the SpyroSolutions Agentic RAG system.

## Entity Extraction Enhancement (Feature 2.1 Extended)

### Advanced Entity Recognition Strategies

#### 1. Multi-Source Entity Resolution
```python
class AdvancedEntityExtractor(EntityExtractor):
    """Enhanced entity extraction with cross-source resolution"""
    
    async def extract_and_resolve_entities(self, 
                                         data_sources: Dict[str, List[Dict]]) -> List[Entity]:
        """Extract entities from multiple sources and resolve duplicates"""
        
        all_entities = []
        
        # Extract from each source
        for source_name, records in data_sources.items():
            source_entities = await self.extract_from_source(source_name, records)
            all_entities.extend(source_entities)
        
        # Resolve duplicates across sources
        resolved_entities = await self.resolve_duplicate_entities(all_entities)
        
        # Enrich with cross-source data
        enriched_entities = await self.cross_source_enrichment(resolved_entities)
        
        return enriched_entities
    
    async def resolve_duplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """Identify and merge duplicate entities from different sources"""
        
        # Group potential duplicates
        candidate_groups = await self._find_duplicate_candidates(entities)
        
        resolved = []
        for group in candidate_groups:
            if len(group) == 1:
                resolved.append(group[0])
            else:
                # Use LLM to determine if entities are the same
                merged = await self._merge_entities_with_llm(group)
                resolved.append(merged)
        
        return resolved
    
    async def _merge_entities_with_llm(self, entities: List[Entity]) -> Entity:
        """Use LLM to intelligently merge entity data"""
        
        prompt = f"""
        Determine if these entities represent the same real-world entity and merge them:
        
        Entities:
        {json.dumps([e.attributes for e in entities], indent=2)}
        
        Consider:
        1. Name variations (e.g., "Tech Corp", "TechCorp", "Tech Corporation")
        2. ID mappings across systems
        3. Conflicting attributes (choose most reliable/recent)
        4. Complementary data (combine non-conflicting attributes)
        
        Return merged entity with confidence score.
        """
        
        result = await self.llm.generate_json(prompt)
        
        return Entity(
            type=entities[0].type,
            id=self._generate_master_id(entities),
            attributes=result["merged_attributes"],
            source_ids={e.source: e.id for e in entities},
            merge_confidence=result["confidence"]
        )
```

#### 2. Complex Entity Type Detection
```python
class EntityTypeDetector:
    """Detect complex entity types from unstructured data"""
    
    def __init__(self):
        self.entity_patterns = self._load_entity_patterns()
        self.llm = LLM(model="gpt-4")
    
    async def detect_entity_types(self, text: str) -> List[DetectedEntity]:
        """Detect multiple entity types in text"""
        
        # Pattern-based detection
        pattern_entities = self._pattern_based_detection(text)
        
        # LLM-based detection for complex entities
        llm_entities = await self._llm_based_detection(text)
        
        # Combine and deduplicate
        all_entities = self._combine_detections(pattern_entities, llm_entities)
        
        return all_entities
    
    async def _llm_based_detection(self, text: str) -> List[DetectedEntity]:
        """Use LLM for sophisticated entity detection"""
        
        prompt = f"""
        Extract all business entities from this text:
        
        {text}
        
        Look for:
        1. Direct mentions (companies, products, people)
        2. Implicit entities (e.g., "the platform team" → Team entity)
        3. Composite entities (e.g., "Q4 revenue target" → Objective + Metric)
        4. Temporal entities (events, milestones, deadlines)
        5. Abstract entities (risks, opportunities, concerns)
        
        For each entity, provide:
        - Type (Customer, Product, Team, Risk, etc.)
        - Name/identifier
        - Relevant attributes
        - Confidence score
        - Text span location
        """
        
        entities = await self.llm.generate_json(prompt)
        
        return [
            DetectedEntity(
                type=e["type"],
                name=e["name"],
                attributes=e["attributes"],
                confidence=e["confidence"],
                span_start=e["span_start"],
                span_end=e["span_end"]
            )
            for e in entities["entities"]
        ]
```

#### 3. Contextual Entity Enrichment
```python
class ContextualEnricher:
    """Enrich entities with contextual information"""
    
    async def enrich_with_context(self, entity: Entity, 
                                 context: Dict[str, Any]) -> Entity:
        """Add contextual information to entity"""
        
        enrichments = {}
        
        # Industry-specific enrichment
        if entity.type == "Customer":
            industry_data = await self._get_industry_context(
                entity.attributes.get("industry"),
                entity.attributes.get("size")
            )
            enrichments.update(industry_data)
        
        # Temporal context
        if "created_date" in entity.attributes:
            temporal_context = self._get_temporal_context(
                entity.attributes["created_date"],
                context.get("current_date")
            )
            enrichments["age_days"] = temporal_context["age_days"]
            enrichments["lifecycle_stage"] = temporal_context["stage"]
        
        # Relationship-based enrichment
        if context.get("related_entities"):
            relationship_enrichments = await self._enrich_from_relationships(
                entity,
                context["related_entities"]
            )
            enrichments.update(relationship_enrichments)
        
        entity.attributes.update(enrichments)
        return entity
```

## Relationship Identification Enhancement (Feature 2.2 Extended)

### Advanced Relationship Discovery

#### 1. Multi-Hop Relationship Inference
```python
class MultiHopRelationshipBuilder(RelationshipBuilder):
    """Discover complex multi-hop relationships"""
    
    async def build_multi_hop_relationships(self, 
                                          entities: List[Entity],
                                          max_hops: int = 3) -> List[Relationship]:
        """Identify relationships that span multiple entities"""
        
        # Build initial graph
        graph = self._build_entity_graph(entities)
        
        multi_hop_relationships = []
        
        # Find paths between entities
        for source in entities:
            for target in entities:
                if source.id != target.id:
                    paths = self._find_meaningful_paths(
                        graph, source, target, max_hops
                    )
                    
                    for path in paths:
                        # Analyze path significance
                        relationship = await self._analyze_path_relationship(path)
                        if relationship.significance > 0.7:
                            multi_hop_relationships.append(relationship)
        
        return multi_hop_relationships
    
    async def _analyze_path_relationship(self, path: List[Entity]) -> MultiHopRelationship:
        """Analyze the significance of a multi-hop path"""
        
        prompt = f"""
        Analyze this path between entities and determine if it represents a meaningful relationship:
        
        Path: {' -> '.join([f"{e.type}:{e.attributes.get('name', e.id)}" for e in path])}
        
        Entity details:
        {json.dumps([{"type": e.type, "attributes": e.attributes} for e in path], indent=2)}
        
        Consider:
        1. Business significance of the connection
        2. Strength of each hop in the path
        3. Whether this reveals hidden dependencies
        4. Impact on business metrics
        
        Return:
        - Relationship name
        - Significance score (0-1)
        - Business impact description
        """
        
        analysis = await self.llm.generate_json(prompt)
        
        return MultiHopRelationship(
            source=path[0],
            target=path[-1],
            path=path,
            relationship_type=analysis["relationship_name"],
            significance=analysis["significance"],
            impact=analysis["impact"]
        )
```

#### 2. Temporal Relationship Discovery
```python
class TemporalRelationshipDiscoverer:
    """Discover relationships based on temporal patterns"""
    
    async def discover_temporal_relationships(self, 
                                            entities: List[Entity],
                                            events: List[Event]) -> List[Relationship]:
        """Find relationships based on temporal correlation"""
        
        temporal_relationships = []
        
        # Group entities by temporal attributes
        temporal_entities = self._group_by_temporal_attributes(entities)
        
        # Analyze event sequences
        for entity_group in temporal_entities:
            correlated_events = await self._find_correlated_events(
                entity_group,
                events
            )
            
            for correlation in correlated_events:
                if correlation.confidence > 0.8:
                    rel = Relationship(
                        source_type=correlation.entity1.type,
                        source_id=correlation.entity1.id,
                        target_type=correlation.entity2.type,
                        target_id=correlation.entity2.id,
                        relationship_type="TEMPORALLY_CORRELATED",
                        properties={
                            "correlation_type": correlation.type,
                            "lag_days": correlation.lag,
                            "confidence": correlation.confidence
                        },
                        confidence=correlation.confidence
                    )
                    temporal_relationships.append(rel)
        
        return temporal_relationships
    
    async def _find_correlated_events(self, 
                                    entities: List[Entity],
                                    events: List[Event]) -> List[Correlation]:
        """Find temporal correlations between entity events"""
        
        correlations = []
        
        # Extract time series for each entity
        entity_timeseries = {
            entity.id: self._extract_timeseries(entity, events)
            for entity in entities
        }
        
        # Pairwise correlation analysis
        for e1, ts1 in entity_timeseries.items():
            for e2, ts2 in entity_timeseries.items():
                if e1 < e2:  # Avoid duplicates
                    correlation = self._calculate_correlation(ts1, ts2)
                    
                    if correlation.is_significant:
                        # Use LLM to interpret correlation
                        interpretation = await self._interpret_correlation(
                            entities[e1], entities[e2], correlation
                        )
                        
                        correlations.append(interpretation)
        
        return correlations
```

#### 3. Semantic Relationship Mining
```python
class SemanticRelationshipMiner:
    """Mine relationships from unstructured text using advanced NLP"""
    
    def __init__(self):
        self.relationship_extractor = RelationshipExtractor()
        self.embedder = Embedder()
        self.llm = LLM(model="gpt-4")
    
    async def mine_semantic_relationships(self, 
                                        documents: List[Document],
                                        entities: List[Entity]) -> List[Relationship]:
        """Extract relationships from document text"""
        
        relationships = []
        
        # Create entity mention index
        entity_mentions = await self._index_entity_mentions(documents, entities)
        
        for doc in documents:
            # Extract relationship candidates from text
            candidates = await self._extract_relationship_candidates(
                doc.text,
                entity_mentions[doc.id]
            )
            
            # Validate and score relationships
            for candidate in candidates:
                validated = await self._validate_relationship(
                    candidate,
                    entities,
                    doc.context
                )
                
                if validated.confidence > 0.7:
                    relationships.append(validated)
        
        # Cluster similar relationships
        clustered = await self._cluster_relationships(relationships)
        
        return clustered
    
    async def _extract_relationship_candidates(self, 
                                             text: str,
                                             entity_mentions: List[EntityMention]) -> List[RelationshipCandidate]:
        """Extract potential relationships from text"""
        
        prompt = f"""
        Extract relationships between entities in this text:
        
        Text: {text}
        
        Entity mentions: {[{"entity": m.entity_id, "text": m.text, "position": m.position} for m in entity_mentions]}
        
        Look for:
        1. Explicit relationships ("X works with Y", "A depends on B")
        2. Implicit relationships ("X mentioned alongside Y frequently")
        3. Causal relationships ("X led to Y", "Because of A, B happened")
        4. Hierarchical relationships ("X reports to Y", "A is part of B")
        5. Temporal relationships ("X before Y", "A triggered B")
        
        For each relationship, identify:
        - Source and target entities
        - Relationship type and direction
        - Supporting text excerpt
        - Confidence score
        """
        
        candidates = await self.llm.generate_json(prompt)
        
        return [
            RelationshipCandidate(
                source_id=c["source"],
                target_id=c["target"],
                relationship_type=c["type"],
                evidence=c["evidence"],
                confidence=c["confidence"]
            )
            for c in candidates["relationships"]
        ]
```

#### 4. Graph Pattern Recognition
```python
class GraphPatternRecognizer:
    """Recognize complex patterns in entity-relationship graphs"""
    
    async def recognize_patterns(self, 
                               entities: List[Entity],
                               relationships: List[Relationship]) -> List[GraphPattern]:
        """Identify meaningful patterns in the graph"""
        
        # Build NetworkX graph
        G = self._build_graph(entities, relationships)
        
        patterns = []
        
        # Hub detection (entities with many connections)
        hubs = self._detect_hubs(G)
        patterns.extend([
            GraphPattern(
                type="HUB",
                entities=[hub],
                description=f"{hub} is a central connector"
            )
            for hub in hubs
        ])
        
        # Triangle patterns (potential collaboration)
        triangles = self._find_triangles(G)
        for triangle in triangles:
            pattern = await self._analyze_triangle_pattern(triangle)
            if pattern.is_significant:
                patterns.append(pattern)
        
        # Chain patterns (dependency chains)
        chains = self._find_chains(G, min_length=3)
        for chain in chains:
            pattern = await self._analyze_chain_pattern(chain)
            patterns.append(pattern)
        
        # Community detection
        communities = self._detect_communities(G)
        for community in communities:
            pattern = GraphPattern(
                type="COMMUNITY",
                entities=list(community),
                description=await self._describe_community(community, G)
            )
            patterns.append(pattern)
        
        return patterns
```

## Integration with Existing Implementation

These enhanced capabilities integrate with the existing features:

1. **Feature 2.1 (Entity Extractor)** - Add the advanced entity resolution and type detection
2. **Feature 2.2 (Relationship Builder)** - Incorporate multi-hop, temporal, and semantic relationship discovery
3. **Feature 2.3 (GraphRAG Indexer)** - Use the enhanced entities and relationships for better indexing

## Testing Strategy

### Entity Extraction Tests
```python
async def test_multi_source_entity_resolution():
    """Test entity resolution across multiple sources"""
    extractor = AdvancedEntityExtractor()
    
    salesforce_data = [{"Id": "001", "Name": "Tech Corp"}]
    gainsight_data = [{"account_id": "TC001", "account_name": "TechCorp"}]
    
    entities = await extractor.extract_and_resolve_entities({
        "salesforce": salesforce_data,
        "gainsight": gainsight_data
    })
    
    # Should resolve to single entity
    assert len(entities) == 1
    assert entities[0].source_ids == {
        "salesforce": "001",
        "gainsight": "TC001"
    }

async def test_complex_entity_detection():
    """Test detection of complex entity types"""
    detector = EntityTypeDetector()
    
    text = """
    The Cloud Platform Team is working on Q4 revenue targets 
    while addressing the security risk identified last month.
    """
    
    entities = await detector.detect_entity_types(text)
    
    entity_types = [e.type for e in entities]
    assert "Team" in entity_types
    assert "Objective" in entity_types
    assert "Risk" in entity_types
```

### Relationship Discovery Tests
```python
async def test_multi_hop_relationships():
    """Test discovery of multi-hop relationships"""
    builder = MultiHopRelationshipBuilder()
    
    entities = [
        Entity(type="Customer", id="c1", attributes={"name": "TechCorp"}),
        Entity(type="Team", id="t1", attributes={"name": "Cloud Team"}),
        Entity(type="Project", id="p1", attributes={"name": "Migration", "team_id": "t1"}),
        Entity(type="Risk", id="r1", attributes={"project_id": "p1", "customer_impact": "c1"})
    ]
    
    relationships = await builder.build_multi_hop_relationships(entities, max_hops=3)
    
    # Should find Customer -> Team relationship through Project and Risk
    customer_team_rel = next(
        r for r in relationships 
        if r.source.id == "c1" and r.target.id == "t1"
    )
    assert customer_team_rel is not None
    assert len(customer_team_rel.path) == 4

async def test_temporal_correlation():
    """Test temporal relationship discovery"""
    discoverer = TemporalRelationshipDiscoverer()
    
    entities = [
        Entity(type="Customer", id="c1", attributes={"churn_date": "2024-03-15"}),
        Entity(type="Risk", id="r1", attributes={"identified_date": "2024-01-15"})
    ]
    
    events = [
        Event(entity_id="c1", type="support_ticket", date="2024-02-01"),
        Event(entity_id="c1", type="health_score_drop", date="2024-02-15")
    ]
    
    relationships = await discoverer.discover_temporal_relationships(entities, events)
    
    # Should find correlation between risk and churn
    assert any(r.properties["correlation_type"] == "risk_precedes_churn" for r in relationships)
```

## Performance Considerations

1. **Batch Processing**: Process entities in batches for LLM calls
2. **Caching**: Cache entity resolution results and relationship patterns
3. **Parallel Processing**: Use asyncio for concurrent operations
4. **Incremental Updates**: Only process new/changed entities

## Configuration

```yaml
# config/extraction.yaml
entity_extraction:
  resolution:
    similarity_threshold: 0.85
    use_llm_validation: true
    cache_ttl: 3600
  
  type_detection:
    patterns_file: "config/entity_patterns.json"
    llm_confidence_threshold: 0.7
    
relationship_discovery:
  multi_hop:
    max_hops: 3
    min_significance: 0.7
    
  temporal:
    correlation_window_days: 90
    min_correlation: 0.8
    
  semantic:
    evidence_threshold: 0.7
    cluster_similarity: 0.85
```

This enhanced entity and relationship extraction system will significantly improve the accuracy and completeness of the knowledge graph, leading to better query results.