# SpyroSolutions Agentic RAG Implementation

## Overview

This document provides a comprehensive technical description of the SpyroSolutions Agentic RAG (Retrieval-Augmented Generation) system, covering both the ingestion pipeline and the autonomous retrieval process. The system is designed to handle enterprise knowledge graphs with dual-schema support (Spyro RAG format and LlamaIndex format).

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Ingestion Pipeline](#ingestion-pipeline)
3. [Agentic Retrieval System](#agentic-retrieval-system)
4. [API Layer](#api-layer)
5. [Web Application](#web-application)
6. [Key Components and Files](#key-components-and-files)

---

## Architecture Overview

The SpyroSolutions Agentic RAG system consists of four main layers:

1. **Data Ingestion Layer**: Processes documents and builds the knowledge graph
2. **Storage Layer**: Neo4j graph database with vector and fulltext indices
3. **Agentic Retrieval Layer**: Autonomous agent with multiple retrieval tools
4. **API/Application Layer**: FastAPI backend and React frontend

### Technology Stack

- **Database**: Neo4j Graph Database
- **Embeddings**: OpenAI Embeddings
- **LLM**: GPT-4 (configurable)
- **Agent Framework**: LangChain with OpenAI Functions
- **Graph RAG**: neo4j-graphrag library
- **API Framework**: FastAPI
- **Frontend**: React with TypeScript

---

## Ingestion Pipeline

### Overview

The ingestion pipeline transforms various document formats into a structured knowledge graph with vector embeddings for semantic search.

### Step-by-Step Ingestion Process

#### 1. Document Loading and Preprocessing

**Files Involved**:
- `ingest_pdf_reports.py`: Main PDF ingestion script
- `ingest_new_reports.py`: Additional report ingestion
- `test_documents/ingest_documents.py`: Test document ingestion

**Process**:
1. Load documents from various sources (primarily PDFs)
2. Extract text content using LlamaIndex document readers
3. Apply chunking strategy (default: 1000 tokens with 200 token overlap)
4. Preserve document metadata (source, page numbers, sections)

#### 2. Entity and Relationship Extraction

**Files Involved**:
- `src/ingestion/entity_extractor.py`: Entity extraction using NER
- `src/ingestion/relationship_extractor.py`: Relationship extraction
- `src/utils/llm_extractor.py`: LLM-based extraction for complex entities

**Process**:
1. **Named Entity Recognition (NER)**:
   - Extract standard entities (Customer, Product, Team, etc.)
   - Use spaCy + custom rules for initial extraction
   - LLM refinement for context-aware extraction

2. **Relationship Extraction**:
   - Pattern-based extraction for standard relationships
   - LLM-based extraction for complex relationships
   - Relationship types: SUBSCRIBES_TO, HAS_RISK, SUPPORTS, etc.

3. **Property Extraction**:
   - Extract numerical properties (revenue, costs, scores)
   - Parse monetary values (e.g., "$8M" → 8000000)
   - Extract dates and time-based properties

#### 3. Knowledge Graph Construction

**Files Involved**:
- `src/ingestion/graph_builder.py`: Graph construction logic
- `src/utils/schema_compatibility.py`: Dual-schema support
- `src/utils/neo4j_connector.py`: Neo4j connection management

**Process**:
1. **Node Creation**:
   ```cypher
   MERGE (c:Customer {name: $name})
   SET c.subscription_value = $value,
       c.success_score = $score,
       c.created_at = datetime()
   ```

2. **Relationship Creation**:
   ```cypher
   MATCH (c:Customer {name: $customer})
   MATCH (p:Product {name: $product})
   MERGE (c)-[r:SUBSCRIBES_TO]->(p)
   SET r.subscription_value = $value
   ```

3. **Dual-Schema Support**:
   - Spyro RAG format: Direct labels (`:Customer`, `:Product`)
   - LlamaIndex format: Entity nodes with type labels (`:__Entity__:CUSTOMER`)
   - Compatibility layer ensures both formats are queryable

#### 4. Vector Embedding Generation

**Files Involved**:
- `src/ingestion/embedding_generator.py`: Embedding generation
- `src/utils/openai_embeddings.py`: OpenAI embedding wrapper

**Process**:
1. Generate embeddings for each text chunk using OpenAI Ada-002
2. Create vector index in Neo4j:
   ```cypher
   CREATE VECTOR INDEX spyro_vector_index IF NOT EXISTS
   FOR (n:Chunk) ON n.embedding
   OPTIONS {indexConfig: {
     `vector.dimensions`: 1536,
     `vector.similarity_function`: 'cosine'
   }}
   ```

3. Store embeddings with chunks for semantic search

#### 5. Fulltext Index Creation

**Files Involved**:
- `src/ingestion/index_builder.py`: Index creation utilities

**Process**:
1. Create fulltext indices for keyword search:
   ```cypher
   CREATE FULLTEXT INDEX spyro_fulltext_index IF NOT EXISTS
   FOR (n:Customer|Product|Team|Risk|Chunk)
   ON EACH [n.name, n.description, n.content]
   ```

### Ingestion Tools and Utilities

1. **PDF Ingestion** (`ingest_pdf_reports.py`):
   - PDF document parsing and text extraction
   - LlamaIndex document processing
   - Automatic chunking and embedding generation

2. **Property Graph Pipeline** (`property_graph_pipeline/`):
   - Direct property graph construction
   - Batch processing for large datasets
   - Incremental updates support

3. **Data Quality Tools**:
   - `src/ingestion/validation.py`: Entity and relationship validation
   - `src/ingestion/deduplication.py`: Duplicate detection and merging
   - `src/ingestion/enrichment.py`: Data enrichment using external sources

---

## Agentic Retrieval System

### Overview

The agentic retrieval system uses an autonomous agent that can select and combine multiple retrieval strategies to answer complex queries.

### Core Components

#### 1. SpyroAgentEnhanced

**File**: `src/agents/spyro_agent_enhanced_fixed.py`

**Key Features**:
- Autonomous tool selection using LangChain with OpenAI Functions
- Schema-aware query generation
- Multi-tool execution for complex queries
- Conversation memory for context retention

**Architecture**:
```python
class SpyroAgentEnhanced:
    def __init__(self, config: Config):
        # Initialize Neo4j driver
        # Setup embeddings and LLM
        # Create retrieval tools
        # Initialize LangChain agent
```

#### 2. Retrieval Tools

The agent has access to four specialized tools:

**a) GraphQuery Tool**
- **Purpose**: Execute Cypher queries for structured data retrieval
- **Implementation**: Uses Text2CypherRetriever from neo4j-graphrag
- **Best for**: Aggregations, specific entity queries, relationship traversal

**b) VectorSearch Tool**
- **Purpose**: Semantic similarity search using embeddings
- **Implementation**: VectorRetriever with OpenAI embeddings
- **Best for**: Conceptual queries, finding similar content

**c) HybridSearch Tool**
- **Purpose**: Combines vector and keyword search
- **Implementation**: HybridRetriever (vector + fulltext)
- **Best for**: General information queries, document search

**d) UnifiedSearch Tool**
- **Purpose**: Intelligent routing between search strategies
- **Implementation**: Custom logic to select appropriate retriever
- **Best for**: Primary entry point for most queries

### Step-by-Step Retrieval Process

#### 1. Query Reception
```python
def query(self, user_query: str) -> Dict[str, Any]:
    # Reset schema tracker
    # Initialize token tracking
    # Execute agent with query
```

#### 2. Agent Decision Making

The agent analyzes the query and decides which tool(s) to use:

```python
# Agent's internal reasoning (via system message):
"TOOL SELECTION STRATEGY:
1. For questions about specific metrics, percentages → Use GraphQuery
2. For exploring relationships and patterns → Use UnifiedSearch  
3. For finding documents or general information → Use HybridSearch
4. For conceptual or philosophical questions → Use VectorSearch"
```

#### 3. Tool Execution

**Example: GraphQuery Execution**
```python
def graph_query(query: str) -> str:
    # Use Text2Cypher to generate Cypher query
    # Execute query against Neo4j
    # Format and return results
```

The Text2Cypher process:
1. Analyze user query
2. Reference enhanced Cypher examples
3. Generate appropriate Cypher query
4. Handle dual-schema compatibility

#### 4. Result Processing

- Serialize Neo4j values (DateTime objects, etc.)
- Track schema sources (Spyro RAG vs LlamaIndex)
- Format results for user consumption

#### 5. Response Generation

The agent synthesizes results from multiple tools if needed:
```python
# Example multi-tool execution:
1. GraphQuery for specific customer data
2. VectorSearch for related insights
3. Combine results into coherent answer
```

### Enhanced Cypher Examples

**File**: `src/utils/cypher_examples_enhanced.py`

Provides real-world query patterns for common business questions:

```python
{
    "question": "What percentage of our ARR is dependent on customers with success scores below 70?",
    "cypher": """
    MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
    OPTIONAL MATCH (c)-[:HAS_SUCCESS_SCORE]->(s)
    WITH c, coalesce(s.score, s.value, 100) as score,
    CASE 
        WHEN sub.value CONTAINS '$' THEN toFloat(replace(replace(sub.value, '$', ''), 'M', '')) * 1000000
        ELSE coalesce(toFloat(sub.value), 0)
    END as revenue
    ...
    """
}
```

---

## API Layer

### FastAPI Backend

**File**: `src/api/main.py`

**Endpoints**:

1. **POST /query**
   - Accepts natural language questions
   - Returns structured response with answer and metadata
   - Requires API key authentication

2. **GET /health**
   - System health check
   - Returns agent capabilities and status

3. **POST /feedback**
   - Collect user feedback on responses
   - Used for continuous improvement

**Request/Response Format**:
```json
// Request
{
    "question": "What percentage of our ARR is dependent on customers with success scores below 70?"
}

// Response
{
    "query": "...",
    "answer": "20.61% of our ARR ($14.8M out of $71.8M) is dependent on customers with success scores below 70.",
    "metadata": {
        "agent_type": "LangChain with OpenAI Functions (Enhanced)",
        "execution_time_seconds": 12.5,
        "tokens_used": 2784,
        "tools_used": ["GraphQuery"],
        "timestamp": "2025-08-02T15:30:00Z"
    },
    "schema_sources": {
        "schemas_accessed": ["Spyro RAG"],
        "entity_count_by_schema": {"Spyro RAG": 15}
    }
}
```

### API Configuration

**File**: `.env`
```bash
# API Configuration
SPYRO_API_KEY=spyro-secret-key-123
API_HOST=0.0.0.0
API_PORT=8000

# Agent Configuration
AGENT_MODEL=gpt-4o
AGENT_TEMPERATURE=0
AGENT_MAX_ITERATIONS=10
```

### Security Features

1. **API Key Authentication**: Required header `x-api-key`
2. **Rate Limiting**: Configurable per API key
3. **CORS Configuration**: Restricted to allowed origins
4. **Request Validation**: Pydantic models for type safety

---

## Web Application

### Frontend Architecture

**Technology**: React with TypeScript

**Key Components**:

1. **Query Interface**:
   - Natural language input box
   - Query history sidebar
   - Real-time response streaming

2. **Results Display**:
   - Formatted answer with syntax highlighting
   - Metadata display (execution time, tokens used)
   - Schema source visualization

3. **Feedback System**:
   - Thumbs up/down for answer quality
   - Detailed feedback form
   - Issue reporting

### Backend Integration

**Communication Flow**:
1. User enters query in React app
2. Frontend sends POST request to `/query` endpoint
3. FastAPI validates request and invokes agent
4. Agent processes query autonomously
5. Response returned and displayed in UI

---

## Key Components and Files

### Core Agent Files

1. **`src/agents/spyro_agent_enhanced_fixed.py`**
   - Main agent implementation
   - Tool orchestration
   - Response generation

2. **`src/agents/schema_tracker.py`**
   - Tracks which schemas were accessed
   - Provides transparency on data sources

### Utility Files

1. **`src/utils/config.py`**
   - Configuration management
   - Environment variable loading

2. **`src/utils/schema_compatibility.py`**
   - Dual-schema support functions
   - Query translation utilities

3. **`src/utils/cypher_examples_enhanced.py`**
   - Enhanced Cypher query examples
   - Pattern matching templates

### Retriever Integration

1. **`src/retrievers/vector_retriever.py`**
   - Vector similarity search implementation

2. **`src/retrievers/hybrid_retriever.py`**
   - Combined vector and keyword search

3. **`src/retrievers/text2cypher_retriever.py`**
   - Natural language to Cypher conversion

### Testing Infrastructure

1. **`test_critical_queries.py`**
   - Tests core business queries
   - Validates data-grounded responses

2. **`scripts/test_all_business_questions.sh`**
   - Comprehensive test suite
   - 60 real-world business queries

3. **`test_actual_success_rate.py`**
   - Measures success rate
   - Identifies improvement areas

---

## Performance Metrics

### Current Capabilities

- **Query Success Rate**: 78% (verified on test suite)
- **Average Response Time**: 5-15 seconds
- **Token Usage**: 1,500-4,000 tokens per query
- **Concurrent Users**: Supports multiple simultaneous queries

### Optimization Strategies

1. **Query Caching**: Redis-based caching for frequent queries
2. **Embedding Cache**: Pre-computed embeddings for common terms
3. **Connection Pooling**: Neo4j connection pool for performance
4. **Async Processing**: Non-blocking I/O for API endpoints

---

## Future Enhancements

1. **Improved Success Rate**:
   - Enhanced entity extraction
   - Better relationship inference
   - Richer Cypher examples

2. **Multi-Modal Support**:
   - Image analysis for diagrams
   - Table extraction from PDFs
   - Chart interpretation

3. **Advanced Analytics**:
   - Predictive queries
   - Trend analysis
   - Anomaly detection

4. **Enterprise Features**:
   - Multi-tenancy support
   - Audit logging
   - Advanced access controls