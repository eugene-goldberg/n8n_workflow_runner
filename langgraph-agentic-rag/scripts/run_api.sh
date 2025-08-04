#!/bin/bash

# Script to run the API server

echo "🚀 Starting LangGraph Agentic RAG API..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "Please edit .env with your API keys and settings."
    exit 1
fi

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Run the API server
python -m uvicorn src.api.server:app --host 0.0.0.0 --port 8000 --reload