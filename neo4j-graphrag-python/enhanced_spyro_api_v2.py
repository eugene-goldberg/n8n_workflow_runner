#!/usr/bin/env python3
"""
Enhanced SpyroSolutions RAG API with proper Text2Cypher support
"""

from fastapi import FastAPI, HTTPException, Depends, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import HybridRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
import os
from dotenv import load_dotenv
import logging
import time
from collections import defaultdict

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# OpenAI configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

# SpyroSolutions schema for Text2Cypher - Updated to match semantic model
SPYRO_SCHEMA = """
Node properties:
Customer {name: STRING, industry: STRING}
Product {name: STRING, description: STRING}
Project {name: STRING, status: STRING}
Team {name: STRING, size: INTEGER}
SaaSSubscription {plan: STRING, period: STRING}
AnnualRecurringRevenue {amount: STRING, year: INTEGER}
CustomerSuccessScore {score: FLOAT, health_status: STRING}
Risk {level: STRING, type: STRING, description: STRING}
Event {type: STRING, date: STRING, impact: STRING}
SLA {metric: STRING, guarantee: STRING}
OperationalStatistics {metric: STRING, value: STRING}
OperationalCost {cost: STRING, category: STRING}
Profitability {impact: STRING, margin: STRING}
CompanyObjective {name: STRING, target: STRING}
Feature {name: STRING, priority: STRING}
Roadmap {name: STRING, quarter: STRING}

The relationships:
(:Product)-[:ASSIGNED_TO_TEAM]->(:Team)
(:Product)-[:HAS_SLA]->(:SLA)
(:Product)-[:HAS_OPERATIONAL_STATS]->(:OperationalStatistics)
(:Product)-[:HAS_ROADMAP]->(:Roadmap)
(:Product)-[:USED_BY]->(:Customer)
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:Customer)-[:HAS_RISK]->(:Risk)
(:Customer)-[:AFFECTED_BY_EVENT]->(:Event)
(:CustomerSuccessScore)-[:INFLUENCED_BY]->(:Event)
(:SaaSSubscription)-[:GENERATES]->(:AnnualRecurringRevenue)
(:Project)-[:DELIVERS_FEATURE]->(:Feature)
(:Project)-[:HAS_OPERATIONAL_COST]->(:OperationalCost)
(:Project)-[:CONTRIBUTES_TO_PROFITABILITY]->(:Profitability)
(:Feature)-[:PART_OF]->(:Project)
(:Feature)-[:COMMITTED_TO]->(:Customer)
(:Roadmap)-[:HAS_FEATURE]->(:Feature)
(:OperationalCost)-[:AFFECTS]->(:Profitability)
(:Profitability)-[:SUPPORTS]->(:CompanyObjective)
(:Risk)-[:IMPACTS]->(:CompanyObjective)
"""

# Examples for Text2Cypher - Updated with new relationships
EXAMPLES = [
    "USER INPUT: 'Show customer subscriptions and revenue' QUERY: MATCH (c:Customer)-[:SUBSCRIBES_TO]->(s:SaaSSubscription)-[:GENERATES]->(arr:AnnualRecurringRevenue) RETURN c.name as customer, s.plan as plan, arr.amount as revenue",
    "USER INPUT: 'Which features are committed to customers?' QUERY: MATCH (f:Feature)-[:COMMITTED_TO]->(c:Customer) RETURN f.name as feature, c.name as customer, f.priority as priority",
    "USER INPUT: 'Show project costs and profitability' QUERY: MATCH (p:Project)-[:HAS_OPERATIONAL_COST]->(oc:OperationalCost), (p)-[:CONTRIBUTES_TO_PROFITABILITY]->(prof:Profitability) RETURN p.name as project, oc.cost as cost, prof.impact as profit_impact",
    "USER INPUT: 'What events affected customer success scores?' QUERY: MATCH (css:CustomerSuccessScore)-[:INFLUENCED_BY]->(e:Event)<-[:AFFECTED_BY_EVENT]-(c:Customer) RETURN c.name as customer, css.score as score, e.type as event_type, e.impact as impact",
    "USER INPUT: 'Show risks impacting company objectives' QUERY: MATCH (r:Risk)-[:IMPACTS]->(co:CompanyObjective) RETURN r.type as risk_type, r.level as risk_level, co.name as objective, co.target as target",
    "USER INPUT: 'How does profitability support objectives?' QUERY: MATCH (p:Profitability)-[:SUPPORTS]->(co:CompanyObjective) RETURN p.impact as profit_impact, co.name as objective, co.target as target",
    "USER INPUT: 'Show cost impact on profitability' QUERY: MATCH (oc:OperationalCost)-[:AFFECTS]->(p:Profitability) RETURN oc.cost as cost, oc.category as category, p.impact as profit_impact, p.margin as margin"
]

# Global RAG system instance
class SpyroRAGSystem:
    def __init__(self):
        self.driver = None
        self.llm = None
        self.embedder = None
        self.hybrid_retriever = None
        self.text2cypher_retriever = None
        self.graph_rag = None
    
    def initialize(self):
        """Initialize all components"""
        logger.info("Initializing SpyroRAG System...")
        
        # Neo4j driver
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # LLM and embedder
        self.llm = OpenAILLM(
            model_name="gpt-4o",
            model_params={"temperature": 0}
        )
        self.embedder = OpenAIEmbeddings()
        
        # Hybrid Retriever
        self.hybrid_retriever = HybridRetriever(
            driver=self.driver,
            vector_index_name="spyro_vector_index",
            fulltext_index_name="spyro_fulltext_index",
            embedder=self.embedder
        )
        
        # Text2Cypher Retriever
        self.text2cypher_retriever = Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=SPYRO_SCHEMA,
            examples=EXAMPLES
        )
        
        # GraphRAG for hybrid search
        self.graph_rag = GraphRAG(
            retriever=self.hybrid_retriever,
            llm=self.llm
        )
        
        logger.info("SpyroRAG System initialized successfully")
    
    def close(self):
        """Close connections"""
        if self.driver:
            self.driver.close()

rag_system = None

# Query metrics
query_metrics = {
    "total_queries": 0,
    "total_response_time": 0,
    "queries_by_retriever": defaultdict(int),
    "recent_queries": []
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global rag_system
    rag_system = SpyroRAGSystem()
    rag_system.initialize()
    yield
    # Shutdown
    if rag_system:
        rag_system.close()

# Create FastAPI app
app = FastAPI(
    title="SpyroSolutions RAG API v2",
    description="Enhanced API with proper Text2Cypher support",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class QueryRequest(BaseModel):
    question: str
    use_cypher: bool = False
    top_k: int = 5

class QueryResponse(BaseModel):
    question: str
    answer: str
    context_items: int
    retriever_type: str
    processing_time_ms: float
    timestamp: datetime
    graph_results: Optional[List[Dict[str, Any]]] = None

# API key authentication
API_KEY = os.getenv("SPYRO_API_KEY", "spyro-secret-key-123")

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return x_api_key

# Endpoints
@app.get("/health")
async def health_check():
    """Check API and Neo4j health"""
    try:
        with rag_system.driver.session() as session:
            result = session.run("RETURN 1 as healthy")
            neo4j_healthy = result.single()["healthy"] == 1
            
            # Get node count
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()["count"]
            
            # Get available indexes
            result = session.run("SHOW INDEXES")
            indexes = []
            for record in result:
                if record["state"] == "ONLINE":
                    indexes.append(f"{record['name']} ({record['type']})")
    except:
        neo4j_healthy = False
        node_count = 0
        indexes = []
    
    return {
        "status": "healthy",
        "neo4j_connected": neo4j_healthy,
        "node_count": node_count,
        "indexes_available": indexes,
        "timestamp": datetime.now()
    }

@app.post("/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest, api_key: str = Depends(verify_api_key)):
    """Execute a query against the knowledge graph"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    start_time = time.time()
    
    try:
        if request.use_cypher:
            # Use Text2CypherRetriever for direct graph queries
            logger.info(f"Executing Text2Cypher query: {request.question}")
            
            # Get Cypher results
            cypher_results = rag_system.text2cypher_retriever.search(
                query_text=request.question
            )
            
            # Format results for response
            graph_results = []
            answer_parts = []
            
            if cypher_results.items:
                for item in cypher_results.items[:request.top_k]:
                    # Parse the string representation of the record
                    content_str = str(item.content)
                    
                    # Extract key-value pairs from the record string
                    # Format: <Record key1='value1' key2='value2'>
                    if content_str.startswith("<Record ") and content_str.endswith(">"):
                        record_str = content_str[8:-1]  # Remove "<Record " and ">"
                        record_dict = {}
                        
                        # Simple parser for the record format
                        import re
                        pairs = re.findall(r"(\w+)='([^']*)'", record_str)
                        for key, value in pairs:
                            record_dict[key] = value
                        
                        graph_results.append(record_dict)
                        
                        # Build natural language answer
                        parts = []
                        for key, value in record_dict.items():
                            if value:
                                parts.append(f"{key}: {value}")
                        if parts:
                            answer_parts.append(" - " + ", ".join(parts))
                
                if answer_parts:
                    answer = "Based on the graph data:\n" + "\n".join(answer_parts)
                else:
                    answer = "The query returned results but no displayable data was found."
            else:
                answer = "No results found for your query."
            
            context_items = len(cypher_results.items)
            retriever_type = "text2cypher"
            
        else:
            # Use GraphRAG with hybrid retriever
            logger.info(f"Executing hybrid search query: {request.question}")
            
            result = rag_system.graph_rag.search(
                query_text=request.question,
                return_context=True,
                retriever_config={"top_k": request.top_k}
            )
            
            answer = result.answer
            context_items = len(result.retriever_result.items) if hasattr(result, 'retriever_result') else 0
            retriever_type = "hybrid"
            graph_results = None
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # ms
        
        # Update metrics
        query_metrics["total_queries"] += 1
        query_metrics["total_response_time"] += processing_time
        query_metrics["queries_by_retriever"][retriever_type] += 1
        query_metrics["recent_queries"].append(request.question)
        if len(query_metrics["recent_queries"]) > 10:
            query_metrics["recent_queries"].pop(0)
        
        return QueryResponse(
            question=request.question,
            answer=answer,
            context_items=context_items,
            retriever_type=retriever_type,
            processing_time_ms=processing_time,
            timestamp=datetime.now(),
            graph_results=graph_results
        )
        
    except Exception as e:
        logger.error(f"Query error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats")
async def get_statistics(api_key: str = Depends(verify_api_key)):
    """Get system usage statistics"""
    avg_response_time = 0
    if query_metrics["total_queries"] > 0:
        avg_response_time = query_metrics["total_response_time"] / query_metrics["total_queries"]
    
    return {
        "total_queries": query_metrics["total_queries"],
        "average_response_time_ms": avg_response_time,
        "queries_by_retriever": dict(query_metrics["queries_by_retriever"]),
        "most_recent_queries": query_metrics["recent_queries"]
    }

@app.get("/graph/stats")
async def graph_statistics(api_key: str = Depends(verify_api_key)):
    """Get statistics about the knowledge graph"""
    if not rag_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    with rag_system.driver.session() as session:
        # Get entity counts
        entity_counts = {}
        result = session.run("""
            MATCH (n)
            WHERE n:Product OR n:Customer OR n:Project OR n:Team 
               OR n:Risk OR n:SaaSSubscription
            RETURN labels(n)[0] as label, count(*) as count
            ORDER BY count DESC
        """)
        for record in result:
            entity_counts[record["label"]] = record["count"]
        
        # Get relationship counts
        relationship_counts = {}
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(*) as count
            ORDER BY count DESC
            LIMIT 10
        """)
        for record in result:
            relationship_counts[record["type"]] = record["count"]
        
        # Total counts
        result = session.run("MATCH (n) RETURN count(n) as nodes")
        total_nodes = result.single()["nodes"]
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as rels")
        total_relationships = result.single()["rels"]
        
        return {
            "entity_counts": entity_counts,
            "relationship_counts": relationship_counts,
            "total_nodes": total_nodes,
            "total_relationships": total_relationships
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)