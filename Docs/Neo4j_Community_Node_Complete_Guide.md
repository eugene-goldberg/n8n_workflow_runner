# Neo4j Community Node for n8n: Complete Implementation Guide

## Overview

The Neo4j community node provides full graph database integration for n8n workflows, including vector search capabilities and LangChain support. This guide covers everything needed to implement Graph RAG using Neo4j with n8n.

## Available Neo4j Nodes

### 1. n8n-nodes-neo4j (by Kurea)
- **npm Package**: `n8n-nodes-neo4j`
- **Version**: 0.2.2
- **Features**: 
  - LangChain integration
  - Vector store support
  - Graph operations
  - Cypher query execution

### 2. @rxap/n8n-nodes-neo4j
- **npm Package**: `@rxap/n8n-nodes-neo4j`
- **Features**: 
  - Basic authentication
  - Cypher query execution
  - Connection management

### 3. n8n_neo4j (by ruapho)
- **GitHub**: https://github.com/ruapho/n8n_neo4j
- **Features**: 
  - Node and Trigger support
  - Custom Cypher queries
  - Data retrieval

## Installation Methods

### Method 1: GUI Installation (Recommended for Cloud)
1. Navigate to Settings > Community Nodes in n8n
2. Click "Install a community node"
3. Enter: `n8n-nodes-neo4j`
4. Click Install

### Method 2: Docker Installation (Self-Hosted)

Create a custom Dockerfile:

```dockerfile
FROM n8nio/n8n:latest

USER root

# Install Neo4j community node
RUN npm install -g n8n-nodes-neo4j

# Optional: Install additional nodes
# RUN npm install -g @rxap/n8n-nodes-neo4j

USER node
```

Update docker-compose.yml:

```yaml
version: '3.8'

services:
  n8n:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: n8n
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=password
      - NODE_FUNCTION_ALLOW_EXTERNAL=*
      - N8N_ENCRYPTION_KEY=${N8N_ENCRYPTION_KEY}
    volumes:
      - ./n8n_data:/home/node/.n8n
      - ./local-files:/files
    depends_on:
      - neo4j
    networks:
      - graph-network

  neo4j:
    image: neo4j:5-enterprise
    container_name: neo4j
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    environment:
      - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
      - NEO4J_ACCEPT_LICENSE_AGREEMENT=yes
      - NEO4J_PLUGINS=["apoc", "graph-data-science"]
      - NEO4J_dbms_memory_pagecache_size=1G
      - NEO4J_dbms_memory_heap_max__size=2G
    volumes:
      - ./neo4j_data/data:/data
      - ./neo4j_data/logs:/logs
      - ./neo4j_data/import:/import
      - ./neo4j_data/plugins:/plugins
    networks:
      - graph-network

networks:
  graph-network:
    driver: bridge
```

### Method 3: Manual NPM Installation

For existing n8n installations:

```bash
# Navigate to n8n custom folder
cd ~/.n8n/custom

# Install the node
npm install n8n-nodes-neo4j

# Restart n8n
```

## Neo4j Configuration

### 1. Create Vector Indexes

```cypher
// Create vector index for documents
CREATE VECTOR INDEX document_embeddings IF NOT EXISTS
FOR (d:Document) ON d.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}};

// Create vector index for entities
CREATE VECTOR INDEX entity_embeddings IF NOT EXISTS
FOR (e:Entity) ON e.embedding
OPTIONS {indexConfig: {
    `vector.dimensions`: 1536,
    `vector.similarity_function`: 'cosine'
}};
```

### 2. Graph Schema for SpyroSolutions

```cypher
// Create constraints
CREATE CONSTRAINT product_id IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE;
CREATE CONSTRAINT customer_id IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT team_id IF NOT EXISTS FOR (t:Team) REQUIRE t.id IS UNIQUE;
CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE;

// Example data structure
CREATE (p:Product {id: 'prod_001', name: 'SpyroSuite', description: 'Main SaaS product'})
CREATE (c:Customer {id: 'cust_001', name: 'EA', tier: 'Enterprise', success_score: 85})
CREATE (t:Team {id: 'team_001', name: 'Development Team', department: 'Engineering'})
CREATE (proj:Project {id: 'proj_001', name: 'Feature X', status: 'In Progress', deadline: date('2024-03-01')})

// Create relationships
CREATE (c)-[:HAS_SUBSCRIPTION {mrr: 50000, start_date: date('2023-01-15')}]->(p)
CREATE (t)-[:WORKS_ON]->(proj)
CREATE (proj)-[:DELIVERS_FEATURE {committed_date: date('2024-02-15')}]->(c)
```

## n8n Workflow Implementation

### Workflow 1: Entity Ingestion

```json
{
  "nodes": [
    {
      "name": "Read CSV Data",
      "type": "n8n-nodes-base.readBinaryFiles",
      "position": [250, 300]
    },
    {
      "name": "Parse CSV",
      "type": "n8n-nodes-base.csv",
      "position": [450, 300]
    },
    {
      "name": "Create Neo4j Nodes",
      "type": "n8n-nodes-neo4j",
      "parameters": {
        "operation": "execute",
        "query": "UNWIND $items AS item CREATE (c:Customer {id: item.id, name: item.name, tier: item.tier})",
        "parameters": "={{ {items: $json} }}"
      },
      "position": [650, 300]
    }
  ]
}
```

### Workflow 2: Vector Embedding Creation

```javascript
// Function node to prepare embeddings
const items = $input.all();
const processedItems = [];

for (const item of items) {
  const text = `${item.json.name} ${item.json.description} ${item.json.tier}`;
  processedItems.push({
    ...item.json,
    text_for_embedding: text
  });
}

return processedItems;
```

### Workflow 3: Graph RAG Query

```json
{
  "nodes": [
    {
      "name": "Chat Trigger",
      "type": "@n8n/n8n-nodes-langchain.chatTrigger"
    },
    {
      "name": "Extract Entities",
      "type": "@n8n/n8n-nodes-langchain.agent",
      "parameters": {
        "promptType": "define",
        "text": "Extract customer names, products, and metrics from: {{ $json.chatInput }}"
      }
    },
    {
      "name": "Neo4j Graph Query",
      "type": "n8n-nodes-neo4j",
      "parameters": {
        "operation": "execute",
        "query": `
          MATCH (c:Customer {name: $customerName})-[:HAS_SUBSCRIPTION]->(p:Product)
          MATCH (c)-[:HAS_RISK]->(r:Risk)
          RETURN c.name, p.name, r.impact, r.severity
        `
      }
    }
  ]
}
```

## Advanced Neo4j Cypher Queries for SpyroSolutions

### 1. Revenue at Risk Query
```cypher
MATCH (c:Customer {name: $customerName})-[sub:HAS_SUBSCRIPTION]->(p:Product)
MATCH (c)-[:HAS_SLA]->(sla:SLA)
MATCH (c)-[:HAS_RISK]->(r:Risk)
WHERE sla.current_value < sla.target
RETURN c.name AS customer,
       sub.mrr AS monthly_revenue,
       r.impact_factor AS risk_factor,
       sub.mrr * r.impact_factor AS revenue_at_risk
```

### 2. Customer Commitments Query
```cypher
MATCH (c:Customer)-[sub:HAS_SUBSCRIPTION]->(p:Product)
WITH c, sub.mrr as revenue
ORDER BY revenue DESC
LIMIT 5
MATCH (c)-[:COMMITTED_FEATURE]->(f:Feature)
OPTIONAL MATCH (f)-[:HAS_RISK]->(r:Risk)
RETURN c.name AS customer,
       revenue,
       collect(DISTINCT f.name) AS commitments,
       collect(DISTINCT r.description) AS risks
```

### 3. Multi-hop Traversal for Impact Analysis
```cypher
MATCH path = (c:Customer)-[:HAS_SUBSCRIPTION|HAS_SLA|COMMITTED_FEATURE*1..3]-(affected)
WHERE c.name = $customerName
WITH c, affected, length(path) as distance
RETURN c.name AS source,
       labels(affected)[0] AS affected_type,
       affected.name AS affected_entity,
       distance
ORDER BY distance
```

## Vector Search Integration

### 1. Hybrid Search (Vector + Graph)
```cypher
// First, find similar documents using vector search
CALL db.index.vector.queryNodes('document_embeddings', 10, $queryEmbedding)
YIELD node AS doc, score

// Then, traverse the graph from these documents
MATCH (doc)-[:MENTIONS]->(e:Entity)
MATCH (e)-[:RELATED_TO*1..2]-(related)
RETURN doc.content, e.name, collect(DISTINCT related.name) AS related_entities, score
ORDER BY score DESC
```

### 2. Context-Aware RAG Query
```cypher
// Find relevant context using vector similarity
CALL db.index.vector.queryNodes('entity_embeddings', 5, $embedding)
YIELD node AS entity, score
WHERE score > 0.7

// Expand to get full context
MATCH (entity)-[r:RELATED_TO|IMPACTS|DEPENDS_ON*1..2]-(context)
RETURN entity, 
       type(r) AS relationship,
       context,
       score
```

## Environment Variables

### Required Variables
```bash
# n8n Configuration
N8N_ENCRYPTION_KEY=your-32-character-encryption-key
NODE_FUNCTION_ALLOW_EXTERNAL=*

# Neo4j Configuration
NEO4J_AUTH=neo4j/your-password
NEO4J_PASSWORD=your-password

# Optional: LangChain Integration
OPENAI_API_KEY=your-openai-key
```

### Production Configuration
```bash
# Security
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password

# Performance
NEO4J_dbms_memory_pagecache_size=2G
NEO4J_dbms_memory_heap_max__size=4G

# Networking
N8N_PROTOCOL=https
N8N_HOST=your-domain.com
WEBHOOK_URL=https://your-domain.com/
```

## Troubleshooting

### Common Issues

1. **Node Not Found**
   - Ensure `NODE_FUNCTION_ALLOW_EXTERNAL=*` is set
   - Rebuild Docker image after adding to Dockerfile
   - Check n8n logs for installation errors

2. **Neo4j Connection Failed**
   - Verify Neo4j is running: `docker ps`
   - Check network connectivity: `docker network ls`
   - Ensure services are on same network

3. **Cypher Query Errors**
   - Use Neo4j Browser to test queries first
   - Check parameter binding syntax
   - Verify indexes are created

### Performance Optimization

1. **Create Indexes**
```cypher
CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name);
CREATE INDEX customer_tier IF NOT EXISTS FOR (c:Customer) ON (c.tier);
```

2. **Query Optimization**
- Use parameters instead of string concatenation
- Limit result sets with `LIMIT`
- Profile queries with `PROFILE`

## Benefits of Neo4j for Graph RAG

1. **Native Graph Storage**: Optimized for relationship traversal
2. **Cypher Query Language**: Expressive pattern matching
3. **Vector Search**: Built-in similarity search
4. **ACID Compliance**: Transaction support
5. **Scalability**: Handles billions of nodes and relationships
6. **Active Community**: Extensive documentation and support

## Conclusion

The Neo4j community node provides a robust solution for implementing Graph RAG in n8n. With proper setup and configuration, it offers superior graph traversal capabilities compared to relational databases, making it ideal for complex relationship queries required by SpyroSolutions.