#!/bin/bash

# FastAPI + React App Setup Script for Hostinger
# Run as root on Ubuntu 24.04

set -e  # Exit on error

echo "========================================="
echo "FastAPI + React App Setup Script"
echo "========================================="

# Variables
PROJECT_DIR="/root/n8n_workflow_runner"
BACKEND_DIR="$PROJECT_DIR/fastapi-react-app/backend"
FRONTEND_DIR="$PROJECT_DIR/fastapi-react-app/frontend"
SERVER_NAME="srv928466.hstgr.cloud"

# Navigate to project directory
cd $PROJECT_DIR

echo "1. Pulling latest code from git..."
git pull

echo "2. Setting up FastAPI backend..."
cd $BACKEND_DIR

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "   Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv and install dependencies
echo "   Installing Python dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "3. Creating systemd service for FastAPI..."
cat > /etc/systemd/system/fastapi.service << EOF
[Unit]
Description=FastAPI app
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$BACKEND_DIR
Environment="PATH=$BACKEND_DIR/venv/bin"
ExecStart=$BACKEND_DIR/venv/bin/python main.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF

echo "4. Building React frontend..."
cd $FRONTEND_DIR

# Install npm dependencies
echo "   Installing npm dependencies..."
npm install

# Build the production version
echo "   Building production build..."
npm run build

echo "5. Configuring nginx..."
# Remove default nginx site if it exists
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi

# Create nginx configuration
cat > /etc/nginx/sites-available/fastapi-react-app << EOF
server {
    listen 8080;
    server_name $SERVER_NAME;

    # Serve React frontend
    location / {
        root $FRONTEND_DIR/build;
        try_files \$uri /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/fastapi-react-app /etc/nginx/sites-enabled/

# Test nginx configuration
echo "   Testing nginx configuration..."
nginx -t

echo "6. Starting services..."
# Reload systemd
systemctl daemon-reload

# Enable and start FastAPI service
systemctl enable fastapi
systemctl stop fastapi 2>/dev/null || true
systemctl start fastapi

# Restart nginx
systemctl restart nginx

echo "7. Checking service status..."
echo "   FastAPI status:"
systemctl status fastapi --no-pager | head -10

echo "   Nginx status:"
systemctl status nginx --no-pager | head -10

echo "========================================="
echo "Setup complete!"
echo "========================================="
echo "Your app should now be accessible at:"
echo "http://$SERVER_NAME"
echo ""
echo "API documentation available at:"
echo "http://$SERVER_NAME/api/docs"
echo ""
echo "To check logs:"
echo "  FastAPI: journalctl -u fastapi -f"
echo "  Nginx: journalctl -u nginx -f"
echo "========================================="