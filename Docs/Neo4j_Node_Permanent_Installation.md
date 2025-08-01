# Neo4j Community Node - Permanent Installation Guide

## Current Status
The Neo4j community node has been temporarily installed in your n8n container. However, this installation will be lost when the container is recreated.

## Permanent Installation Method

To make the Neo4j node installation persistent, you need to modify your docker-compose.yml to use a custom Dockerfile:

1. **Create a Dockerfile** (already created at `/root/Dockerfile.n8n`):
```dockerfile
FROM docker.n8n.io/n8nio/n8n:latest

USER root

# Install Neo4j community node
RUN cd /usr/local/lib/node_modules/n8n && npm install n8n-nodes-neo4j

USER node
```

2. **Update your docker-compose.yml**:
Replace:
```yaml
n8n:
  image: docker.n8n.io/n8nio/n8n
```

With:
```yaml
n8n:
  build:
    context: .
    dockerfile: Dockerfile.n8n
```

3. **Rebuild the container**:
```bash
docker-compose down
docker-compose build
docker-compose up -d
```

## Alternative: Keep Current Setup

Since the Neo4j node is already installed and working, you can continue using it until the next container recreation. The node will be available in n8n's node panel.

## Verifying Installation

1. Access n8n at https://n8n.srv928466.hstgr.cloud
2. In the workflow editor, click the "+" button to add a node
3. Search for "Neo4j" - you should see the Neo4j node available

## Neo4j Connection Details

- **Host**: spyro_neo4j (within Docker network)
- **Port**: 7687 (Bolt protocol)
- **Username**: neo4j
- **Password**: SpyroSolutions2025!

## Test Query

Once you've added the Neo4j node to a workflow, you can test with this Cypher query:
```cypher
MATCH (c:Customer)-[:HAS_SUBSCRIPTION]->(p:Product)
RETURN c.name, p.name, c.tier
LIMIT 5
```