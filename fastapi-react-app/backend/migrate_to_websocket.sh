#!/bin/bash

echo "Migrating to WebSocket-enabled backend..."

# Backup current main.py
if [ -f "main.py" ]; then
    cp main.py main_backup.py
    echo "✓ Backed up current main.py to main_backup.py"
fi

# Copy new WebSocket version
cp main_with_websocket.py main.py
echo "✓ Updated main.py with WebSocket support"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "Installing new dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "Migration complete! New features added:"
echo "- WebSocket support at /ws/{user_id}"
echo "- n8n callback endpoint at /api/n8n-callback"
echo "- Request tracking with correlation IDs"
echo "- Health check endpoint at /api/health"
echo ""
echo "To start the server, run:"
echo "  python3 main.py"