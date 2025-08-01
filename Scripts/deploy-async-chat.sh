#!/bin/bash

# Complete deployment script for async chat implementation

set -e  # Exit on error

echo "========================================="
echo "Deploying Async Chat Implementation"
echo "========================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root (sudo)"
    exit 1
fi

PROJECT_DIR="/root/n8n_workflow_runner"
BACKEND_DIR="$PROJECT_DIR/fastapi-react-app/backend"
FRONTEND_DIR="$PROJECT_DIR/fastapi-react-app/frontend"

echo "1. Updating backend..."
cd $BACKEND_DIR

# Run backend migration
if [ -f "migrate_to_websocket.sh" ]; then
    ./migrate_to_websocket.sh
else
    echo "✗ Backend migration script not found"
fi

# Restart backend service
echo "Restarting FastAPI service..."
systemctl restart fastapi
sleep 3
systemctl status fastapi --no-pager | head -10

echo ""
echo "2. Updating frontend..."
cd $FRONTEND_DIR

# Run frontend migration
if [ -f "migrate_to_chat.sh" ]; then
    ./migrate_to_chat.sh
else
    echo "✗ Frontend migration script not found"
fi

# Install dependencies
echo "Installing frontend dependencies..."
npm install

# Build production version
echo "Building production frontend..."
npm run build

# Deploy to web directory
echo "Deploying frontend..."
rm -rf /var/www/fastapi-react-app/*
cp -r build/* /var/www/fastapi-react-app/
chown -R www-data:www-data /var/www/fastapi-react-app

echo ""
echo "3. Updating nginx configuration..."
cd $PROJECT_DIR

# Update nginx for WebSocket support
if [ -f "update-nginx-websocket.sh" ]; then
    ./update-nginx-websocket.sh
else
    echo "✗ Nginx update script not found"
fi

echo ""
echo "4. Checking services..."
./check-services.sh

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
echo ""
echo "Your AI Chat application is ready at:"
echo "http://srv928466.hstgr.cloud:8080"
echo ""
echo "New features deployed:"
echo "✓ WebSocket real-time chat"
echo "✓ AI assistant interface"
echo "✓ Asynchronous workflow processing"
echo "✓ Correlation ID tracking"
echo ""
echo "Next steps:"
echo "1. Import n8n-ai-chat-workflow.json into n8n"
echo "2. Update N8N_WEBHOOK_URL in backend/main.py"
echo "3. Activate the n8n workflow"
echo ""
echo "Monitor logs:"
echo "- FastAPI: journalctl -u fastapi -f"
echo "- Nginx: journalctl -u nginx -f"
echo "========================================="