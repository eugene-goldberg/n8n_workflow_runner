# SpyroSolutions Agentic RAG System

A true agentic Retrieval-Augmented Generation (RAG) system for SpyroSolutions that uses LLM-powered agents to autonomously select and execute retrieval strategies.

## Overview

This project implements an intelligent agent that:
- Analyzes user queries to understand intent
- Autonomously selects appropriate retrieval tools (vector search, hybrid search, graph queries)
- Executes multiple tools in parallel when beneficial
- Synthesizes comprehensive answers from multiple sources

## Architecture

The system is built on:
- **neo4j-graphrag-python**: For graph retrieval capabilities
- **LangChain**: For agent orchestration and tool management
- **Neo4j**: As the knowledge graph database
- **OpenAI GPT-4**: For LLM capabilities

## Project Structure

```
spyro-agentic-rag/
├── src/
│   ├── agents/           # Agent implementations
│   ├── retrievers/       # Custom retriever logic
│   ├── api/             # FastAPI endpoints
│   └── utils/           # Utility functions
├── webapp/              # React web application
│   ├── src/            # React components
│   ├── public/         # Static assets
│   └── package.json    # Node dependencies
├── docs/                # Documentation
├── tests/               # Test suites
├── scripts/             # Setup and utility scripts
├── config/              # Configuration files
└── requirements.txt     # Python dependencies
```

## Key Features

1. **Autonomous Tool Selection**: The agent decides which retrieval methods to use based on query analysis
2. **Multi-Tool Execution**: Can use multiple retrieval strategies for comprehensive results
3. **No Manual Toggles**: Removes the need for users to specify retrieval methods
4. **Intelligent Synthesis**: Combines results from multiple sources into coherent answers

## Getting Started

### Backend Setup

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

3. Initialize the Neo4j database:
   ```bash
   python scripts/setup_database.py
   ```

4. Run the API:
   ```bash
   python -m src.api.main
   ```

### Web Application Setup

1. Navigate to the webapp directory:
   ```bash
   cd webapp
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Create environment file:
   ```bash
   cp .env.example .env
   ```

4. Start the web application:
   ```bash
   npm start
   ```

The web app will be available at http://localhost:3000

## Usage

Send queries to the API endpoint:

```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"question": "Which customers have subscriptions worth more than $5M?"},
    headers={"X-API-Key": "your-api-key"}
)

print(response.json())
```

## Implementation Details

See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for detailed architecture and design decisions.