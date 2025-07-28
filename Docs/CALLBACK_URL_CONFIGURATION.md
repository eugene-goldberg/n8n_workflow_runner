# Callback URL Configuration Guide

## Issue
When n8n tries to connect to `http://srv928466.hstgr.cloud:8080/api/n8n-callback`, it resolves to `127.0.1.1:8080` causing a connection refused error.

## Root Cause
- n8n and FastAPI are running on the same server
- The server's hostname resolves to a local loopback address
- nginx is listening on port 8080, but FastAPI is on port 8000

## Solutions

### Option 1: Use localhost (Recommended)
Since n8n and FastAPI are on the same server, use localhost:
```python
CALLBACK_BASE_URL = "http://localhost:8000"
```

### Option 2: Use nginx proxy
If you want to go through nginx:
```python
CALLBACK_BASE_URL = "http://localhost:8080"
```

### Option 3: Use server's public IP
Replace hostname with actual IP:
```python
CALLBACK_BASE_URL = "http://YOUR_SERVER_IP:8000"
```

### Option 4: Fix server's hosts file
Add to `/etc/hosts` on the server:
```
YOUR_PUBLIC_IP srv928466.hstgr.cloud
```

## Current Configuration
- FastAPI runs on port 8000 internally
- nginx proxies port 8080 to FastAPI port 8000
- n8n should callback to `localhost:8000` for direct access
- Or `localhost:8080` to go through nginx

## Testing
After updating CALLBACK_BASE_URL:
1. Restart FastAPI: `sudo systemctl restart fastapi`
2. Test the callback endpoint: `curl http://localhost:8000/api/n8n-callback`