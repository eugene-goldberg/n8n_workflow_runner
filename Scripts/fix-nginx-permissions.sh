#!/bin/bash

echo "Fixing nginx permissions issue..."

# Option 1: Move the frontend build to a standard web directory
echo "Creating web directory..."
mkdir -p /var/www/fastapi-react-app

# Copy the build files
echo "Copying frontend build files..."
cp -r /root/n8n_workflow_runner/fastapi-react-app/frontend/build/* /var/www/fastapi-react-app/

# Set proper permissions
echo "Setting permissions..."
chown -R www-data:www-data /var/www/fastapi-react-app
chmod -R 755 /var/www/fastapi-react-app

# Update nginx configuration to use the new path
echo "Updating nginx configuration..."
cat > /etc/nginx/sites-available/fastapi-react-app << 'EOF'
server {
    listen 8080;
    server_name srv928466.hstgr.cloud;

    # Serve React frontend from standard web directory
    location / {
        root /var/www/fastapi-react-app;
        try_files $uri /index.html;
    }

    # Proxy API requests to FastAPI backend
    location /api {
        proxy_pass http://127.0.0.1:8000;
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

# Test and reload nginx
echo "Testing nginx configuration..."
nginx -t

echo "Reloading nginx..."
systemctl reload nginx

echo "Done! Your app should now be accessible at http://srv928466.hstgr.cloud:8080"