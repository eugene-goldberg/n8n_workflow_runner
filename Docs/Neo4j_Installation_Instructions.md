# Neo4j Installation Instructions for n8n

## Step 1: Install Neo4j Community Node

Since your n8n instance doesn't have the Neo4j node installed, here are the installation options:

### Option A: Using n8n UI (Recommended)
1. Open your n8n instance at https://n8n.srv928466.hstgr.cloud
2. Navigate to **Settings** → **Community Nodes**
3. Click **Install a community node**
4. Enter: `n8n-nodes-neo4j`
5. Click **Install**
6. Restart n8n if prompted

### Option B: Manual Installation via Docker
If you need to update your Docker setup, create a custom Dockerfile:

```dockerfile
FROM n8nio/n8n:latest

USER root

# Install Neo4j community node
RUN npm install -g n8n-nodes-neo4j

USER node
```

## Step 2: Set up Neo4j Database

Create a `docker-compose.neo4j.yml` file:

```yaml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
    container_name: spyro_neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/SpyroSolutions2025!
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_memory_pagecache_size=1G
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - ./neo4j_data/data:/data
      - ./neo4j_data/logs:/logs
      - ./neo4j_data/import:/import
      - ./neo4j_data/plugins:/plugins
    networks:
      - n8n-network

networks:
  n8n-network:
    external: true
    name: n8n_default
```

Run Neo4j:
```bash
docker-compose -f docker-compose.neo4j.yml up -d
```

## Step 3: Verify Neo4j Installation

1. Access Neo4j Browser: http://localhost:7474
2. Login with:
   - Username: `neo4j`
   - Password: `SpyroSolutions2025!`

## Step 4: Create Initial Schema

Run these commands in Neo4j Browser:

```cypher
// Create constraints
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT team_id IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;

// Create vector indexes for embeddings
CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
FOR (d:Document) ON d.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}};
```

## Step 5: Configure n8n Credentials

1. In n8n, go to **Credentials** → **Create New**
2. Search for "Basic Auth" (for HTTP requests to Neo4j)
3. Configure:
   - Username: `neo4j`
   - Password: `SpyroSolutions2025!`

## Next Steps

Once Neo4j is running and the community node is installed, we can:
1. Create the entity ingestion workflow
2. Build the query processing workflow
3. Test with sample SpyroSolutions data