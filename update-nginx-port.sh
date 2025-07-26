#!/bin/bash

# Quick script to update nginx to use port 8080

echo "Updating nginx to use port 8080..."

# Update the nginx configuration
cat > /etc/nginx/sites-available/fastapi-react-app << 'EOF'
server {
    listen 8080;
    server_name srv928466.hstgr.cloud;

    # Serve React frontend
    location / {
        root /root/n8n_workflow_runner/fastapi-react-app/frontend/build;
        try_files $uri /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

# Test nginx configuration
echo "Testing nginx configuration..."
nginx -t

# Restart nginx
echo "Restarting nginx..."
systemctl restart nginx

# Check status
echo "Checking nginx status..."
systemctl status nginx --no-pager | head -10

echo ""
echo "========================================="
echo "Nginx updated to use port 8080"
echo "Your app is now accessible at:"
echo "http://srv928466.hstgr.cloud:8080"
echo "========================================="