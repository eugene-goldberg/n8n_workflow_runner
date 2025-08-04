# LangGraph Agentic RAG System

A production-grade agentic RAG (Retrieval-Augmented Generation) system built with LangGraph, featuring a hybrid pgvector + Neo4j architecture for enhanced reasoning and reliability.

## Architecture Overview

This system implements a sophisticated dual-memory architecture:
- **Associative Memory** (pgvector/Neo4j Vector Index): Semantic similarity search
- **Declarative Memory** (Neo4j Knowledge Graph): Explicit relationships and graph traversal

## Key Features

- **Dynamic Retrieval Strategies**: Intelligent routing between vector search, graph queries, and hybrid approaches
- **Automated Knowledge Graph Construction**: Using neo4j-graphrag-python for entity/relation extraction
- **Stateful Agent Control**: LangGraph-based orchestration with persistent memory
- **Self-Correction Loops**: Automatic error recovery and reflection
- **Human-in-the-Loop**: Critical decision points with approval workflows
- **Production Observability**: Full tracing with LangSmith integration

## Project Structure

```
langgraph-agentic-rag/
├── src/
│   ├── agents/          # LangGraph agent implementations
│   ├── ingestion/       # Knowledge graph construction pipeline
│   ├── retrievers/      # Vector, graph, and hybrid retrievers
│   ├── tools/           # Agent tools for search and QA
│   ├── state/           # State management and checkpointers
│   └── evaluation/      # Evaluation framework
├── config/              # Configuration files
├── notebooks/           # Example notebooks
├── tests/               # Test suite
└── scripts/             # Utility scripts
```

## Tech Stack

- **LangGraph**: Agentic orchestration and state management
- **Neo4j**: Graph database for knowledge storage
- **PostgreSQL + pgvector**: Vector similarity search
- **neo4j-graphrag-python**: Automated KG construction
- **LangSmith**: Observability and evaluation

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up databases:
```bash
# PostgreSQL with pgvector
docker run -d --name pgvector \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  ankane/pgvector

# Neo4j
docker run -d --name neo4j \
  -e NEO4J_AUTH=neo4j/password \
  -p 7474:7474 -p 7687:7687 \
  neo4j:latest
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API keys and database connections
```

4. Run the ingestion pipeline:
```bash
python -m src.ingestion.pipeline
```

5. Start the agent:
```bash
python -m src.agents.main
```

## Architecture Details

### 1. Knowledge Backbone

The system uses a hybrid approach combining:
- pgvector for efficient semantic search on unstructured text
- Neo4j for storing structured entities and relationships
- Automated entity extraction via LLM-based pipelines

### 2. Retrieval Strategies

Multiple retriever types are available:
- **VectorRetriever**: Pure semantic search
- **HybridRetriever**: Combined vector + keyword search
- **VectorCypherRetriever**: Graph traversal from vector-found entry points

### 3. Agent Control Flow

LangGraph StateGraph implements:
- Dynamic routing based on query analysis
- Tool selection and execution
- Self-correction on errors
- Human approval for critical actions

### 4. Production Features

- PostgreSQL-based state persistence
- LangSmith tracing for all agent actions
- Evaluation framework with LLM-as-judge
- Active learning from production failures

## Development

See [DEVELOPMENT.md](./docs/DEVELOPMENT.md) for detailed development guidelines.

## License

MIT