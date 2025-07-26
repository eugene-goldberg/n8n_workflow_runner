# FastAPI + React + n8n Project Summary

## Quick Start Guide

### Access the Application
- **Live URL**: http://srv928466.hstgr.cloud:8080
- **API Docs**: http://srv928466.hstgr.cloud:8080/api/docs

### What Was Built

1. **Full-Stack Todo Application**
   - FastAPI backend with REST API
   - React TypeScript frontend
   - Real-time CRUD operations

2. **n8n Workflow Integration**
   - "Execute Workflow" button
   - Webhook trigger system
   - JSON data exchange

3. **Production Deployment**
   - Ubuntu 24.04 VPS on Hostinger
   - Nginx reverse proxy
   - Systemd service management
   - Automated deployment scripts

## Project Structure
```
n8n_workflow_runner/
├── fastapi-react-app/
│   ├── backend/
│   │   ├── main.py           # FastAPI application
│   │   └── requirements.txt  # Python dependencies
│   └── frontend/
│       ├── src/              # React source code
│       ├── build/            # Production build
│       └── package.json      # Node dependencies
├── setup-hostinger.sh        # Automated setup script
├── check-services.sh         # Service health check
├── rebuild-frontend.sh       # Frontend rebuild script
├── fix-nginx-permissions.sh  # Permission fix script
├── n8n-webhook-workflow.json # n8n workflow template
└── DEPLOYMENT_GUIDE.md       # Detailed documentation
```

## Key Commands

### On Hostinger Server

**Check Status**
```bash
./check-services.sh
```

**Update Application**
```bash
git pull
./rebuild-frontend.sh
systemctl restart fastapi
```

**View Logs**
```bash
journalctl -u fastapi -f    # Backend logs
journalctl -u nginx -f      # Nginx logs
```

**Restart Services**
```bash
systemctl restart fastapi
systemctl restart nginx
```

### Local Development

**Backend**
```bash
cd fastapi-react-app/backend
source venv/bin/activate
python3 main.py
```

**Frontend**
```bash
cd fastapi-react-app/frontend
npm start
```

## Configuration Files

### Backend API Endpoints
- `POST /api/workflow/execute` - Triggers n8n workflow
- `GET/POST/PUT/DELETE /api/items` - Todo CRUD operations

### Environment Variables
- Frontend: `REACT_APP_API_URL` in `.env.production`
- Update webhook URL in `backend/main.py`

### Service Locations
- Nginx config: `/etc/nginx/sites-available/fastapi-react-app`
- Systemd service: `/etc/systemd/system/fastapi.service`
- Frontend files: `/var/www/fastapi-react-app`

## Workflow Integration

1. **Setup n8n Webhook**
   - Import `n8n-webhook-workflow.json` into n8n
   - Get webhook URL from trigger node
   - Update `N8N_WEBHOOK_URL` in backend

2. **Webhook Payload**
```json
{
    "timestamp": "ISO date string",
    "source": "FastAPI Todo App",
    "action": "manual_trigger"
}
```

## Troubleshooting Quick Reference

| Issue | Solution |
|-------|----------|
| CORS errors | Check allowed origins in `main.py` |
| Nginx 500 error | Run `./fix-nginx-permissions.sh` |
| Frontend not updating | Clear cache, run `./rebuild-frontend.sh` |
| Service not running | Check with `systemctl status [service]` |
| Port conflict | Using port 8080 (Docker uses 80) |

## Next Steps

1. **Add Authentication**
   - Implement JWT tokens
   - Secure API endpoints

2. **Enable HTTPS**
   - Install SSL certificate
   - Update nginx config

3. **Add Database**
   - Replace in-memory storage
   - Use PostgreSQL or SQLite

4. **Enhance n8n Integration**
   - Pass todo items to workflow
   - Handle workflow responses
   - Add more trigger options

## Repository
https://github.com/eugene-goldberg/n8n_workflow_runner