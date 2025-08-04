#!/bin/bash

# Setup script for PostgreSQL and Neo4j databases

echo "🚀 Setting up databases for LangGraph Agentic RAG..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Start PostgreSQL with pgvector
echo "📦 Starting PostgreSQL with pgvector..."
docker run -d \
    --name langgraph-pgvector \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=password \
    -e POSTGRES_DB=agentic_rag \
    -p 5432:5432 \
    ankane/pgvector:latest

# Start Neo4j
echo "📊 Starting Neo4j..."
docker run -d \
    --name langgraph-neo4j \
    -e NEO4J_AUTH=neo4j/password \
    -e NEO4J_PLUGINS='["apoc", "graph-data-science"]' \
    -e NEO4J_dbms_security_procedures_unrestricted=apoc.* \
    -p 7474:7474 \
    -p 7687:7687 \
    neo4j:latest

# Wait for databases to start
echo "⏳ Waiting for databases to start..."
sleep 10

# Create pgvector extension
echo "🔧 Setting up pgvector extension..."
docker exec langgraph-pgvector psql -U postgres -d agentic_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"

echo "✅ Databases setup complete!"
echo ""
echo "PostgreSQL: postgresql://postgres:password@localhost:5432/agentic_rag"
echo "Neo4j Browser: http://localhost:7474 (username: neo4j, password: password)"
echo ""
echo "To stop databases: docker stop langgraph-pgvector langgraph-neo4j"
echo "To remove databases: docker rm langgraph-pgvector langgraph-neo4j"