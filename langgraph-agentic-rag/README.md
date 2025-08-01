# LangGraph Agentic RAG System

An advanced Retrieval-Augmented Generation system built with LangGraph, implementing explicit state machines, deterministic routing, and self-correction mechanisms for intelligent query handling across vector and graph databases.

## Architecture

This system implements the expert-recommended architectural triad:
- **Neo4j**: For structured relationships and multi-hop queries
- **PostgreSQL with pgvector**: For semantic similarity search
- **LangGraph Agent**: Explicit state machine orchestration with deterministic routing

## Key Features

- **Deterministic Routing**: Rule-based query classification for predictable tool selection
- **Explicit State Machines**: Observable, debuggable workflows using LangGraph
- **Self-Correction Loops**: Grade → Reflect → Rewrite cycles for improved accuracy
- **Advanced Hybrid Patterns**: Sequential and parallel retrieval with fusion/reranking
- **Business Entity Recognition**: Specialized routing for SaaS metrics and entities

## Project Structure

```
langgraph-agentic-rag/
├── app/
│   ├── agent/          # LangGraph workflows and state management
│   ├── tools/          # Tool implementations (vector, graph, hybrid)
│   ├── schemas/        # Pydantic models and data schemas
│   └── monitoring/     # Metrics and performance tracking
├── tests/              # Unit and integration tests
├── scripts/            # Deployment and utility scripts
└── requirements.txt    # Python dependencies
```

## Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your credentials
```

## Configuration

Create a `.env` file with:

```bash
# LLM Configuration
OPENAI_API_KEY=your-key-here
LLM_MODEL=gpt-4o

# Neo4j Configuration
NEO4J_URI=bolt://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password

# PostgreSQL Configuration
POSTGRES_DSN=postgresql://user:password@localhost:5432/dbname

# Redis Configuration (for caching)
REDIS_URL=redis://localhost:6379
```

## Usage

```python
from app.agent import AgenticRAG

# Initialize the agent
agent = AgenticRAG()

# Process a query
result = await agent.query("How much revenue is at risk if Disney churns?")

# The agent will:
# 1. Route to appropriate strategy (graph for business entities)
# 2. Execute retrieval with self-correction if needed
# 3. Rerank and synthesize results
# 4. Generate final answer
```

## Deployment

Deploy to remote server:

```bash
./scripts/deploy.sh user@host:/path/to/deployment
```

## Development Status

- [x] Project structure and dependencies
- [ ] Core state machine implementation
- [ ] Deterministic router
- [ ] Tool implementations
- [ ] Self-correction mechanisms
- [ ] Advanced hybrid patterns
- [ ] Monitoring and analytics