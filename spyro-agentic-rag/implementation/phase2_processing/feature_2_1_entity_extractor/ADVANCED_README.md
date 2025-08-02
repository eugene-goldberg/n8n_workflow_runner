# Feature 2.1: Advanced Entity Extractor

## Overview
The Entity Extractor is responsible for identifying, extracting, validating, and enriching entities from raw data. This advanced version includes multi-source resolution, complex entity detection, and contextual enrichment.

## Status
✅ **Core Implementation Complete**

## Specifications

### Size
Medium (4-5 days) - Extended to Large (6-7 days) with advanced features

### Dependencies
- Feature 1.3 (Schema Mapper)
- Feature 1.4 (Change Detector)

### Core Capabilities

#### 1. Basic Entity Extraction
- Extract entities from mapped data
- Validate against schema
- Handle multiple entity types per record
- Auto-fix validation errors with LLM

#### 2. Advanced Entity Resolution
- Resolve duplicate entities across sources
- Match entities with different naming conventions
- Maintain source ID mappings
- Confidence scoring for matches

#### 3. Complex Entity Detection
- Pattern-based entity recognition
- LLM-based entity discovery
- Implicit entity identification
- Composite entity handling

#### 4. Contextual Enrichment
- Industry-specific enrichment
- Temporal context addition
- Relationship-based enrichment
- Derived attribute calculation

## Implementation Components

### 1. Base Entity Extractor
```python
class EntityExtractor:
    """Core entity extraction functionality"""
    
    async def extract_entities(self, raw_data: Dict, mapping: Dict) -> List[Entity]:
        # Map raw data to entities
        # Validate entities
        # Fix validation errors
        # Return entity list
```

### 2. Multi-Source Resolver
```python
class MultiSourceEntityResolver:
    """Resolve entities across multiple data sources"""
    
    async def resolve_duplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        # Group potential duplicates
        # Use fuzzy matching for names
        # Use LLM for complex cases
        # Merge entity attributes
```

### 3. Entity Type Detector
```python
class EntityTypeDetector:
    """Detect entity types from unstructured data"""
    
    async def detect_entity_types(self, text: str) -> List[DetectedEntity]:
        # Pattern-based detection
        # LLM-based detection
        # Confidence scoring
        # Span location tracking
```

### 4. Contextual Enricher
```python
class ContextualEnricher:
    """Enrich entities with derived and contextual data"""
    
    async def enrich_entity(self, entity: Entity, context: Dict) -> Entity:
        # Add industry context
        # Calculate temporal attributes
        # Derive tier/category
        # Add relationship context
```

## Advanced Features

### Entity Resolution Algorithm
```python
async def resolve_entities_with_llm(self, candidates: List[Entity]) -> Entity:
    """Use LLM to intelligently merge entities"""
    
    # Prepare entity comparison
    comparison_prompt = self._build_comparison_prompt(candidates)
    
    # Get LLM decision
    decision = await self.llm.analyze_entity_match(comparison_prompt)
    
    # Merge if match confirmed
    if decision.is_match:
        merged = self._merge_entity_attributes(candidates, decision.merge_strategy)
        return merged
    
    # Return highest confidence candidate
    return max(candidates, key=lambda e: e.confidence)
```

### Pattern-Based Detection
```yaml
# config/entity_patterns.yaml
patterns:
  Customer:
    - regex: '\b(?:customer|client|account)\s+(\w+)'
    - regex: '(\w+)\s+(?:Inc|Corp|LLC|Ltd)'
  
  Team:
    - regex: '(\w+)\s+(?:team|department|group)'
    - keywords: ['engineering', 'sales', 'support', 'platform']
  
  Risk:
    - keywords: ['risk', 'threat', 'vulnerability', 'issue']
    - context: ['identified', 'mitigated', 'addressed']
```

### Enrichment Rules
```python
enrichment_rules = {
    "Customer": {
        "size_mapping": {
            "employees": [
                (1, 50, "SMB"),
                (51, 500, "Mid-Market"),
                (501, None, "Enterprise")
            ]
        },
        "industry_context": {
            "technology": {"growth_rate": 0.15, "churn_risk": "medium"},
            "finance": {"growth_rate": 0.08, "churn_risk": "low"},
            "healthcare": {"growth_rate": 0.12, "churn_risk": "low"}
        }
    }
}
```

## Testing Strategy

### Unit Tests
```python
# Test basic extraction
async def test_extract_single_entity():
    extractor = EntityExtractor()
    raw_data = {"id": "123", "name": "TechCorp"}
    mapping = {
        "id": {"entity": "Customer", "field": "id"},
        "name": {"entity": "Customer", "field": "name"}
    }
    
    entities = await extractor.extract_entities(raw_data, mapping)
    assert len(entities) == 1
    assert entities[0].type == "Customer"

# Test multi-source resolution
async def test_resolve_duplicate_entities():
    resolver = MultiSourceEntityResolver()
    
    entities = [
        Entity(type="Customer", id="sf_123", attributes={"name": "Tech Corp"}),
        Entity(type="Customer", id="gs_456", attributes={"name": "TechCorp"})
    ]
    
    resolved = await resolver.resolve_duplicate_entities(entities)
    assert len(resolved) == 1
    assert resolved[0].source_ids == {"salesforce": "sf_123", "gainsight": "gs_456"}

# Test complex entity detection
async def test_detect_implicit_entities():
    detector = EntityTypeDetector()
    
    text = "The platform team is addressing the Q4 revenue risk"
    entities = await detector.detect_entity_types(text)
    
    types = [e.type for e in entities]
    assert "Team" in types
    assert "Risk" in types
    assert "Objective" in types
```

### Integration Tests
```python
# Test full extraction pipeline
async def test_full_extraction_pipeline():
    pipeline = EntityExtractionPipeline()
    
    # Multiple data sources
    sources = {
        "crm": [{"account": "TechCorp", "value": 500000}],
        "support": [{"customer": "Tech Corp", "tickets": 25}]
    }
    
    entities = await pipeline.extract_from_sources(sources)
    
    # Should resolve to single customer
    customers = [e for e in entities if e.type == "Customer"]
    assert len(customers) == 1
    assert customers[0].attributes["support_tickets"] == 25
```

### Performance Tests
```python
# Test extraction at scale
async def test_bulk_extraction_performance():
    extractor = EntityExtractor()
    
    # Generate 10k records
    records = generate_test_records(10000)
    
    start = time.time()
    entities = await extractor.extract_entities_bulk(records)
    duration = time.time() - start
    
    assert duration < 30  # Should process in under 30 seconds
    assert len(entities) >= 10000  # At least one entity per record
```

## Acceptance Criteria

### Core Requirements
- [ ] Extracts entities from mapped data
- [ ] Validates against schema
- [ ] Handles validation errors gracefully
- [ ] Supports batch processing

### Advanced Requirements
- [ ] Resolves entities across multiple sources
- [ ] Detects entities from unstructured text
- [ ] Enriches entities with contextual data
- [ ] Maintains source traceability
- [ ] Provides confidence scores

### Performance Requirements
- [ ] Processes 1000+ entities/second
- [ ] LLM calls optimized with batching
- [ ] Caching for resolved entities
- [ ] Memory efficient for large datasets

## Configuration

```yaml
# config/entity_extraction.yaml
extraction:
  validation:
    strict_mode: false
    auto_fix_errors: true
    required_fields:
      Customer: ["id", "name"]
      Product: ["id", "name", "category"]
  
  resolution:
    similarity_threshold: 0.85
    llm_validation: true
    merge_strategy: "most_complete"
  
  enrichment:
    enable_industry_context: true
    enable_derived_fields: true
    cache_enrichments: true
  
  performance:
    batch_size: 100
    max_concurrent_llm_calls: 5
    cache_ttl_seconds: 3600
```

## Implementation Priority

1. **Phase 1**: Basic extraction and validation
2. **Phase 2**: Multi-source resolution
3. **Phase 3**: Complex entity detection
4. **Phase 4**: Contextual enrichment

## Dependencies on Other Features

- **Schema Mapper**: For field mapping rules
- **Change Detector**: For incremental updates
- **LLM Service**: For validation and resolution
- **Cache Service**: For performance optimization

## Next Steps

1. Implement basic EntityExtractor class
2. Add validation framework
3. Implement multi-source resolver
4. Add entity type detection
5. Build enrichment pipeline
6. Optimize for performance