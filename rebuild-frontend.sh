#!/bin/bash

echo "Rebuilding frontend with correct API URL..."

cd /root/n8n_workflow_runner/fastapi-react-app/frontend

# Rebuild the frontend
echo "Building production version..."
npm run build

# Copy to web directory
echo "Deploying to web directory..."
rm -rf /var/www/fastapi-react-app/*
cp -r build/* /var/www/fastapi-react-app/

# Set permissions
chown -R www-data:www-data /var/www/fastapi-react-app
chmod -R 755 /var/www/fastapi-react-app

echo "Frontend rebuilt and deployed!"
echo "Clear your browser cache and try again at http://srv928466.hstgr.cloud:8080"