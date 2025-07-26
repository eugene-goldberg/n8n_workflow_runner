#!/bin/bash

# Service Check Script

echo "========================================="
echo "Service Status Check"
echo "========================================="

# Check if services are running
echo "1. Checking FastAPI service..."
if systemctl is-active --quiet fastapi; then
    echo "   ✓ FastAPI is running"
    echo "   Recent logs:"
    journalctl -u fastapi -n 5 --no-pager
else
    echo "   ✗ FastAPI is not running"
    echo "   Error logs:"
    journalctl -u fastapi -n 10 --no-pager
fi

echo ""
echo "2. Checking Nginx service..."
if systemctl is-active --quiet nginx; then
    echo "   ✓ Nginx is running"
else
    echo "   ✗ Nginx is not running"
fi

echo ""
echo "3. Checking port 8000 (FastAPI)..."
if netstat -tuln | grep -q ":8000 "; then
    echo "   ✓ Port 8000 is listening"
else
    echo "   ✗ Port 8000 is not listening"
fi

echo ""
echo "4. Testing API endpoint..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/ | grep -q "200"; then
    echo "   ✓ API root endpoint is responding"
else
    echo "   ✗ API is not responding"
fi

echo ""
echo "5. Testing nginx proxy..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/api/ | grep -q "200"; then
    echo "   ✓ Nginx proxy to API is working"
else
    echo "   ✗ Nginx proxy is not working"
fi

echo "========================================="