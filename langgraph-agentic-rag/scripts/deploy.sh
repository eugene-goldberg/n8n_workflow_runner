#!/bin/bash

# Deployment script for LangGraph Agentic RAG
# Usage: ./scripts/deploy.sh

set -e

# Configuration
REMOTE_USER="root"
REMOTE_HOST="154.53.57.127"
REMOTE_PATH="/root/langgraph-agentic-rag"
LOCAL_PATH="/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag"

echo "🚀 Deploying LangGraph Agentic RAG to $REMOTE_HOST..."

# Create remote directory if it doesn't exist
echo "📁 Creating remote directory..."
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH"

# Copy project files
echo "📦 Copying project files..."
scp -r $LOCAL_PATH/app $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
scp -r $LOCAL_PATH/scripts $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
scp $LOCAL_PATH/requirements.txt $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
scp $LOCAL_PATH/README.md $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/
scp $LOCAL_PATH/.env.example $REMOTE_USER@$REMOTE_HOST:$REMOTE_PATH/

# Create tests directory on remote
ssh $REMOTE_USER@$REMOTE_HOST "mkdir -p $REMOTE_PATH/tests"

echo "✅ Deployment complete!"
echo ""
echo "Next steps on remote server:"
echo "1. cd $REMOTE_PATH"
echo "2. python3 -m venv venv"
echo "3. source venv/bin/activate"
echo "4. pip install -r requirements.txt"
echo "5. cp .env.example .env && edit .env with actual credentials"