# SpyroSolutions Scripts Directory

This directory contains all the scripts and configurations used in the SpyroSolutions Agentic RAG implementation.

## Directory Structure

### `/graph_rag_alignment/`
Graph RAG Semantic Model Alignment scripts (Cypher for Neo4j):
- `phase1_entity_model.cypher` - Creates new entity types (Subscription, Project, Team, etc.)
- `phase2_relationships.cypher` - Creates relationships between entities
- `phase3_data_migration.cypher` - Migrates existing data to new model
- `cleanup_phase1.cypher` - Cleanup script to remove entities before re-running
- `fix_graph_structure.cypher` - Original script to fix malformed entities

### `/workflows/`
n8n workflow JSON files:
- `agentic_rag_workflow.json` - Basic Agentic RAG workflow
- `agentic_rag_stream_workflow.json` - Streaming version of the workflow
- `agentic_rag_advanced_workflow.json` - Advanced workflow with UUID validation

### `/demo_app/`
Agentic RAG Demo Application files:
- `agentic_rag_backend.py` - FastAPI backend for demo app
- `AgenticRAGApp.tsx` - React TypeScript frontend component

### `/configs/`
Configuration files:
- `spyro-agentic-rag-nginx.conf` - Main API Nginx configuration
- `agentic-rag-demo-nginx-fixed.conf` - Demo app Nginx configuration
- `spyro-dashboard.json` - Grafana dashboard configuration

## Usage

### Graph RAG Alignment Scripts
Execute in order on the Neo4j server:
```bash
# SSH to server
ssh root@srv928466.hstgr.cloud

# Execute scripts
docker exec -i spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' < /root/SpyroSolutions/graph_rag/scripts/phase1_entity_model.cypher
docker exec -i spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' < /root/SpyroSolutions/graph_rag/scripts/phase2_relationships.cypher
docker exec -i spyro_neo4j cypher-shell -u neo4j -p 'SpyroSolutions2025!' < /root/SpyroSolutions/graph_rag/scripts/phase3_data_migration.cypher
```

### n8n Workflows
Import into n8n via the UI:
1. Access n8n at http://srv928466.hstgr.cloud:5678/
2. Create new workflow
3. Import from JSON file

### Demo App
The demo app is already deployed at http://srv928466.hstgr.cloud:8082/

To run locally:
```bash
# Backend
cd demo_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python agentic_rag_backend.py

# Frontend
# Copy AgenticRAGApp.tsx to your React app's components directory
```

## Server Locations

All scripts are also copied to the server:
- Graph RAG scripts: `/root/SpyroSolutions/graph_rag/scripts/`
- Demo app: `/root/agentic-rag-demo/`
- Nginx configs: `/etc/nginx/sites-available/`