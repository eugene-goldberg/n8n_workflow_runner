# Detailed Implementation Plan - SpyroSolutions Agentic Ingestion Pipeline

## Overview
This plan breaks down the implementation into small, testable features that can be completed incrementally. Each feature includes clear acceptance criteria and testing procedures.

## Phase 1: Core Infrastructure (Weeks 1-4)

### Feature 1.1: Base Connector Framework
**Size**: Small (2-3 days)
**Dependencies**: None

#### Implementation:
```python
# src/connectors/base_connector.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any, AsyncIterator
from dataclasses import dataclass

@dataclass
class ConnectorConfig:
    name: str
    api_key: str
    base_url: str
    rate_limit: int = 100
    retry_count: int = 3

class BaseConnector(ABC):
    def __init__(self, config: ConnectorConfig):
        self.config = config
        self.session = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection and verify credentials"""
        pass
    
    @abstractmethod
    async def discover_schema(self) -> Dict[str, Any]:
        """Auto-discover available data and schema"""
        pass
    
    @abstractmethod
    async def fetch_data(self, entity_type: str, 
                        since: datetime = None) -> AsyncIterator[Dict]:
        """Fetch data with pagination support"""
        pass
    
    @abstractmethod
    async def get_sample_data(self, entity_type: str, 
                             limit: int = 5) -> List[Dict]:
        """Get sample records for testing"""
        pass
```

#### Testing:
```python
# tests/test_base_connector.py
async def test_connector_interface():
    """Verify all connectors implement required methods"""
    config = ConnectorConfig(name="test", api_key="test", base_url="http://test")
    
    # Should not be instantiable
    with pytest.raises(TypeError):
        BaseConnector(config)
```

#### Acceptance Criteria:
- [ ] Base abstract class defined
- [ ] Config dataclass with validation
- [ ] Rate limiting interface
- [ ] Error handling interface
- [ ] Unit tests pass

---

### Feature 1.2: Mock Data Connector
**Size**: Small (1-2 days)
**Dependencies**: Feature 1.1

#### Implementation:
```python
# src/connectors/mock_connector.py
class MockConnector(BaseConnector):
    """Mock connector for testing without real APIs"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.mock_data = self._generate_mock_data()
    
    async def connect(self) -> bool:
        await asyncio.sleep(0.1)  # Simulate network delay
        return True
    
    async def discover_schema(self) -> Dict[str, Any]:
        return {
            "customers": {
                "fields": ["id", "name", "size", "industry"],
                "count": 100
            },
            "subscriptions": {
                "fields": ["id", "customer_id", "product", "mrr"],
                "count": 150
            }
        }
    
    async def fetch_data(self, entity_type: str, 
                        since: datetime = None) -> AsyncIterator[Dict]:
        data = self.mock_data.get(entity_type, [])
        for record in data:
            if since and record.get("updated_at") < since:
                continue
            yield record
```

#### Testing:
```python
# tests/test_mock_connector.py
async def test_mock_connector_fetch():
    connector = MockConnector(test_config)
    assert await connector.connect()
    
    # Test schema discovery
    schema = await connector.discover_schema()
    assert "customers" in schema
    
    # Test data fetching
    customers = []
    async for customer in connector.fetch_data("customers"):
        customers.append(customer)
    assert len(customers) > 0
```

#### Acceptance Criteria:
- [ ] Mock connector implements all base methods
- [ ] Generates realistic test data
- [ ] Supports pagination simulation
- [ ] Handles date filtering
- [ ] Integration tests pass

---

### Feature 1.3: Schema Mapper
**Size**: Medium (3-4 days)
**Dependencies**: Feature 1.1

#### Implementation:
```python
# src/ingestion/schema_mapper.py
class SchemaMapper:
    """Maps external schemas to SpyroSolutions entities"""
    
    def __init__(self):
        self.mapping_rules = self._load_default_mappings()
        self.llm = LLM(model="gpt-4")
    
    async def auto_map_schema(self, source_schema: Dict, 
                             target_entities: List[str]) -> Dict[str, Dict]:
        """Use LLM to intelligently map source fields to target entities"""
        
        prompt = f"""
        Map these source fields to target entities:
        
        Source Schema: {json.dumps(source_schema, indent=2)}
        Target Entities: {target_entities}
        
        Consider:
        1. Semantic meaning of field names
        2. Data types and constraints
        3. Common patterns (e.g., 'customer_id' -> Customer.id)
        
        Return a mapping dictionary.
        """
        
        mapping = await self.llm.generate_json(prompt)
        return self._validate_mapping(mapping)
    
    def apply_mapping(self, source_data: Dict, 
                     mapping: Dict) -> Dict[str, Any]:
        """Transform source data to target schema"""
        transformed = {}
        for source_field, target_spec in mapping.items():
            if source_field in source_data:
                target_entity = target_spec["entity"]
                target_field = target_spec["field"]
                transform_fn = target_spec.get("transform")
                
                if target_entity not in transformed:
                    transformed[target_entity] = {}
                
                value = source_data[source_field]
                if transform_fn:
                    value = self._apply_transform(value, transform_fn)
                
                transformed[target_entity][target_field] = value
        
        return transformed
```

#### Testing:
```python
# tests/test_schema_mapper.py
async def test_auto_mapping():
    mapper = SchemaMapper()
    
    source_schema = {
        "accounts": {
            "fields": ["id", "name", "annual_revenue", "employee_count"]
        }
    }
    
    mapping = await mapper.auto_map_schema(
        source_schema, 
        ["Customer", "SaaSSubscription"]
    )
    
    assert mapping["accounts"]["name"]["entity"] == "Customer"
    assert mapping["accounts"]["annual_revenue"]["entity"] == "SaaSSubscription"

def test_apply_mapping():
    mapper = SchemaMapper()
    
    source_data = {
        "id": "123",
        "name": "TechCorp",
        "annual_revenue": 1000000
    }
    
    mapping = {
        "id": {"entity": "Customer", "field": "external_id"},
        "name": {"entity": "Customer", "field": "name"},
        "annual_revenue": {"entity": "SaaSSubscription", "field": "arr"}
    }
    
    result = mapper.apply_mapping(source_data, mapping)
    assert result["Customer"]["name"] == "TechCorp"
    assert result["SaaSSubscription"]["arr"] == 1000000
```

#### Acceptance Criteria:
- [ ] LLM-powered auto-mapping
- [ ] Manual mapping override support
- [ ] Transform function support
- [ ] Validation of mappings
- [ ] Unit and integration tests pass

---

### Feature 1.4: Change Detection System
**Size**: Medium (3-4 days)
**Dependencies**: Features 1.1, 1.2

#### Implementation:
```python
# src/ingestion/change_detector.py
@dataclass
class Change:
    entity_type: str
    entity_id: str
    operation: str  # create, update, delete
    fields_changed: List[str]
    old_values: Dict[str, Any]
    new_values: Dict[str, Any]
    timestamp: datetime

class ChangeDetector:
    """Detects changes in data for incremental updates"""
    
    def __init__(self, state_store: StateStore):
        self.state_store = state_store
        self.significance_rules = self._load_significance_rules()
    
    async def detect_changes(self, entity_type: str, 
                           new_data: List[Dict]) -> List[Change]:
        """Compare new data with stored state to find changes"""
        
        changes = []
        existing_state = await self.state_store.get_state(entity_type)
        
        # Index existing data
        existing_map = {item["id"]: item for item in existing_state}
        new_map = {item["id"]: item for item in new_data}
        
        # Find creates
        for id, item in new_map.items():
            if id not in existing_map:
                changes.append(Change(
                    entity_type=entity_type,
                    entity_id=id,
                    operation="create",
                    fields_changed=list(item.keys()),
                    old_values={},
                    new_values=item,
                    timestamp=datetime.now()
                ))
        
        # Find updates
        for id, new_item in new_map.items():
            if id in existing_map:
                old_item = existing_map[id]
                changed_fields = []
                old_values = {}
                new_values = {}
                
                for field, new_value in new_item.items():
                    old_value = old_item.get(field)
                    if old_value != new_value:
                        changed_fields.append(field)
                        old_values[field] = old_value
                        new_values[field] = new_value
                
                if changed_fields:
                    changes.append(Change(
                        entity_type=entity_type,
                        entity_id=id,
                        operation="update",
                        fields_changed=changed_fields,
                        old_values=old_values,
                        new_values=new_values,
                        timestamp=datetime.now()
                    ))
        
        # Find deletes
        for id in existing_map:
            if id not in new_map:
                changes.append(Change(
                    entity_type=entity_type,
                    entity_id=id,
                    operation="delete",
                    fields_changed=[],
                    old_values=existing_map[id],
                    new_values={},
                    timestamp=datetime.now()
                ))
        
        # Update state
        await self.state_store.update_state(entity_type, new_data)
        
        return changes
    
    def is_significant(self, change: Change) -> bool:
        """Determine if a change is significant enough to process"""
        
        # Always process creates and deletes
        if change.operation in ["create", "delete"]:
            return True
        
        # Check significance rules for updates
        rules = self.significance_rules.get(change.entity_type, {})
        
        # Check if any significant field changed
        significant_fields = rules.get("significant_fields", [])
        if any(field in change.fields_changed for field in significant_fields):
            return True
        
        # Check threshold rules
        for field in change.fields_changed:
            if field in rules.get("thresholds", {}):
                threshold = rules["thresholds"][field]
                old = change.old_values.get(field, 0)
                new = change.new_values.get(field, 0)
                
                if abs(new - old) >= threshold:
                    return True
        
        return False
```

#### Testing:
```python
# tests/test_change_detector.py
async def test_detect_creates():
    state_store = InMemoryStateStore()
    detector = ChangeDetector(state_store)
    
    # Initial empty state
    changes = await detector.detect_changes("customers", [
        {"id": "1", "name": "TechCorp", "size": "Enterprise"}
    ])
    
    assert len(changes) == 1
    assert changes[0].operation == "create"
    assert changes[0].entity_id == "1"

async def test_detect_updates():
    state_store = InMemoryStateStore()
    detector = ChangeDetector(state_store)
    
    # Set initial state
    await detector.detect_changes("customers", [
        {"id": "1", "name": "TechCorp", "size": "Enterprise"}
    ])
    
    # Update data
    changes = await detector.detect_changes("customers", [
        {"id": "1", "name": "TechCorp", "size": "SMB"}
    ])
    
    assert len(changes) == 1
    assert changes[0].operation == "update"
    assert "size" in changes[0].fields_changed

def test_significance_rules():
    detector = ChangeDetector(InMemoryStateStore())
    
    # ARR change > 10% is significant
    change = Change(
        entity_type="subscription",
        entity_id="1",
        operation="update",
        fields_changed=["arr"],
        old_values={"arr": 100000},
        new_values={"arr": 115000},
        timestamp=datetime.now()
    )
    
    assert detector.is_significant(change) == True
```

#### Acceptance Criteria:
- [ ] Detects creates, updates, deletes
- [ ] Maintains state between runs
- [ ] Significance rules configurable
- [ ] Handles large datasets efficiently
- [ ] Comprehensive test coverage

---

## Phase 2: Data Processing Pipeline (Weeks 5-8)

### Feature 2.1: Entity Extractor
**Size**: Medium (4-5 days)
**Dependencies**: Features 1.3, 1.4

#### Implementation:
```python
# src/processing/entity_extractor.py
class EntityExtractor:
    """Extracts and validates entities from raw data"""
    
    def __init__(self, schema_mapper: SchemaMapper):
        self.schema_mapper = schema_mapper
        self.validators = self._load_validators()
        self.llm = LLM(model="gpt-4")
    
    async def extract_entities(self, raw_data: Dict, 
                             mapping: Dict) -> List[Entity]:
        """Extract entities with validation and enrichment"""
        
        # Apply schema mapping
        mapped_data = self.schema_mapper.apply_mapping(raw_data, mapping)
        
        entities = []
        for entity_type, attributes in mapped_data.items():
            # Validate required fields
            validator = self.validators.get(entity_type)
            if validator:
                validation_result = validator.validate(attributes)
                if not validation_result.is_valid:
                    # Attempt to fix with LLM
                    attributes = await self._fix_validation_errors(
                        entity_type, attributes, validation_result.errors
                    )
            
            # Create entity
            entity = Entity(
                type=entity_type,
                id=attributes.get("id"),
                attributes=attributes,
                extracted_at=datetime.now()
            )
            
            entities.append(entity)
        
        return entities
    
    async def _fix_validation_errors(self, entity_type: str, 
                                   attributes: Dict, 
                                   errors: List[str]) -> Dict:
        """Use LLM to fix validation errors"""
        
        prompt = f"""
        Fix these validation errors for {entity_type}:
        
        Data: {json.dumps(attributes, indent=2)}
        Errors: {errors}
        
        Return corrected data that passes validation.
        """
        
        corrected = await self.llm.generate_json(prompt)
        return corrected
    
    async def enrich_entity(self, entity: Entity) -> Entity:
        """Enrich entity with derived attributes"""
        
        enrichments = {}
        
        # Example: Calculate customer tier
        if entity.type == "Customer":
            if "arr" in entity.attributes:
                arr = entity.attributes["arr"]
                if arr > 1000000:
                    enrichments["tier"] = "Enterprise"
                elif arr > 100000:
                    enrichments["tier"] = "Mid-Market"
                else:
                    enrichments["tier"] = "SMB"
        
        # Example: Extract sentiment from text
        if entity.type == "CustomerConcern":
            if "description" in entity.attributes:
                sentiment = await self._analyze_sentiment(
                    entity.attributes["description"]
                )
                enrichments["sentiment"] = sentiment
        
        entity.attributes.update(enrichments)
        return entity
```

#### Testing:
```python
# tests/test_entity_extractor.py
async def test_entity_extraction():
    mapper = SchemaMapper()
    extractor = EntityExtractor(mapper)
    
    raw_data = {
        "account_id": "123",
        "company_name": "TechCorp",
        "contract_value": 500000
    }
    
    mapping = {
        "account_id": {"entity": "Customer", "field": "id"},
        "company_name": {"entity": "Customer", "field": "name"},
        "contract_value": {"entity": "SaaSSubscription", "field": "arr"}
    }
    
    entities = await extractor.extract_entities(raw_data, mapping)
    
    assert len(entities) == 2
    assert entities[0].type == "Customer"
    assert entities[0].attributes["name"] == "TechCorp"

async def test_entity_enrichment():
    extractor = EntityExtractor(SchemaMapper())
    
    entity = Entity(
        type="Customer",
        id="123",
        attributes={"name": "TechCorp", "arr": 1500000}
    )
    
    enriched = await extractor.enrich_entity(entity)
    assert enriched.attributes["tier"] == "Enterprise"
```

#### Acceptance Criteria:
- [ ] Extracts multiple entity types from single record
- [ ] Validates entities against schema
- [ ] Auto-fixes validation errors with LLM
- [ ] Enriches entities with derived fields
- [ ] Handles missing/malformed data gracefully

---

### Feature 2.2: Relationship Builder
**Size**: Large (5-6 days)
**Dependencies**: Feature 2.1

#### Implementation:
```python
# src/processing/relationship_builder.py
@dataclass
class Relationship:
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relationship_type: str
    properties: Dict[str, Any]
    confidence: float

class RelationshipBuilder:
    """Discovers and builds relationships between entities"""
    
    def __init__(self):
        self.explicit_rules = self._load_explicit_rules()
        self.llm = LLM(model="gpt-4")
        self.embedder = Embedder()
    
    async def build_relationships(self, entities: List[Entity]) -> List[Relationship]:
        """Build relationships using multiple strategies"""
        
        relationships = []
        
        # 1. Explicit ID-based relationships
        explicit_rels = self._build_explicit_relationships(entities)
        relationships.extend(explicit_rels)
        
        # 2. Inferred semantic relationships
        semantic_rels = await self._infer_semantic_relationships(entities)
        relationships.extend(semantic_rels)
        
        # 3. Temporal relationships
        temporal_rels = self._build_temporal_relationships(entities)
        relationships.extend(temporal_rels)
        
        # 4. Hierarchical relationships
        hierarchical_rels = self._build_hierarchical_relationships(entities)
        relationships.extend(hierarchical_rels)
        
        # Deduplicate and resolve conflicts
        relationships = self._deduplicate_relationships(relationships)
        
        return relationships
    
    def _build_explicit_relationships(self, entities: List[Entity]) -> List[Relationship]:
        """Build relationships based on explicit IDs"""
        
        relationships = []
        entity_map = {(e.type, e.id): e for e in entities}
        
        for entity in entities:
            for field, value in entity.attributes.items():
                # Check if field references another entity
                for rule in self.explicit_rules:
                    if rule.matches(entity.type, field):
                        target_type = rule.target_type
                        target_id = value
                        
                        if (target_type, target_id) in entity_map:
                            rel = Relationship(
                                source_type=entity.type,
                                source_id=entity.id,
                                target_type=target_type,
                                target_id=target_id,
                                relationship_type=rule.relationship_type,
                                properties={},
                                confidence=1.0
                            )
                            relationships.append(rel)
        
        return relationships
    
    async def _infer_semantic_relationships(self, entities: List[Entity]) -> List[Relationship]:
        """Use LLM to infer non-obvious relationships"""
        
        relationships = []
        
        # Group entities by type for efficient processing
        entities_by_type = defaultdict(list)
        for entity in entities:
            entities_by_type[entity.type].append(entity)
        
        # Check for semantic relationships between different types
        for type1, entities1 in entities_by_type.items():
            for type2, entities2 in entities_by_type.items():
                if type1 >= type2:  # Avoid duplicates
                    continue
                
                # Sample entities for LLM analysis
                sample1 = entities1[:5]
                sample2 = entities2[:5]
                
                prompt = f"""
                Find relationships between these entity types:
                
                {type1} entities: {[e.attributes for e in sample1]}
                {type2} entities: {[e.attributes for e in sample2]}
                
                Look for:
                1. Implicit references (e.g., team names in descriptions)
                2. Shared attributes or patterns
                3. Business logic connections
                
                Return relationships with confidence scores.
                """
                
                inferred = await self.llm.generate_json(prompt)
                
                for rel_spec in inferred.get("relationships", []):
                    if rel_spec["confidence"] > 0.7:
                        rel = Relationship(
                            source_type=type1,
                            source_id=rel_spec["source_id"],
                            target_type=type2,
                            target_id=rel_spec["target_id"],
                            relationship_type=rel_spec["type"],
                            properties=rel_spec.get("properties", {}),
                            confidence=rel_spec["confidence"]
                        )
                        relationships.append(rel)
        
        return relationships
```

#### Testing:
```python
# tests/test_relationship_builder.py
async def test_explicit_relationships():
    builder = RelationshipBuilder()
    
    entities = [
        Entity(type="Customer", id="c1", attributes={"name": "TechCorp"}),
        Entity(type="SaaSSubscription", id="s1", attributes={"customer_id": "c1", "product": "SpyroCloud"})
    ]
    
    relationships = await builder.build_relationships(entities)
    
    # Should find Customer -> Subscription relationship
    customer_sub_rel = next(
        r for r in relationships 
        if r.source_id == "s1" and r.target_id == "c1"
    )
    assert customer_sub_rel.relationship_type == "BELONGS_TO"

async def test_semantic_inference():
    builder = RelationshipBuilder()
    
    entities = [
        Entity(type="Customer", id="c1", attributes={"name": "TechCorp", "description": "Working with Cloud Platform Team"}),
        Entity(type="Team", id="t1", attributes={"name": "Cloud Platform Team"})
    ]
    
    relationships = await builder.build_relationships(entities)
    
    # Should infer relationship from description
    assert any(
        r.source_id == "c1" and r.target_id == "t1" 
        for r in relationships
    )
```

#### Acceptance Criteria:
- [ ] Builds explicit ID-based relationships
- [ ] Infers semantic relationships with LLM
- [ ] Handles temporal relationships
- [ ] Builds hierarchical relationships
- [ ] Confidence scoring for inferred relationships
- [ ] Deduplication and conflict resolution

---

### Feature 2.3: GraphRAG Indexer
**Size**: Large (5-6 days)
**Dependencies**: Features 2.1, 2.2

#### Implementation:
```python
# src/processing/graphrag_indexer.py
class GraphRAGIndexer:
    """Implements GraphRAG indexing for enhanced retrieval"""
    
    def __init__(self, neo4j_driver, vector_store):
        self.neo4j = neo4j_driver
        self.vector_store = vector_store
        self.chunker = SemanticChunker()
        self.llm = LLM(model="gpt-4")
    
    async def index_documents(self, documents: List[Document]) -> IndexResult:
        """Index documents using GraphRAG methodology"""
        
        # Step 1: Semantic chunking
        all_chunks = []
        for doc in documents:
            chunks = await self.chunker.chunk_document(
                doc,
                method="SPLICE",
                min_size=256,
                max_size=1024,
                preserve_structure=True
            )
            all_chunks.extend(chunks)
        
        # Step 2: Extract entities and relationships from chunks
        graph_elements = []
        for chunk in all_chunks:
            elements = await self._extract_graph_elements(chunk)
            graph_elements.extend(elements)
        
        # Step 3: Build communities for global queries
        communities = await self._build_communities(graph_elements)
        
        # Step 4: Generate community summaries
        summaries = await self._generate_summaries(communities)
        
        # Step 5: Store in Neo4j and vector store
        await self._store_graph_data(graph_elements, communities, summaries)
        
        # Step 6: Create embeddings for chunks
        await self._create_embeddings(all_chunks)
        
        return IndexResult(
            chunks_processed=len(all_chunks),
            entities_created=sum(len(e.entities) for e in graph_elements),
            relationships_created=sum(len(e.relationships) for e in graph_elements),
            communities_detected=len(communities)
        )
    
    async def _extract_graph_elements(self, chunk: Chunk) -> List[GraphElement]:
        """Extract entities, relationships, and claims from chunk"""
        
        prompt = f"""
        Extract graph elements from this text:
        
        {chunk.text}
        
        Extract:
        1. Entities (with type and properties)
        2. Relationships between entities
        3. Key claims or facts
        
        Return structured JSON.
        """
        
        extraction = await self.llm.generate_json(prompt)
        
        return GraphElement(
            chunk_id=chunk.id,
            entities=extraction["entities"],
            relationships=extraction["relationships"],
            claims=extraction["claims"]
        )
    
    async def _build_communities(self, elements: List[GraphElement]) -> List[Community]:
        """Detect communities in the graph for hierarchical summarization"""
        
        # Build NetworkX graph
        G = nx.Graph()
        
        for element in elements:
            # Add nodes
            for entity in element.entities:
                G.add_node(entity["id"], **entity)
            
            # Add edges
            for rel in element.relationships:
                G.add_edge(rel["source"], rel["target"], **rel)
        
        # Detect communities using Louvain algorithm
        communities = nx.community.louvain_communities(G)
        
        # Convert to Community objects
        community_objects = []
        for i, nodes in enumerate(communities):
            community = Community(
                id=f"community_{i}",
                nodes=list(nodes),
                size=len(nodes),
                density=nx.density(G.subgraph(nodes))
            )
            community_objects.append(community)
        
        return community_objects
    
    async def _generate_summaries(self, communities: List[Community]) -> Dict[str, str]:
        """Generate summaries for each community"""
        
        summaries = {}
        
        for community in communities:
            # Get all text chunks related to community nodes
            relevant_chunks = await self._get_community_chunks(community)
            
            prompt = f"""
            Summarize the main themes and insights from this community of related information:
            
            Nodes: {community.nodes}
            Text samples: {relevant_chunks[:3]}
            
            Provide a concise summary for answering global questions.
            """
            
            summary = await self.llm.generate(prompt)
            summaries[community.id] = summary
        
        return summaries
```

#### Testing:
```python
# tests/test_graphrag_indexer.py
async def test_document_indexing():
    neo4j_driver = create_test_driver()
    vector_store = InMemoryVectorStore()
    indexer = GraphRAGIndexer(neo4j_driver, vector_store)
    
    documents = [
        Document("TechCorp signed a 3-year contract for SpyroCloud with $500k ARR"),
        Document("The Cloud Platform Team is working on multi-region deployment for TechCorp")
    ]
    
    result = await indexer.index_documents(documents)
    
    assert result.chunks_processed > 0
    assert result.entities_created >= 4  # TechCorp, SpyroCloud, Contract, Team
    assert result.relationships_created >= 3
    assert result.communities_detected >= 1

async def test_community_detection():
    indexer = GraphRAGIndexer(test_driver, test_store)
    
    # Create test graph elements
    elements = [
        GraphElement(
            chunk_id="1",
            entities=[
                {"id": "c1", "type": "Customer", "name": "TechCorp"},
                {"id": "p1", "type": "Product", "name": "SpyroCloud"}
            ],
            relationships=[
                {"source": "c1", "target": "p1", "type": "USES"}
            ]
        )
    ]
    
    communities = await indexer._build_communities(elements)
    assert len(communities) >= 1
```

#### Acceptance Criteria:
- [ ] Implements SPLICE semantic chunking
- [ ] Extracts entities and relationships from text
- [ ] Detects graph communities
- [ ] Generates community summaries
- [ ] Stores in both Neo4j and vector store
- [ ] Handles large documents efficiently

---

## Phase 3: Real-time Ingestion (Weeks 9-12)

### Feature 3.1: Event Stream Processor
**Size**: Medium (4-5 days)
**Dependencies**: Features 2.1, 2.2, 2.3

#### Implementation:
```python
# src/ingestion/stream_processor.py
class StreamProcessor:
    """Processes real-time event streams"""
    
    def __init__(self, entity_extractor, relationship_builder, graph_updater):
        self.entity_extractor = entity_extractor
        self.relationship_builder = relationship_builder
        self.graph_updater = graph_updater
        self.event_queue = asyncio.Queue()
        self.processing_semaphore = asyncio.Semaphore(10)
    
    async def process_event_stream(self):
        """Main event processing loop"""
        
        while True:
            try:
                # Get batch of events (with timeout)
                events = await self._get_event_batch(
                    max_size=100,
                    timeout=1.0
                )
                
                if events:
                    await self._process_batch(events)
                    
            except Exception as e:
                logger.error(f"Stream processing error: {e}")
                await asyncio.sleep(1)
    
    async def _process_batch(self, events: List[Event]):
        """Process a batch of events"""
        
        async with self.processing_semaphore:
            # Group events by entity type
            events_by_type = defaultdict(list)
            for event in events:
                events_by_type[event.entity_type].append(event)
            
            # Process each entity type
            for entity_type, type_events in events_by_type.items():
                # Extract entities
                entities = []
                for event in type_events:
                    extracted = await self.entity_extractor.extract_entities(
                        event.data,
                        event.mapping
                    )
                    entities.extend(extracted)
                
                # Build relationships
                relationships = await self.relationship_builder.build_relationships(
                    entities
                )
                
                # Update graph
                await self.graph_updater.update_incrementally(
                    entities,
                    relationships
                )
    
    async def add_event(self, event: Event):
        """Add event to processing queue"""
        await self.event_queue.put(event)
    
    async def get_status(self) -> StreamStatus:
        """Get current stream processing status"""
        return StreamStatus(
            queue_size=self.event_queue.qsize(),
            events_processed=self.events_processed,
            last_processed=self.last_processed_time,
            errors=self.error_count
        )
```

#### Testing:
```python
# tests/test_stream_processor.py
async def test_event_processing():
    processor = create_test_processor()
    
    # Add test event
    event = Event(
        entity_type="Customer",
        operation="update",
        data={"id": "123", "name": "TechCorp", "size": "Enterprise"},
        mapping={"id": {"entity": "Customer", "field": "id"}}
    )
    
    await processor.add_event(event)
    
    # Process events
    await processor._process_batch([event])
    
    # Verify graph was updated
    status = await processor.get_status()
    assert status.events_processed == 1

async def test_batch_processing():
    processor = create_test_processor()
    
    # Add multiple events
    events = [
        Event(entity_type="Customer", operation="create", data={"id": f"c{i}"})
        for i in range(10)
    ]
    
    for event in events:
        await processor.add_event(event)
    
    # Should process as batch
    batch = await processor._get_event_batch(max_size=5)
    assert len(batch) == 5
```

#### Acceptance Criteria:
- [ ] Processes events in real-time
- [ ] Batches events for efficiency
- [ ] Handles backpressure
- [ ] Maintains processing statistics
- [ ] Error recovery and retry logic

---

### Feature 3.2: Webhook API
**Size**: Small (2-3 days)
**Dependencies**: Feature 3.1

#### Implementation:
```python
# src/api/webhook_endpoints.py
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel

class WebhookEvent(BaseModel):
    source: str
    entity_type: str
    operation: str
    data: Dict[str, Any]
    timestamp: datetime

app = FastAPI()

@app.post("/webhook/{source}")
async def receive_webhook(
    source: str,
    event: WebhookEvent,
    x_api_key: str = Header(None)
):
    """Receive webhook events from external systems"""
    
    # Validate API key
    if not await validate_api_key(source, x_api_key):
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Get connector configuration
    connector_config = await get_connector_config(source)
    if not connector_config:
        raise HTTPException(status_code=404, detail="Unknown source")
    
    # Transform event to internal format
    internal_event = Event(
        source=source,
        entity_type=event.entity_type,
        operation=event.operation,
        data=event.data,
        mapping=connector_config.mapping,
        received_at=datetime.now()
    )
    
    # Add to processing queue
    await stream_processor.add_event(internal_event)
    
    return {
        "status": "accepted",
        "event_id": internal_event.id,
        "queue_position": await stream_processor.get_queue_position(internal_event.id)
    }

@app.get("/webhook/status/{event_id}")
async def get_event_status(event_id: str):
    """Check processing status of a webhook event"""
    
    status = await stream_processor.get_event_status(event_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "event_id": event_id,
        "status": status.state,  # queued, processing, completed, failed
        "processed_at": status.processed_at,
        "error": status.error_message if status.state == "failed" else None
    }
```

#### Testing:
```python
# tests/test_webhook_api.py
async def test_webhook_reception():
    async with AsyncClient(app=app) as client:
        event = {
            "source": "salesforce",
            "entity_type": "Account",
            "operation": "update",
            "data": {"Id": "123", "Name": "TechCorp"},
            "timestamp": datetime.now().isoformat()
        }
        
        response = await client.post(
            "/webhook/salesforce",
            json=event,
            headers={"X-API-Key": "test-key"}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == "accepted"

async def test_webhook_authentication():
    async with AsyncClient(app=app) as client:
        response = await client.post(
            "/webhook/salesforce",
            json={"data": {}},
            headers={"X-API-Key": "invalid-key"}
        )
        
        assert response.status_code == 401
```

#### Acceptance Criteria:
- [ ] REST endpoint for webhooks
- [ ] Authentication via API keys
- [ ] Source validation
- [ ] Event transformation
- [ ] Status tracking endpoint
- [ ] Rate limiting

---

### Feature 3.3: Incremental Graph Updater
**Size**: Large (5-6 days)
**Dependencies**: Features 2.3, 3.1

#### Implementation:
```python
# src/processing/graph_updater.py
class IncrementalGraphUpdater:
    """Updates graph incrementally without full rebuild"""
    
    def __init__(self, neo4j_driver, vector_store):
        self.neo4j = neo4j_driver
        self.vector_store = vector_store
        self.update_queue = asyncio.Queue()
        self.bi_temporal_tracker = BiTemporalTracker()
    
    async def update_incrementally(self, entities: List[Entity], 
                                  relationships: List[Relationship]):
        """Apply incremental updates to graph"""
        
        async with self.neo4j.session() as session:
            # Start transaction
            async with session.begin_transaction() as tx:
                try:
                    # Update entities
                    for entity in entities:
                        await self._update_entity(tx, entity)
                    
                    # Update relationships
                    for rel in relationships:
                        await self._update_relationship(tx, rel)
                    
                    # Update bi-temporal tracking
                    await self._update_temporal_data(tx, entities, relationships)
                    
                    # Commit transaction
                    await tx.commit()
                    
                    # Update vector embeddings asynchronously
                    asyncio.create_task(
                        self._update_embeddings(entities)
                    )
                    
                except Exception as e:
                    await tx.rollback()
                    raise UpdateError(f"Failed to update graph: {e}")
    
    async def _update_entity(self, tx, entity: Entity):
        """Update or create entity with bi-temporal tracking"""
        
        # Check if entity exists
        result = await tx.run(
            """
            MATCH (e:{type} {{id: $id}})
            RETURN e, e.valid_from as valid_from, e.valid_to as valid_to
            """.format(type=entity.type),
            id=entity.id
        )
        
        existing = await result.single()
        
        if existing:
            # Bi-temporal update: close previous version
            await tx.run(
                """
                MATCH (e:{type} {{id: $id}})
                WHERE e.valid_to IS NULL
                SET e.valid_to = $now,
                    e.transaction_to = $now
                """.format(type=entity.type),
                id=entity.id,
                now=datetime.now()
            )
            
            # Create new version
            await tx.run(
                """
                CREATE (e:{type} $props)
                SET e.id = $id,
                    e.valid_from = $now,
                    e.valid_to = null,
                    e.transaction_from = $now,
                    e.transaction_to = null
                """.format(type=entity.type),
                id=entity.id,
                props=entity.attributes,
                now=datetime.now()
            )
        else:
            # Create new entity
            await tx.run(
                """
                CREATE (e:{type} $props)
                SET e.id = $id,
                    e.valid_from = $now,
                    e.valid_to = null,
                    e.transaction_from = $now,
                    e.transaction_to = null
                """.format(type=entity.type),
                id=entity.id,
                props=entity.attributes,
                now=datetime.now()
            )
    
    async def _update_embeddings(self, entities: List[Entity]):
        """Update vector embeddings for changed entities"""
        
        for entity in entities:
            # Generate text representation
            text = self._entity_to_text(entity)
            
            # Create embedding
            embedding = await self.embedder.embed(text)
            
            # Update vector store
            await self.vector_store.upsert(
                id=f"{entity.type}_{entity.id}",
                embedding=embedding,
                metadata={
                    "type": entity.type,
                    "id": entity.id,
                    "attributes": entity.attributes,
                    "updated_at": datetime.now()
                }
            )
```

#### Testing:
```python
# tests/test_graph_updater.py
async def test_incremental_update():
    updater = IncrementalGraphUpdater(test_driver, test_store)
    
    # Create initial entity
    entity1 = Entity(
        type="Customer",
        id="c1",
        attributes={"name": "TechCorp", "size": "SMB"}
    )
    
    await updater.update_incrementally([entity1], [])
    
    # Update entity
    entity2 = Entity(
        type="Customer",
        id="c1",
        attributes={"name": "TechCorp", "size": "Enterprise"}
    )
    
    await updater.update_incrementally([entity2], [])
    
    # Verify bi-temporal versioning
    async with test_driver.session() as session:
        result = await session.run(
            """
            MATCH (c:Customer {id: 'c1'})
            RETURN c.size as size, c.valid_to as valid_to
            ORDER BY c.transaction_from DESC
            """
        )
        
        records = [r async for r in result]
        assert len(records) == 2
        assert records[0]["size"] == "Enterprise"
        assert records[0]["valid_to"] is None  # Current version
        assert records[1]["size"] == "SMB"
        assert records[1]["valid_to"] is not None  # Historical

async def test_embedding_update():
    updater = IncrementalGraphUpdater(test_driver, test_store)
    
    entity = Entity(
        type="Product",
        id="p1",
        attributes={"name": "SpyroCloud", "description": "Cloud platform"}
    )
    
    await updater.update_incrementally([entity], [])
    
    # Wait for async embedding update
    await asyncio.sleep(0.1)
    
    # Verify embedding was created
    result = await test_store.search(
        query="cloud platform",
        filter={"type": "Product"}
    )
    
    assert len(result) > 0
    assert result[0].metadata["id"] == "p1"
```

#### Acceptance Criteria:
- [ ] Incremental entity updates
- [ ] Incremental relationship updates
- [ ] Bi-temporal version tracking
- [ ] Async embedding updates
- [ ] Transaction safety
- [ ] Point-in-time queries support

---

## Phase 4: Testing & Validation (Weeks 13-14)

### Feature 4.1: End-to-End Test Suite
**Size**: Medium (3-4 days)
**Dependencies**: All previous features

#### Implementation:
```python
# tests/test_e2e_ingestion.py
class TestEndToEndIngestion:
    """Comprehensive end-to-end testing"""
    
    async def test_full_ingestion_flow(self):
        """Test complete flow from source to query"""
        
        # 1. Setup test environment
        pipeline = await self.create_test_pipeline()
        
        # 2. Add mock connector
        mock_connector = MockConnector(test_config)
        pipeline.add_connector("test_source", mock_connector)
        
        # 3. Run discovery
        schema = await pipeline.discover_schemas()
        assert "test_source" in schema
        
        # 4. Configure mapping
        mapping = await pipeline.auto_map_schema("test_source")
        assert mapping.is_valid()
        
        # 5. Start ingestion
        result = await pipeline.ingest_source("test_source")
        assert result.entities_created > 0
        assert result.relationships_created > 0
        
        # 6. Test webhook update
        webhook_event = {
            "entity_type": "Customer",
            "operation": "update",
            "data": {"id": "c1", "name": "UpdatedCorp"}
        }
        
        await pipeline.process_webhook("test_source", webhook_event)
        
        # 7. Verify data in graph
        query_result = await pipeline.query(
            "What customers do we have?"
        )
        
        assert "UpdatedCorp" in query_result.answer
        
        # 8. Test GraphRAG global query
        global_result = await pipeline.query(
            "What are the main themes in our customer base?"
        )
        
        assert global_result.used_community_summaries == True
    
    async def test_performance_benchmarks(self):
        """Verify performance meets requirements"""
        
        pipeline = await self.create_test_pipeline()
        
        # Generate large dataset
        entities = [
            self.generate_customer(i) for i in range(10000)
        ]
        
        # Measure ingestion time
        start = time.time()
        result = await pipeline.ingest_batch(entities)
        duration = time.time() - start
        
        # Verify throughput
        throughput = len(entities) / duration
        assert throughput > 1000  # >1000 entities/second
        
        # Measure query latency
        latencies = []
        for _ in range(100):
            start = time.time()
            await pipeline.query("Get customer TechCorp")
            latencies.append(time.time() - start)
        
        # Verify p95 latency
        p95_latency = np.percentile(latencies, 95)
        assert p95_latency < 0.2  # <200ms
```

#### Testing:
```python
# Meta-test
def test_test_coverage():
    """Ensure comprehensive test coverage"""
    
    coverage_report = run_coverage_analysis()
    assert coverage_report.total_coverage > 0.85  # >85% coverage
    
    # Check critical paths covered
    critical_modules = [
        "connectors.base_connector",
        "processing.entity_extractor",
        "processing.relationship_builder",
        "ingestion.stream_processor"
    ]
    
    for module in critical_modules:
        assert coverage_report.get_coverage(module) > 0.90
```

#### Acceptance Criteria:
- [ ] Full pipeline flow tested
- [ ] Performance benchmarks verified
- [ ] Error scenarios covered
- [ ] Integration with all components
- [ ] >85% code coverage

---

### Feature 4.2: Monitoring Dashboard
**Size**: Medium (3-4 days)
**Dependencies**: Feature 4.1

#### Implementation:
```python
# src/monitoring/dashboard.py
from prometheus_client import Counter, Histogram, Gauge
import streamlit as st

class IngestionDashboard:
    """Real-time monitoring dashboard"""
    
    def __init__(self):
        # Metrics
        self.entities_processed = Counter(
            'entities_processed_total',
            'Total entities processed',
            ['source', 'entity_type']
        )
        
        self.processing_duration = Histogram(
            'processing_duration_seconds',
            'Processing duration',
            ['operation']
        )
        
        self.queue_size = Gauge(
            'queue_size',
            'Current queue size',
            ['queue_name']
        )
        
        self.error_count = Counter(
            'errors_total',
            'Total errors',
            ['source', 'error_type']
        )
    
    def create_streamlit_dashboard(self):
        """Create Streamlit monitoring dashboard"""
        
        st.title("SpyroSolutions Ingestion Pipeline Monitor")
        
        # Real-time metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Entities/Hour",
                self.get_hourly_rate(),
                delta=self.get_rate_change()
            )
        
        with col2:
            st.metric(
                "Queue Size",
                self.get_current_queue_size(),
                delta=self.get_queue_change()
            )
        
        with col3:
            st.metric(
                "Success Rate",
                f"{self.get_success_rate():.1%}",
                delta=self.get_success_change()
            )
        
        with col4:
            st.metric(
                "Avg Latency",
                f"{self.get_avg_latency():.0f}ms",
                delta=self.get_latency_change()
            )
        
        # Charts
        st.subheader("Ingestion Timeline")
        timeline_chart = self.create_timeline_chart()
        st.plotly_chart(timeline_chart, use_container_width=True)
        
        # Source status
        st.subheader("Source Status")
        source_data = self.get_source_status()
        st.dataframe(source_data, use_container_width=True)
        
        # Error log
        st.subheader("Recent Errors")
        errors = self.get_recent_errors(limit=10)
        for error in errors:
            st.error(f"{error.timestamp}: {error.source} - {error.message}")
```

#### Testing:
```python
# tests/test_monitoring.py
def test_dashboard_metrics():
    dashboard = IngestionDashboard()
    
    # Simulate processing
    with dashboard.processing_duration.time():
        # Process entity
        dashboard.entities_processed.labels(
            source="salesforce",
            entity_type="Customer"
        ).inc()
    
    # Verify metrics
    assert dashboard.get_hourly_rate() > 0
    assert dashboard.get_success_rate() > 0

def test_streamlit_dashboard():
    """Test dashboard renders without errors"""
    dashboard = IngestionDashboard()
    
    # Mock streamlit
    with patch('streamlit.title'):
        with patch('streamlit.metric'):
            dashboard.create_streamlit_dashboard()
```

#### Acceptance Criteria:
- [ ] Real-time metrics display
- [ ] Historical charts
- [ ] Source status tracking
- [ ] Error monitoring
- [ ] Performance indicators
- [ ] Streamlit UI works

---

## Testing Strategy

### Unit Tests
- Each feature has comprehensive unit tests
- Mock external dependencies
- Test edge cases and error conditions
- Target: >90% coverage per feature

### Integration Tests
- Test interaction between components
- Use test containers for Neo4j
- Mock external APIs with WireMock
- Target: All integration points tested

### Performance Tests
- Benchmark each component
- Load testing with realistic data volumes
- Latency measurements
- Target: Meet all performance KPIs

### End-to-End Tests
- Complete pipeline flows
- Real connectors with sandbox accounts
- Query accuracy validation
- Target: All business scenarios covered

## Rollout Plan

1. **Development Environment** (Week 1)
   - Local Neo4j instance
   - Mock connectors
   - Basic monitoring

2. **Staging Environment** (Week 8)
   - Neo4j Aura Dev
   - Sandbox API accounts
   - Full monitoring

3. **Production Pilot** (Week 12)
   - Single data source
   - Limited users
   - Careful monitoring

4. **Full Production** (Week 14)
   - All data sources
   - All users
   - Auto-scaling enabled

## Success Metrics

- Query success rate: >95%
- Ingestion throughput: >10K records/sec
- Query latency: <200ms p95
- System uptime: 99.9%
- Zero data loss
- <5 minute data freshness

This implementation plan provides a clear path from the current 88.33% success rate to a production-ready system with real-time enterprise data ingestion.