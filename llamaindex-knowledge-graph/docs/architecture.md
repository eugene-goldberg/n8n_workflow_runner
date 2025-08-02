# LlamaIndex Knowledge Graph Architecture

## Overview

This document describes the architecture of the LlamaIndex Knowledge Graph pipeline, which transforms unstructured documents into queryable knowledge graphs.

## System Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌────────────────────┐
│   PDF/Documents │────▶│   LlamaParse     │────▶│  Markdown Content  │
└─────────────────┘     └──────────────────┘     └────────────────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │MarkdownElement    │
                                                  │   NodeParser       │
                                                  └────────────────────┘
                                                            │
                                                  ┌─────────┴──────────┐
                                                  ▼                    ▼
                                          ┌──────────────┐    ┌──────────────┐
                                          │  Text Nodes  │    │ Table Nodes  │
                                          └──────────────┘    └──────────────┘
                                                  │                    │
                                                  └─────────┬──────────┘
                                                            ▼
                                                  ┌────────────────────┐
                                                  │ SchemaLLMPath      │
                                                  │   Extractor        │
                                                  └────────────────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │ PropertyGraphIndex │
                                                  └────────────────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │   Neo4j Graph DB   │
                                                  └────────────────────┘
                                                            │
                                                            ▼
                                                  ┌────────────────────┐
                                                  │   Query Engine     │
                                                  └────────────────────┘
```

## Components

### 1. Document Parser (LlamaParse)
- **Purpose**: Convert PDF and other documents into structured markdown
- **Key Features**:
  - Preserves document structure (headers, tables, lists)
  - Handles complex layouts and formatting
  - Outputs clean markdown for downstream processing

### 2. Node Parser (MarkdownElementNodeParser)
- **Purpose**: Segment markdown into semantic nodes
- **Key Features**:
  - Identifies different content types (text vs tables)
  - Creates appropriate node types for each content type
  - Preserves relationships between content sections

### 3. Knowledge Extractor (SchemaLLMPathExtractor)
- **Purpose**: Extract entities and relationships using LLM
- **Key Features**:
  - Schema-driven extraction for consistency
  - Validates relationships against predefined rules
  - Supports custom entity and relationship types

### 4. Graph Store (Neo4jPropertyGraphStore)
- **Purpose**: Persist knowledge graph in Neo4j
- **Key Features**:
  - Direct integration with Neo4j database
  - Supports property graphs with rich metadata
  - Enables complex graph queries

### 5. Query Engine
- **Purpose**: Enable natural language querying of the graph
- **Key Features**:
  - Translates natural language to graph queries
  - Supports multi-hop reasoning
  - Returns contextualized answers

## Data Flow

1. **Document Input**: PDF or other documents are provided to the pipeline
2. **Parsing**: LlamaParse converts documents to structured markdown
3. **Node Creation**: MarkdownElementNodeParser creates typed nodes
4. **Entity Extraction**: SchemaLLMPathExtractor identifies entities and relationships
5. **Graph Construction**: PropertyGraphIndex builds the knowledge graph
6. **Storage**: Graph is persisted in Neo4j
7. **Querying**: Natural language queries are processed against the graph

## Schema Design

### Entity Types
Entities represent the "nodes" in the knowledge graph:
- **PERSON**: Individuals mentioned in documents
- **COMPANY**: Organizations and businesses
- **PRODUCT**: Products and services
- **FINANCIAL_METRIC**: Revenue, costs, profits, etc.
- **LOCATION**: Geographic entities
- **DATE/TIME**: Temporal entities
- **EVENT**: Acquisitions, launches, milestones

### Relationship Types
Relationships represent the "edges" connecting entities:
- **WORKS_FOR**: Person → Company
- **PRODUCES**: Company → Product
- **LOCATED_IN**: Entity → Location
- **OCCURRED_ON**: Event → Date
- **IMPACTS**: Event → Entity

### Validation Rules
The schema enforces consistency through validation:
- Each entity type has allowed relationship types
- Relationships must connect appropriate entity types
- Cardinality constraints can be applied

## Configuration

The pipeline is highly configurable through environment variables and schema definitions:

### API Configuration
- `LLAMA_CLOUD_API_KEY`: For document parsing
- `OPENAI_API_KEY`: For LLM operations

### Neo4j Configuration
- `NEO4J_URI`: Database connection string
- `NEO4J_USERNAME`: Authentication username
- `NEO4J_PASSWORD`: Authentication password

### Processing Configuration
- `LLM_MODEL`: Which OpenAI model to use
- `LLM_TEMPERATURE`: Control extraction creativity
- Parser settings for performance tuning

## Performance Considerations

### Scalability
- Document parsing can be parallelized
- Node extraction uses configurable worker pools
- Neo4j handles large graphs efficiently

### Optimization
- Create indexes on frequently queried properties
- Use batch operations for bulk ingestion
- Cache parsed documents when reprocessing

### Resource Usage
- LLM API calls are the primary cost driver
- Memory usage scales with document size
- Neo4j requires adequate disk space for graphs

## Error Handling

The pipeline implements robust error handling:
- Failed document parsing is logged and skipped
- Extraction errors don't halt the entire process
- Database connection failures trigger retries
- All errors are logged with context

## Extensibility

The architecture supports several extension points:

### Custom Schemas
Create domain-specific schemas by extending `GraphSchema`

### Custom Extractors
Implement specialized extraction logic for specific document types

### Additional Parsers
Add support for new document formats beyond PDF

### Query Enhancements
Extend the query engine with custom query patterns

## Security Considerations

- API keys should be stored securely (environment variables)
- Neo4j should use authentication in production
- Consider data privacy when processing sensitive documents
- Implement access controls for multi-user scenarios