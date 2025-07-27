#!/bin/bash

echo "Updating nginx configuration for WebSocket support..."

# Backup current nginx config
if [ -f "/etc/nginx/sites-available/fastapi-react-app" ]; then
    cp /etc/nginx/sites-available/fastapi-react-app /etc/nginx/sites-available/fastapi-react-app.backup
    echo "✓ Backed up current nginx configuration"
fi

# Copy new configuration
cp nginx-websocket.conf /etc/nginx/sites-available/fastapi-react-app
echo "✓ Updated nginx configuration with WebSocket support"

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✓ Nginx configuration is valid"
    
    # Reload nginx
    echo "Reloading nginx..."
    systemctl reload nginx
    
    echo ""
    echo "✓ Nginx updated successfully!"
    echo ""
    echo "WebSocket endpoints configured:"
    echo "- /ws/* → WebSocket connections for chat"
    echo "- /api/* → Regular API endpoints"
    echo "- / → React frontend"
else
    echo "✗ Nginx configuration test failed"
    echo "Restoring backup..."
    cp /etc/nginx/sites-available/fastapi-react-app.backup /etc/nginx/sites-available/fastapi-react-app
    exit 1
fi