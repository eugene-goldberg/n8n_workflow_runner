# SpyroSolutions Agentic RAG Knowledge Graph Implementation Plan

## Executive Summary

This document outlines a comprehensive plan to deploy and integrate the Agentic RAG Knowledge Graph system for SpyroSolutions on the Hostinger server. The system will enhance the existing Neo4j Graph RAG implementation with intelligent agent capabilities, temporal tracking, and advanced search features.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Prerequisites & Current State](#prerequisites--current-state)
3. [Phase 1: Environment Preparation](#phase-1-environment-preparation)
4. [Phase 2: Database Setup](#phase-2-database-setup)
5. [Phase 3: Application Deployment](#phase-3-application-deployment)
6. [Phase 4: Data Migration & Ingestion](#phase-4-data-migration--ingestion)
7. [Phase 5: n8n Integration](#phase-5-n8n-integration)
8. [Phase 6: Testing & Validation](#phase-6-testing--validation)
9. [Phase 7: Production Configuration](#phase-7-production-configuration)
10. [Maintenance & Monitoring](#maintenance--monitoring)

---

## Architecture Overview

### Target Architecture
```
Hostinger Server (148.230.84.166)
├── Docker Containers
│   ├── n8n (existing)
│   ├── Neo4j (existing)
│   ├── PostgreSQL (existing)
│   └── Agentic RAG API (new)
├── Services
│   ├── FastAPI on port 8058
│   ├── Neo4j on ports 7474/7687
│   └── PostgreSQL on port 5432
└── Integration Points
    ├── n8n HTTP Request nodes → RAG API
    ├── RAG API → Neo4j (Graphiti)
    └── RAG API → PostgreSQL (pgvector)
```

### Key Benefits for SpyroSolutions
- **Intelligent Query Routing**: AI agent decides optimal search strategy
- **Temporal Analysis**: Track how customer relationships evolve
- **Tool Transparency**: Understand reasoning behind each response
- **Unified Interface**: Single API for all RAG operations

---

## Prerequisites & Current State

### Current Infrastructure
- **Server**: Hostinger VPS at 148.230.84.166
- **Neo4j**: Running in Docker (spyro_neo4j)
- **PostgreSQL**: Running in Docker (n8n_postgres_memory)
- **n8n**: Running with workflows configured
- **Docker Network**: root_default

### Required Resources
- Python 3.11+ runtime
- 4GB+ RAM for the service
- 10GB storage for embeddings
- API keys for LLM providers

---

## Phase 1: Environment Preparation

### Step 1.1: Create Project Directory Structure
```bash
ssh root@148.230.84.166 "mkdir -p /root/spyro-agentic-rag/{app,data,logs,config}"
```

### Step 1.2: Install Python 3.11
```bash
ssh root@148.230.84.166 "apt update && apt install -y python3.11 python3.11-venv python3.11-dev"
```

### Step 1.3: Clone and Transfer Project
```bash
# On local machine
cd /Users/eugene/dev/apps/n8n_workflow_runner
tar -czf agentic-rag.tar.gz agentic-rag-knowledge-graph/

# Transfer to server
scp agentic-rag.tar.gz root@148.230.84.166:/root/spyro-agentic-rag/

# Extract on server
ssh root@148.230.84.166 "cd /root/spyro-agentic-rag && tar -xzf agentic-rag.tar.gz && mv agentic-rag-knowledge-graph app/"
```

### Step 1.4: Create Python Virtual Environment
```bash
ssh root@148.230.84.166 "cd /root/spyro-agentic-rag/app && python3.11 -m venv venv"
```

### Step 1.5: Install Dependencies
```bash
ssh root@148.230.84.166 "cd /root/spyro-agentic-rag/app && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
```

---

## Phase 2: Database Setup

### Step 2.1: Configure PostgreSQL with pgvector
```bash
# Check if pgvector is installed
ssh root@148.230.84.166 "docker exec n8n_postgres_memory psql -U postgres -d postgres -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

### Step 2.2: Create RAG Database
```bash
# Create dedicated database
ssh root@148.230.84.166 "docker exec n8n_postgres_memory psql -U postgres -c 'CREATE DATABASE spyro_rag_db;'"

# Create pgvector extension in new database
ssh root@148.230.84.166 "docker exec n8n_postgres_memory psql -U postgres -d spyro_rag_db -c 'CREATE EXTENSION IF NOT EXISTS vector;'"
```

### Step 2.3: Apply Database Schema
```bash
# Copy schema file to server
scp /Users/eugene/dev/apps/n8n_workflow_runner/agentic-rag-knowledge-graph/sql/schema.sql root@148.230.84.166:/root/spyro-agentic-rag/

# Apply schema
ssh root@148.230.84.166 "docker exec -i n8n_postgres_memory psql -U postgres -d spyro_rag_db < /root/spyro-agentic-rag/schema.sql"
```

### Step 2.4: Verify Neo4j Connection
```bash
# Test Neo4j connectivity
ssh root@148.230.84.166 "docker exec spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' 'RETURN 1'"
```

---

## Phase 3: Application Deployment

### Step 3.1: Create Environment Configuration
```bash
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/app/.env << 'EOF'
# Database Configuration
DATABASE_URL=postgresql://postgres:postgres@n8n_postgres_memory:5432/spyro_rag_db

# Neo4j Configuration  
NEO4J_URI=bolt://spyro_neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=SpyroSolutions2025!

# LLM Provider Configuration
LLM_PROVIDER=openai
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-api-key-here
LLM_CHOICE=gpt-4o-mini

# Embedding Configuration
EMBEDDING_PROVIDER=openai
EMBEDDING_BASE_URL=https://api.openai.com/v1
EMBEDDING_API_KEY=sk-your-api-key-here
EMBEDDING_MODEL=text-embedding-3-small

# Ingestion Configuration
INGESTION_LLM_CHOICE=gpt-3.5-turbo

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
APP_PORT=8058
EOF"
```

### Step 3.2: Create Dockerfile for Service
```bash
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ .

# Create necessary directories
RUN mkdir -p /app/logs /app/documents

# Expose port
EXPOSE 8058

# Run the application
CMD [\"python\", \"-m\", \"agent.api\"]
EOF"
```

### Step 3.3: Create Docker Compose Configuration
```bash
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/docker-compose.yml << 'EOF'
version: '3.8'

services:
  spyro-rag-api:
    build: .
    container_name: spyro_rag_api
    ports:
      - \"8058:8058\"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@n8n_postgres_memory:5432/spyro_rag_db
      - NEO4J_URI=bolt://spyro_neo4j:7687
    env_file:
      - ./app/.env
    volumes:
      - ./data:/app/documents
      - ./logs:/app/logs
    networks:
      - root_default
    depends_on:
      - n8n_postgres_memory
      - spyro_neo4j
    restart: unless-stopped

networks:
  root_default:
    external: true
EOF"
```

### Step 3.4: Build and Launch Service
```bash
# Build Docker image
ssh root@148.230.84.166 "cd /root/spyro-agentic-rag && docker-compose build"

# Start the service
ssh root@148.230.84.166 "cd /root/spyro-agentic-rag && docker-compose up -d"

# Check logs
ssh root@148.230.84.166 "docker logs spyro_rag_api"
```

---

## Phase 4: Data Migration & Ingestion

### Step 4.1: Prepare SpyroSolutions Documents
```bash
# Create documents directory
ssh root@148.230.84.166 "mkdir -p /root/spyro-agentic-rag/data/documents"

# Create sample documents with SpyroSolutions data
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/data/documents/spyro_customers.md << 'EOF'
# SpyroSolutions Customer Portfolio

## Enterprise Customers

### EA (Electronic Arts)
- **Tier**: Enterprise
- **MRR**: $50,000
- **Products**: SpyroSuite
- **Success Score**: 85
- **Current Risks**: Feature delay - Q1 deliverables (Impact: 20%)
- **Projects**: API v2 Migration (In Progress)

### Nintendo
- **Tier**: Enterprise
- **MRR**: $75,000
- **Products**: SpyroSuite
- **Success Score**: 92
- **Current Risks**: None
- **Notable**: Long-term stable customer since 2023

### Disney
- **Tier**: Enterprise
- **MRR**: $100,000
- **Products**: SpyroAnalytics
- **Success Score**: 78
- **Current Risks**: 
  - SLA breach - uptime below 99.5% (Impact: 30%)
  - Performance degradation during peak hours (Impact: 25%)
- **Projects**: SSO Integration (In Progress)

## Professional Customers

### Netflix
- **Tier**: Professional
- **MRR**: $35,000
- **Products**: SpyroAnalytics
- **Success Score**: 88
- **Current Risks**: None
- **Projects**: SSO Integration (In Progress)

### Spotify
- **Tier**: Professional
- **MRR**: $25,000
- **Products**: SpyroSuite
- **Success Score**: 71
- **Current Risks**: Integration issues with legacy systems (Impact: 15%)
EOF"
```

### Step 4.2: Create Risk Analysis Document
```bash
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/data/documents/spyro_risk_analysis.md << 'EOF'
# SpyroSolutions Risk Analysis Q1 2025

## High-Risk Accounts

### Disney - Critical Revenue Risk
- **Total Revenue at Risk**: $55,000/month
- **Primary Issues**:
  - SLA violations on uptime guarantees
  - Performance issues affecting user experience
- **Mitigation Strategy**: 
  - Dedicated engineering resources allocated
  - Infrastructure scaling in progress
  - Weekly executive reviews

### EA - Feature Delivery Risk
- **Revenue at Risk**: $10,000/month
- **Issue**: Q1 feature commitments behind schedule
- **Impact**: Customer considering alternatives
- **Action Plan**: Sprint replanning with Platform Team

## Risk Trends
- 40% of Enterprise customers have active risks
- Average risk impact: 22% of MRR
- Primary risk categories: Performance (40%), Features (35%), Integration (25%)
EOF"
```

### Step 4.3: Run Ingestion Pipeline
```bash
# Execute ingestion within container
ssh root@148.230.84.166 "docker exec spyro_rag_api python -m ingestion.ingest --clean"

# Monitor ingestion progress
ssh root@148.230.84.166 "docker logs -f spyro_rag_api"
```

---

## Phase 5: n8n Integration

### Step 5.1: Create n8n Workflow for Agentic RAG
```json
{
  "name": "SpyroSolutions_Agentic_RAG",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "spyro-agentic-rag",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "webhook",
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "typeVersion": 1,
      "position": [250, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "http://spyro_rag_api:8058/chat",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Content-Type",
              "value": "application/json"
            }
          ]
        },
        "sendBody": true,
        "specifyBody": "json",
        "jsonBody": "={{ { \"message\": $json.body.query, \"session_id\": $json.body.session_id || \"default\" } }}",
        "options": {}
      },
      "id": "call_rag_api",
      "name": "Call Agentic RAG",
      "type": "n8n-nodes-base.httpRequest",
      "typeVersion": 4.1,
      "position": [450, 300]
    },
    {
      "parameters": {
        "jsCode": "// Extract and format the response\nconst ragResponse = $json;\n\n// Build enhanced response with tool usage\nconst response = {\n  answer: ragResponse.response,\n  tools_used: ragResponse.tools_used || [],\n  session_id: ragResponse.session_id,\n  timestamp: new Date().toISOString(),\n  metadata: {\n    model_used: ragResponse.model,\n    search_strategy: ragResponse.tools_used.map(t => t.tool).join(', ')\n  }\n};\n\n// Add tool details for transparency\nif (ragResponse.tools_used.length > 0) {\n  response.tool_details = ragResponse.tools_used.map(tool => ({\n    tool: tool.tool,\n    query: tool.input.query || tool.input.entity || 'N/A',\n    result_count: tool.output?.length || 0\n  }));\n}\n\nreturn [{ json: response }];"
      },
      "id": "format_response",
      "name": "Format Response",
      "type": "n8n-nodes-base.code",
      "typeVersion": 2,
      "position": [650, 300]
    },
    {
      "parameters": {
        "respondWith": "json",
        "responseBody": "={{ $json }}",
        "options": {}
      },
      "id": "respond",
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "typeVersion": 1,
      "position": [850, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{
        "node": "Call Agentic RAG",
        "type": "main",
        "index": 0
      }]]
    },
    "Call Agentic RAG": {
      "main": [[{
        "node": "Format Response",
        "type": "main",
        "index": 0
      }]]
    },
    "Format Response": {
      "main": [[{
        "node": "Respond",
        "type": "main",
        "index": 0
      }]]
    }
  },
  "settings": {
    "executionOrder": "v1"
  }
}
```

### Step 5.2: Deploy Workflow via n8n API
```bash
# Save workflow to file
cat > /tmp/agentic_rag_workflow.json << 'EOF'
[workflow JSON from above]
EOF

# Create workflow via API
curl -X POST \
  'https://n8n.srv928466.hstgr.cloud/api/v1/workflows' \
  -H 'X-N8N-API-KEY: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI4Mzk4ZmRjMS01ZWJjLTQ5NDAtYTA1My0wMGE3OTVmNjcxZGMiLCJpc3MiOiJuOG4iLCJhdWQiOiJwdWJsaWMtYXBpIiwiaWF0IjoxNzUzOTc5MTYxLCJleHAiOjE3NTY1MDQ4MDB9.n-6DdprWCI6BgthLJ76wAUMeq5BCmEEUClNp99Apb2k' \
  -H 'Content-Type: application/json' \
  -d @/tmp/agentic_rag_workflow.json
```

### Step 5.3: Create Streaming Workflow
```bash
# Create a separate workflow for streaming responses
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/streaming_workflow.json << 'EOF'
{
  \"name\": \"SpyroSolutions_Agentic_RAG_Stream\",
  \"nodes\": [
    {
      \"parameters\": {
        \"httpMethod\": \"POST\",
        \"path\": \"spyro-agentic-rag-stream\",
        \"options\": {}
      },
      \"id\": \"webhook\",
      \"name\": \"Webhook\",
      \"type\": \"n8n-nodes-base.webhook\",
      \"typeVersion\": 1,
      \"position\": [250, 300]
    },
    {
      \"parameters\": {
        \"jsCode\": \"// Forward to streaming endpoint\\nconst streamUrl = 'http://spyro_rag_api:8058/chat/stream';\\nconst payload = {\\n  message: $json.body.query,\\n  session_id: $json.body.session_id || 'default'\\n};\\n\\n// Return streaming URL for client\\nreturn [{\\n  json: {\\n    stream_url: streamUrl,\\n    payload: payload,\\n    instructions: 'Use EventSource or similar to consume SSE stream'\\n  }\\n}];\"
      },
      \"id\": \"prepare_stream\",
      \"name\": \"Prepare Stream\",
      \"type\": \"n8n-nodes-base.code\",
      \"typeVersion\": 2,
      \"position\": [450, 300]
    }
  ]
}
EOF"
```

---

## Phase 6: Testing & Validation

### Step 6.1: API Health Check
```bash
# Check if API is running
ssh root@148.230.84.166 "curl http://localhost:8058/health"

# Expected response: {"status":"healthy","neo4j":"connected","postgres":"connected"}
```

### Step 6.2: Test Basic Query
```bash
# Test revenue at risk query
ssh root@148.230.84.166 "curl -X POST http://localhost:8058/chat \
  -H 'Content-Type: application/json' \
  -d '{\"message\": \"What is the total revenue at risk for SpyroSolutions?\"}'"
```

### Step 6.3: Test Tool Usage Visibility
```bash
# Query that should use multiple tools
ssh root@148.230.84.166 "curl -X POST http://localhost:8058/chat \
  -H 'Content-Type: application/json' \
  -d '{\"message\": \"Show me Disney customer details and their risk analysis\"}'"
```

### Step 6.4: Test n8n Integration
```bash
# Call the n8n webhook
curl -X POST https://n8n.srv928466.hstgr.cloud/webhook/spyro-agentic-rag \
  -H 'Content-Type: application/json' \
  -d '{"query": "Which customers have the highest risk scores?"}'
```

### Step 6.5: CLI Testing
```bash
# Connect to the API using CLI
ssh root@148.230.84.166 "cd /root/spyro-agentic-rag/app && source venv/bin/activate && python cli.py --url http://localhost:8058"
```

---

## Phase 7: Production Configuration

### Step 7.1: Configure Nginx Reverse Proxy
```bash
ssh root@148.230.84.166 "cat > /etc/nginx/sites-available/spyro-rag << 'EOF'
server {
    listen 80;
    server_name rag.srv928466.hstgr.cloud;

    location / {
        proxy_pass http://localhost:8058;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        
        # SSE specific settings
        proxy_set_header Cache-Control no-cache;
        proxy_set_header X-Accel-Buffering no;
        proxy_read_timeout 86400;
    }
}
EOF"

# Enable site
ssh root@148.230.84.166 "ln -s /etc/nginx/sites-available/spyro-rag /etc/nginx/sites-enabled/"
ssh root@148.230.84.166 "nginx -t && systemctl reload nginx"
```

### Step 7.2: Set Up SSL with Certbot
```bash
ssh root@148.230.84.166 "certbot --nginx -d rag.srv928466.hstgr.cloud --non-interactive --agree-tos --email eugene.goldberg117@gmail.com"
```

### Step 7.3: Configure Monitoring
```bash
# Create health check script
ssh root@148.230.84.166 "cat > /root/spyro-agentic-rag/health_check.sh << 'EOF'
#!/bin/bash
HEALTH_URL=\"http://localhost:8058/health\"
RESPONSE=\$(curl -s -o /dev/null -w \"%{http_code}\" \$HEALTH_URL)

if [ \$RESPONSE -ne 200 ]; then
    echo \"Health check failed with status \$RESPONSE\"
    docker restart spyro_rag_api
fi
EOF"

# Make executable and add to cron
ssh root@148.230.84.166 "chmod +x /root/spyro-agentic-rag/health_check.sh"
ssh root@148.230.84.166 "echo '*/5 * * * * /root/spyro-agentic-rag/health_check.sh' | crontab -"
```

### Step 7.4: Configure Log Rotation
```bash
ssh root@148.230.84.166 "cat > /etc/logrotate.d/spyro-rag << 'EOF'
/root/spyro-agentic-rag/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        docker restart spyro_rag_api > /dev/null
    endscript
}
EOF"
```

---

## Maintenance & Monitoring

### Daily Tasks
1. **Check API Health**: `curl https://rag.srv928466.hstgr.cloud/health`
2. **Monitor Logs**: `docker logs --tail 100 spyro_rag_api`
3. **Check Resource Usage**: `docker stats spyro_rag_api`

### Weekly Tasks
1. **Update Knowledge Base**: Run ingestion for new documents
2. **Review Tool Usage**: Analyze which tools are most used
3. **Performance Metrics**: Check response times and error rates

### Monthly Tasks
1. **Update Dependencies**: Check for security updates
2. **Backup Databases**: Export PostgreSQL and Neo4j data
3. **Review Costs**: Monitor API usage and costs

### Backup Commands
```bash
# Backup PostgreSQL
ssh root@148.230.84.166 "docker exec n8n_postgres_memory pg_dump -U postgres spyro_rag_db > /root/backups/spyro_rag_$(date +%Y%m%d).sql"

# Backup Neo4j
ssh root@148.230.84.166 "docker exec spyro_neo4j neo4j-admin database dump neo4j --to-path=/backups/"
```

---

## Troubleshooting Guide

### Common Issues

1. **API Not Responding**
   ```bash
   # Check container status
   docker ps -a | grep spyro_rag_api
   # Restart container
   docker restart spyro_rag_api
   ```

2. **Database Connection Errors**
   ```bash
   # Test PostgreSQL connection
   docker exec n8n_postgres_memory psql -U postgres -d spyro_rag_db -c "SELECT 1"
   # Test Neo4j connection
   docker exec spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' "RETURN 1"
   ```

3. **Ingestion Failures**
   ```bash
   # Check logs for errors
   docker logs spyro_rag_api | grep ERROR
   # Re-run with verbose logging
   docker exec spyro_rag_api python -m ingestion.ingest --verbose
   ```

---

## Success Metrics

### Technical Metrics
- API response time < 2 seconds for queries
- 99.9% uptime for the service
- Tool selection accuracy > 90%

### Business Metrics
- Improved risk detection accuracy
- Faster customer insight retrieval
- Enhanced decision-making with temporal analysis

### Integration Success
- Seamless n8n workflow integration
- Tool transparency in all responses
- Consistent performance under load

---

## Conclusion

This implementation plan provides SpyroSolutions with a state-of-the-art Agentic RAG system that enhances the existing Neo4j Graph RAG with intelligent agent capabilities. The system will provide better insights, more accurate responses, and complete transparency in its reasoning process.

The deployment on Hostinger leverages the existing infrastructure while adding powerful new capabilities that will help SpyroSolutions better understand and serve their customers.