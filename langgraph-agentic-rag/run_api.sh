#!/bin/bash

# Activate virtual environment and run the API
cd /Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag

# Install FastAPI if not already installed
./venv/bin/pip install fastapi uvicorn

# Set environment variables
export OPENAI_MODEL=gpt-3.5-turbo
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USERNAME=neo4j
export NEO4J_PASSWORD=password123
export LANGGRAPH_API_PORT=8000

# Run the API
./venv/bin/python3 src/api/langgraph_api.py