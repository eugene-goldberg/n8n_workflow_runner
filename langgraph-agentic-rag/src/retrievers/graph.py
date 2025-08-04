"""Graph-based retrievers for structured queries and graph traversal."""

import logging
from typing import List, Dict, Any, Optional

from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from neo4j_graphrag.retrievers import VectorCypherRetriever as Neo4jVectorCypherRetriever
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings as Neo4jOpenAIEmbeddings

from config.settings import settings
from src.state.types import RetrievalResult
from .base import BaseRetriever
from src.tools.enhanced_cypher_queries import ENHANCED_CYPHER_QUERIES

logger = logging.getLogger(__name__)


# Enhanced prompt for Text2Cypher with spyro schema context
CYPHER_GENERATION_TEMPLATE = """Task: Generate Cypher statement to query a graph database.
Instructions:
Use only the provided relationship types and properties in the schema.
Do not use any other relationship types or properties that are not provided.

Schema:
{schema}

The graph uses LlamaIndex format with :__Entity__:TYPE labels.
Main entity types: CUSTOMER, PRODUCT, TEAM, PROJECT, RISK, SUBSCRIPTION, REVENUE, FEATURE, 
ROADMAP_ITEM, CUSTOMER_SUCCESS_SCORE, EVENT, COST, PROFITABILITY, OBJECTIVE, SLA

Key relationships:
- (CUSTOMER)-[:HAS_SUCCESS_SCORE]->(CUSTOMER_SUCCESS_SCORE)
- (CUSTOMER)-[:USES]->(PRODUCT)
- (SUBSCRIPTION)-[:GENERATES]->(REVENUE)
- (PROJECT)-[:HAS_RISK]->(RISK)
- (TEAM)-[:SUPPORTS]->(PRODUCT)
- Many entities connected via [:MENTIONS] relationships

Important patterns:
- Customer revenue/ARR: CUSTOMER -> (various paths) -> REVENUE nodes
- Customer events: (CUSTOMER)-[:EXPERIENCED]->(EVENT)
- Event properties: impact (negative/positive/High), severity (high/critical/medium/low), timestamp

Properties vary by entity type:
- CUSTOMER: name (customers don't have direct ARR/revenue properties)
- CUSTOMER_SUCCESS_SCORE: value, score (the actual score value)
- PRODUCT: name
- REVENUE: amount (the revenue/ARR value)
- SUBSCRIPTION: plan, value

Notes:
- Customer ARR is found through relationships to REVENUE entities, not as a direct property
- Events from 2024 won't match "last 90 days" queries in 2025 - adjust date ranges accordingly
- Only 2 EXPERIENCED relationships exist between customers and events in the current data

Note: Do not include any explanations or apologies in your responses.
Do not respond to any questions that might ask anything else than for you to construct a Cypher statement.
Do not include any text except the generated Cypher statement.

The question is:
{question}"""


class GraphRetriever(BaseRetriever):
    """Pure graph retriever using Cypher queries."""
    
    def __init__(self):
        """Initialize the graph retriever."""
        self.graph = Neo4jGraph(
            url=settings.neo4j.uri,
            username=settings.neo4j.username,
            password=settings.neo4j.password
        )
        
        # Refresh schema to get latest
        self.graph.refresh_schema()
        
        self.llm = ChatOpenAI(
            api_key=settings.openai.api_key,
            model=settings.openai.model,
            temperature=0  # Use 0 for more deterministic Cypher generation
        )
        
        # Create prompt template
        cypher_prompt = PromptTemplate(
            input_variables=["schema", "question"],
            template=CYPHER_GENERATION_TEMPLATE
        )
        
        # Initialize GraphCypherQAChain for Text2Cypher
        self.qa_chain = GraphCypherQAChain.from_llm(
            llm=self.llm,
            graph=self.graph,
            verbose=True,
            cypher_prompt=cypher_prompt,
            return_intermediate_steps=True,
            allow_dangerous_requests=True  # We acknowledge the risks - this is for a controlled environment
        )
        
        logger.info("Initialized graph retriever with Text2Cypher")
    
    def _find_matching_enhanced_query(self, query: str) -> Optional[tuple[str, str]]:
        """Find an enhanced query template that matches the user query.
        
        Returns tuple of (query_key, cypher_template) or None
        """
        query_lower = query.lower()
        
        # Keywords mapping to enhanced queries - more flexible matching
        query_mappings = {
            ("percentage", "arr", "success score"): "arr_percentage_by_score",
            ("percentage", "arr", "below"): "arr_percentage_by_score",
            ("80%", "revenue", "risk"): "top_revenue_customers",
            ("generate", "revenue", "risk"): "top_revenue_customers",
            ("negative events", "percentage"): "customers_with_negative_events_percentage",
            ("operational cost", "profitability"): "operational_cost_impact",
            ("team", "operational cost", "revenue"): "team_cost_to_revenue_ratio",
            ("team", "highest", "cost"): "team_cost_to_revenue_ratio",
            ("churn", "risk", "success"): "customer_churn_risk_analysis",
            ("churn", "highest risk"): "customer_churn_risk_analysis",
            ("roadmap", "deadline", "revenue"): "projected_revenue_impact_roadmap",
            ("commitment", "risk"): "top_customer_commitments_and_risks",
            ("feature", "promised"): "features_promised_to_customers",
            ("customer", "waiting", "feature"): "customers_waiting_for_features",
            ("sla", "unmet"): "unmet_sla_commitments",
            ("product", "satisfaction"): "product_satisfaction_scores",
            ("customer", "product", "average"): "customers_per_product_with_value",
            ("product", "operational", "issue"): "products_with_operational_issues",
            ("adoption", "feature"): "feature_adoption_rates",
            ("roadmap", "critical", "retention"): "critical_roadmap_items_for_retention",
            ("roadmap", "behind", "percentage"): "roadmap_behind_schedule_percentage",
            ("roadmap", "behind schedule"): "roadmap_behind_schedule_percentage",
            ("project", "blocked"): "projects_blocked_by_constraints",
            ("revenue", "team member"): "revenue_per_team_member",
            ("revenue", "per", "team"): "revenue_per_team_member",
            ("objective", "risk"): "company_objectives_risk_count",
            ("objective", "highest", "risk"): "company_objectives_risk_count",
            ("high severity", "risk", "mitigation"): "high_severity_risks_without_mitigation",
            ("risk", "multiple", "objective"): "cross_objective_risks",
            ("project", "success rate"): "project_delivery_success_rate",
            ("customer segment", "growth"): "high_growth_customer_segments",
            ("profitability", "cost", "ratio"): "profitability_to_cost_ratio",
            ("region", "expansion"): "regional_expansion_metrics",
            ("feature", "success score"): "features_to_improve_success_scores",
            ("objective", "critical", "growth"): "critical_growth_objectives"
        }
        
        # Check each mapping
        for keywords, query_key in query_mappings.items():
            if all(keyword in query_lower for keyword in keywords):
                if query_key in ENHANCED_CYPHER_QUERIES:
                    return query_key, ENHANCED_CYPHER_QUERIES[query_key]
        
        return None
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve using graph traversal via Text2Cypher.
        
        Args:
            query: Natural language query
            k: Maximum number of results (used as LIMIT in Cypher)
            filters: Optional filters
            
        Returns:
            List of retrieval results
        """
        try:
            # First check if we have an enhanced query for this
            enhanced_match = self._find_matching_enhanced_query(query)
            
            if enhanced_match:
                query_key, cypher_template = enhanced_match
                logger.info(f"Using enhanced query template: {query_key}")
                
                # Extract parameters from the query
                params = self._extract_query_parameters(query, query_key)
                
                # Execute the enhanced query directly
                try:
                    graph_results = self.graph.query(cypher_template, params)
                    cypher_query = cypher_template
                    logger.info(f"Enhanced query returned {len(graph_results)} results")
                except Exception as e:
                    logger.warning(f"Enhanced query failed, falling back to Text2Cypher: {e}")
                    # Fall back to regular Text2Cypher
                    result = self.qa_chain({"query": query})
                    intermediate_steps = result.get("intermediate_steps", [])
                    cypher_query = ""
                    graph_results = []
                    
                    for step in intermediate_steps:
                        if isinstance(step, dict):
                            if "query" in step:
                                cypher_query = step["query"]
                            if "context" in step:
                                graph_results = step["context"]
            else:
                # Use regular Text2Cypher
                result = self.qa_chain({"query": query})
                
                # Extract the generated Cypher query and results
                intermediate_steps = result.get("intermediate_steps", [])
                cypher_query = ""
                graph_results = []
                
                # Parse intermediate steps - they come as list of dicts
                for step in intermediate_steps:
                    if isinstance(step, dict):
                        if "query" in step:
                            cypher_query = step["query"]
                        if "context" in step:
                            graph_results = step["context"]
            
            logger.info(f"Generated/Used Cypher: {cypher_query[:200]}...")
            
            # Convert graph results to RetrievalResult format
            retrieval_results = []
            for i, item in enumerate(graph_results[:k]):
                # Format the result based on its type
                if isinstance(item, dict):
                    content = self._format_dict_result(item)
                else:
                    content = str(item)
                
                retrieval_result = RetrievalResult(
                    content=content,
                    metadata={
                        "cypher_query": cypher_query,
                        "result_index": i,
                        "result_type": type(item).__name__,
                        "enhanced_query": enhanced_match[0] if enhanced_match else None
                    },
                    source="graph_traversal",
                    score=1.0  # Graph queries don't have natural scores
                )
                retrieval_results.append(retrieval_result)
            
            logger.info(f"Graph retrieval returned {len(retrieval_results)} results")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Error in graph retrieval: {e}")
            return []
    
    def _extract_query_parameters(self, query: str, query_key: str) -> Dict[str, Any]:
        """Extract parameters needed for enhanced queries."""
        import re
        params = {}
        
        # Check what parameters the actual query needs
        cypher_template = ENHANCED_CYPHER_QUERIES.get(query_key, "")
        
        # Extract parameters based on what's in the template
        if "$score_threshold" in cypher_template:
            # Extract score threshold (default to 70)
            score_match = re.search(r"scores?\s*(?:below|<|less than)\s*(\d+)", query.lower())
            params["score_threshold"] = int(score_match.group(1)) if score_match else 70
        
        if "$target_percentage" in cypher_template:
            # Extract percentage (default to 80)
            percent_match = re.search(r"(\d+)\s*%", query)
            params["target_percentage"] = int(percent_match.group(1)) if percent_match else 80
        
        if "$days" in cypher_template:
            # Extract days (default to 90)
            days_match = re.search(r"(\d+)\s*days?", query.lower())
            params["days"] = int(days_match.group(1)) if days_match else 90
        
        return params
    
    def _format_dict_result(self, result: Dict[str, Any]) -> str:
        """Format a dictionary result for display."""
        lines = []
        for key, value in result.items():
            if value is not None:
                # Format based on value type
                if isinstance(value, (int, float)):
                    if "revenue" in key.lower() or "arr" in key.lower() or "amount" in key.lower():
                        lines.append(f"{key}: ${value:,.2f}")
                    elif "percentage" in key.lower() or "rate" in key.lower():
                        lines.append(f"{key}: {value}%")
                    else:
                        lines.append(f"{key}: {value}")
                elif isinstance(value, list):
                    if value:  # Only show non-empty lists
                        lines.append(f"{key}: {', '.join(map(str, value))}")
                else:
                    lines.append(f"{key}: {value}")
        return "\n".join(lines)
    
    def get_retriever_type(self) -> str:
        """Get the type identifier for this retriever."""
        return "graph"


class VectorCypherRetriever(BaseRetriever):
    """Advanced retriever combining vector search with graph traversal."""
    
    def __init__(self):
        """Initialize the vector-cypher retriever."""
        # Initialize embeddings
        self.embeddings = Neo4jOpenAIEmbeddings(
            api_key=settings.openai.api_key,
            model="text-embedding-ada-002"
        )
        
        # Define the Cypher template for graph expansion
        # This template is specific to the spyro schema
        retrieval_query = """
        // Start from the vector search results
        WITH node, score
        
        // Expand based on entity type
        CALL {
            WITH node
            WHERE node:CUSTOMER
            OPTIONAL MATCH (node)-[:HAS_SUBSCRIPTION]->(sub:__Entity__:SUBSCRIPTION)
            OPTIONAL MATCH (node)-[:HAS_SUCCESS_SCORE]->(score:__Entity__:CUSTOMER_SUCCESS_SCORE)
            OPTIONAL MATCH (node)-[:USES]->(prod:__Entity__:PRODUCT)
            RETURN 
                {subscriptions: collect(DISTINCT sub.plan), 
                 success_scores: collect(DISTINCT score.value),
                 products: collect(DISTINCT prod.name)} as related
            
            UNION
            
            WITH node
            WHERE node:PRODUCT
            OPTIONAL MATCH (node)-[:HAS_FEATURE]->(feat:__Entity__:FEATURE)
            OPTIONAL MATCH (node)<-[:USES]-(cust:__Entity__:CUSTOMER)
            RETURN 
                {features: collect(DISTINCT feat.name),
                 customers: collect(DISTINCT cust.name)} as related
                 
            UNION
            
            WITH node
            WHERE node:PROJECT
            OPTIONAL MATCH (node)-[:HAS_RISK]->(risk:__Entity__:RISK)
            OPTIONAL MATCH (node)<-[:WORKS_ON]-(team:__Entity__:TEAM)
            RETURN 
                {risks: collect(DISTINCT risk.description),
                 teams: collect(DISTINCT team.name)} as related
        }
        
        // Return enriched results
        RETURN node {
            .*, 
            score: score,
            relationships: related
        } as result
        ORDER BY score DESC
        """
        
        # Initialize the retriever
        self.retriever = Neo4jVectorCypherRetriever(
            driver=self._get_neo4j_driver(),
            index_name="spyro_vector_index",  # Use spyro's vector index
            embedder=self.embeddings,
            retrieval_query=retrieval_query
        )
        
        logger.info("Initialized vector-cypher retriever")
    
    def _get_neo4j_driver(self):
        """Get Neo4j driver instance."""
        from neo4j import GraphDatabase
        return GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve using vector search followed by graph expansion.
        
        Args:
            query: The search query
            k: Number of initial vector results
            filters: Optional filters
            
        Returns:
            List of enriched retrieval results
        """
        try:
            # Perform vector search with graph expansion
            results = self.retriever.search(
                query_text=query,
                top_k=k
            )
            
            # Convert to RetrievalResult format
            retrieval_results = []
            for result in results:
                # Extract the enriched content
                if hasattr(result, 'content'):
                    node_data = result.content if isinstance(result.content, dict) else {"content": str(result.content)}
                else:
                    node_data = {"content": str(result)}
                
                # Build enriched content
                content_parts = []
                
                # Add main entity info
                if 'name' in node_data:
                    content_parts.append(f"Entity: {node_data.get('name')}")
                if 'type' in node_data:
                    content_parts.append(f"Type: {node_data.get('type')}")
                
                # Add relationship data
                if 'relationships' in node_data and node_data['relationships']:
                    rel_data = node_data['relationships']
                    if isinstance(rel_data, dict):
                        for key, values in rel_data.items():
                            if values:
                                content_parts.append(f"{key}: {', '.join(map(str, values))}")
                
                # Add any other properties
                for key, value in node_data.items():
                    if key not in ['name', 'type', 'relationships', 'score'] and value:
                        content_parts.append(f"{key}: {value}")
                
                enriched_content = "\n".join(content_parts)
                
                retrieval_result = RetrievalResult(
                    content=enriched_content,
                    metadata={
                        "entity_type": node_data.get('labels', []),
                        "relationships": node_data.get('relationships', {}),
                        "retrieval_type": "vector_cypher"
                    },
                    source="vector_cypher",
                    score=float(node_data.get("score", 1.0))
                )
                retrieval_results.append(retrieval_result)
            
            logger.info(f"Vector-Cypher retrieval returned {len(retrieval_results)} enriched results")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Error in vector-cypher retrieval: {e}")
            return []
    
    def get_retriever_type(self) -> str:
        """Get the type identifier for this retriever."""
        return "vector_cypher"