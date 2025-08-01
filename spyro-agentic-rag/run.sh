#!/bin/bash

# SpyroSolutions Agentic RAG Runner Script

echo "SpyroSolutions Agentic RAG System"
echo "================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import neo4j_graphrag" 2>/dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env with your credentials before running!"
    exit 1
fi

# Check if Neo4j is accessible
echo "Checking Neo4j connection..."
python -c "
from src.utils.config import Config
import neo4j
try:
    config = Config.from_env()
    driver = neo4j.GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password))
    driver.verify_connectivity()
    driver.close()
    print('✓ Neo4j connection successful')
except Exception as e:
    print(f'✗ Neo4j connection failed: {e}')
    exit(1)
"

# Run the API
echo ""
echo "Starting API server..."
echo "API will be available at http://localhost:8000"
echo "Documentation at http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""

python -m src.api.main