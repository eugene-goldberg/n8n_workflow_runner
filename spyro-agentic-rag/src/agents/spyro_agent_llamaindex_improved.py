"""
SpyroSolutions LangChain Agent - Improved LlamaIndex Schema Version
Implements better error handling and retry logic for Text2CypherRetriever
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json
import time

from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks import get_openai_callback

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.exceptions import (
    Text2CypherRetrievalError, 
    SearchValidationError,
    LLMGenerationError,
    Neo4jGraphRagError
)

from ..utils.config import Config
from typing import Optional as OptionalType
from ..utils.llamaindex_schema import LLAMAINDEX_SCHEMA
from ..utils.cypher_examples_llamaindex import LLAMAINDEX_CYPHER_EXAMPLES, LLAMAINDEX_CYPHER_INSTRUCTIONS
from ..utils.cypher_examples_extracted import EXTRACTED_CYPHER_EXAMPLES, EXTRACTED_CYPHER_INSTRUCTIONS

logger = logging.getLogger(__name__)


class SpyroAgentLlamaIndexImproved:
    """
    Improved LangChain-based agent with better error handling for Text2CypherRetriever
    """
    
    def __init__(self, config: Config):
        self.config = config
        
        # Initialize Neo4j driver
        self.driver = neo4j.GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_username, config.neo4j_password)
        )
        
        # Initialize embeddings and LLM
        self.embedder = OpenAIEmbeddings(
            api_key=config.openai_api_key
        )
        self.llm = OpenAILLM(
            api_key=config.openai_api_key,
            model_name=config.agent_model
        )
        
        # Initialize retrievers and tools
        self._initialize_retrievers()
        self._create_tools()
        self._initialize_agent()
        
        logger.info("SpyroAgent initialized with improved error handling")
    
    def _initialize_retrievers(self):
        """Initialize all retrievers with LlamaIndex schema"""
        # Vector Retriever
        self.vector_retriever = VectorRetriever(
            driver=self.driver,
            index_name=self.config.vector_index_name,
            embedder=self.embedder
        )
        
        # Hybrid Retriever
        self.hybrid_retriever = HybridRetriever(
            driver=self.driver,
            vector_index_name=self.config.vector_index_name,
            fulltext_index_name=self.config.fulltext_index_name,
            embedder=self.embedder
        )
        
        # Text2Cypher Retriever with comprehensive examples
        example_strings = []
        
        # Add extracted examples (prioritize these as they match our actual data)
        for example in EXTRACTED_CYPHER_EXAMPLES:
            example_str = f"Question: {example['question']}\nCypher: {example['cypher']}"
            example_strings.append(example_str)
        
        # Create enhanced schema with more details
        enhanced_schema = LLAMAINDEX_SCHEMA + """
        
Important Notes:
- Cost data is stored in OPERATIONAL_COST nodes with properties: total_monthly_cost, cost_per_customer, infrastructure_cost, support_cost
- Customer commitments are in COMMITMENT nodes with properties: feature_name, risk_level, revenue_at_risk, current_status
- Team efficiency data includes: monthly_cost, revenue_supported, efficiency_ratio
- Products have satisfaction scores in SATISFACTION_SCORE nodes
- All monetary values are numbers, not strings
        """
        
        self.text2cypher_retriever = Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=enhanced_schema,
            examples=example_strings,
            custom_prompt=EXTRACTED_CYPHER_INSTRUCTIONS
        )
        
        # Create GraphRAG instances
        self.vector_rag = GraphRAG(
            retriever=self.vector_retriever,
            llm=self.llm
        )
        
        self.hybrid_rag = GraphRAG(
            retriever=self.hybrid_retriever,
            llm=self.llm
        )
        
        logger.info("Retrievers initialized with enhanced schema")
    
    def _create_tools(self):
        """Create tools with improved error handling"""
        
        def graph_query_with_retry(query: str) -> str:
            """Execute graph queries with retry logic and better error handling"""
            max_retries = 3
            retry_delay = 1.0
            
            for attempt in range(max_retries):
                try:
                    # Log the attempt
                    logger.info(f"Graph query attempt {attempt + 1}: {query[:100]}...")
                    
                    # Try direct Cypher first for common patterns
                    direct_result = self._try_direct_cypher(query)
                    if direct_result:
                        return direct_result
                    
                    # Fall back to Text2CypherRetriever
                    result = self.text2cypher_retriever.search(query_text=query)
                    
                    if result.items:
                        # Format results
                        formatted = []
                        for item in result.items[:10]:
                            content = item.content
                            if hasattr(content, '__dict__'):
                                # Neo4j Record or Node
                                formatted.append(str(dict(content)))
                            elif isinstance(content, dict):
                                formatted.append(json.dumps(content, indent=2))
                            else:
                                formatted.append(str(content))
                        
                        return "Graph query results:\n" + "\n".join(formatted)
                    else:
                        return "No results found for the query."
                        
                except Text2CypherRetrievalError as e:
                    logger.warning(f"Text2Cypher failed on attempt {attempt + 1}: {str(e)}")
                    
                    if attempt < max_retries - 1:
                        # Try rephrasing the query
                        query = self._rephrase_query(query)
                        time.sleep(retry_delay)
                    else:
                        # Final attempt - try a fallback approach
                        return self._fallback_query(query)
                        
                except SearchValidationError as e:
                    logger.error(f"Search validation error: {str(e)}")
                    return f"Invalid search query: {str(e)}"
                    
                except Exception as e:
                    logger.error(f"Unexpected error in graph query: {str(e)}")
                    if attempt == max_retries - 1:
                        return f"Unable to process query after {max_retries} attempts. Error: {str(e)}"
                    time.sleep(retry_delay)
            
            return "Unable to process the query. Please try rephrasing."
        
        def hybrid_search(query: str) -> str:
            """Search using hybrid retriever"""
            try:
                logger.info(f"Hybrid search: {query[:100]}...")
                response = self.hybrid_rag.search(query_text=query, k=self.config.retriever_top_k)
                return response.answer
            except Exception as e:
                logger.error(f"Hybrid search error: {e}")
                return f"Error in hybrid search: {str(e)}"
        
        def vector_search(query: str) -> str:
            """Search using vector retriever"""
            try:
                logger.info(f"Vector search: {query[:100]}...")
                response = self.vector_rag.search(query_text=query, k=self.config.retriever_top_k)
                return response.answer
            except Exception as e:
                logger.error(f"Vector search error: {e}")
                return f"Error in vector search: {str(e)}"
        
        # Define tools with detailed descriptions
        self.tools = [
            Tool(
                name="GraphQuery",
                func=graph_query_with_retry,
                description="""Use this tool for queries about specific entities, relationships, counts, and aggregations in the knowledge graph.
                PERFECT FOR: Finding specific customers, costs, commitments, SLAs, satisfaction scores, team metrics, and financial data.
                EXAMPLES: 
                - 'How much does it cost to run each product across all regions?'
                - 'What is the cost-per-customer for SpyroAI by region?'
                - 'Which customer commitments are at high risk?'
                - 'What are the satisfaction scores for each product?'
                DO NOT USE for: General feature descriptions or conceptual questions."""
            ),
            Tool(
                name="HybridSearch",
                func=hybrid_search,
                description="""Use this tool when the query mentions ANY SPECIFIC PRODUCT NAME (SpyroCloud, SpyroAI, SpyroSecure) along with features, capabilities, or characteristics.
                PERFECT FOR: Product-specific information, features of named products, capabilities of specific offerings."""
            ),
            Tool(
                name="VectorSearch",
                func=vector_search,
                description="""Use this tool ONLY for general conceptual questions that do NOT mention specific product names or entities.
                PERFECT FOR: Abstract concepts, general benefits, overall approach, philosophy questions."""
            )
        ]
        
        logger.info(f"Created {len(self.tools)} tools with improved error handling")
    
    def _try_direct_cypher(self, query: str) -> Optional[str]:
        """Try to match query to known patterns and execute direct Cypher"""
        query_lower = query.lower()
        
        # Direct pattern matching for common queries
        direct_queries = {
            "cost.*product.*region": """
                MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
                WITH p.name as product, sum(c.total_monthly_cost) as total_cost,
                     collect(DISTINCT {region: r.name, cost: c.total_monthly_cost}) as regional_costs
                RETURN product, total_cost, regional_costs
                ORDER BY total_cost DESC
            """,
            "cost.*per.*customer": """
                MATCH (p:__Entity__:PRODUCT)-[:HAS_OPERATIONAL_COST]->(c:__Entity__:OPERATIONAL_COST)-[:INCURS_COST]->(r:__Entity__:REGION)
                WHERE c.cost_per_customer IS NOT NULL
                RETURN p.name as product, r.name as region, c.cost_per_customer as cost_per_customer
                ORDER BY p.name, c.cost_per_customer DESC
            """,
            "commitment.*risk": """
                MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
                WHERE com.risk_level IN ['High', 'Critical']
                RETURN c.name as customer, com.feature_name as feature, com.risk_level as risk, 
                       com.revenue_at_risk as revenue_at_risk
                ORDER BY com.revenue_at_risk DESC
            """,
            "satisfaction.*score": """
                MATCH (p:__Entity__:PRODUCT)-[:HAS_SATISFACTION_SCORE]->(s:__Entity__:SATISFACTION_SCORE)
                RETURN p.name as product, s.average_score as score, s.nps_score as nps
                ORDER BY s.average_score DESC
            """
        }
        
        # Check if query matches any pattern
        for pattern, cypher in direct_queries.items():
            if all(word in query_lower for word in pattern.split(".*")):
                try:
                    with self.driver.session() as session:
                        result = session.run(cypher)
                        records = list(result)
                        if records:
                            formatted = [str(dict(r)) for r in records[:10]]
                            return "Direct query results:\n" + "\n".join(formatted)
                except Exception as e:
                    logger.debug(f"Direct cypher failed: {e}")
                break
        
        return None
    
    def _rephrase_query(self, query: str) -> str:
        """Rephrase query to be more specific for Text2Cypher"""
        rephrases = {
            "cost": "Show the total_monthly_cost from OPERATIONAL_COST nodes",
            "customer": "List CUSTOMER nodes with their properties",
            "product": "Show PRODUCT nodes and their relationships",
            "team": "Display TEAM nodes with monthly_cost and revenue_supported",
            "commitment": "Find COMMITMENT nodes with risk_level and revenue_at_risk"
        }
        
        query_lower = query.lower()
        for key, rephrase in rephrases.items():
            if key in query_lower:
                return f"{rephrase} for: {query}"
        
        return query
    
    def _fallback_query(self, original_query: str) -> str:
        """Fallback approach when Text2Cypher fails"""
        try:
            # Try to extract key entities from the query
            query_lower = original_query.lower()
            
            # Simple entity extraction
            if "cost" in query_lower:
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (c:__Entity__:OPERATIONAL_COST)
                        WHERE c.total_monthly_cost IS NOT NULL
                        RETURN c LIMIT 5
                    """)
                    records = list(result)
                    if records:
                        return f"Found cost data (showing sample): " + str([dict(r['c']) for r in records])
            
            elif "commitment" in query_lower:
                with self.driver.session() as session:
                    result = session.run("""
                        MATCH (com:__Entity__:COMMITMENT)
                        RETURN com LIMIT 5
                    """)
                    records = list(result)
                    if records:
                        return f"Found commitments (showing sample): " + str([dict(r['com']) for r in records])
            
            return f"Unable to generate valid query. Available entity types: PRODUCT, CUSTOMER, TEAM, OPERATIONAL_COST, COMMITMENT, SLA, SATISFACTION_SCORE"
            
        except Exception as e:
            logger.error(f"Fallback query failed: {e}")
            return "Query processing failed. Please try a simpler query."
    
    def _initialize_agent(self):
        """Initialize the LangChain agent with higher limits"""
        # Create memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create agent with higher iteration limit
        self.agent = initialize_agent(
            tools=self.tools,
            llm=ChatOpenAI(
                temperature=self.config.agent_temperature,
                model_name=self.config.agent_model,
                openai_api_key=self.config.openai_api_key,
                request_timeout=60  # Increase timeout
            ),
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.config.agent_verbose,
            memory=self.memory,
            max_iterations=15,  # Increase from default
            max_execution_time=120,  # 2 minutes
            early_stopping_method="generate",  # Let LLM generate final response
            agent_kwargs={
                "system_message": """You are an intelligent assistant for SpyroSolutions with access to a comprehensive knowledge graph.

Your knowledge includes:
- Products: SpyroCloud, SpyroAI, SpyroSecure with detailed cost data
- Operational costs by product and region with cost_per_customer metrics
- Customer commitments with risk levels and revenue at risk
- Team costs and efficiency ratios
- Product satisfaction scores

When queries fail, try rephrasing them or breaking them into simpler parts.
Always prefer the GraphQuery tool for specific data about costs, commitments, teams, etc.

If you encounter errors, explain what data you were looking for and suggest alternative queries."""
            }
        )
        
        logger.info("Agent initialized with improved configuration")
    
    def query(self, question: str) -> str:
        """Process a query using the agent"""
        try:
            logger.info(f"Processing question: {question}")
            
            with get_openai_callback() as cb:
                response = self.agent.run(question)
                
                logger.info(f"Tokens used: {cb.total_tokens} | Cost: ${cb.total_cost:.4f}")
                
                return response
                
        except Exception as e:
            logger.error(f"Agent query failed: {e}")
            
            # Try a direct approach as last resort
            if any(term in question.lower() for term in ["cost", "commitment", "satisfaction", "team"]):
                return self._fallback_query(question)
            
            return f"I encountered an error processing your question. Error: {str(e)}"
    
    def close(self):
        """Clean up resources"""
        self.driver.close()
        logger.info("SpyroAgent closed")


def create_agent(config: OptionalType[Config] = None) -> SpyroAgentLlamaIndexImproved:
    """Factory function to create an agent instance"""
    if config is None:
        config = Config.from_env()
    return SpyroAgentLlamaIndexImproved(config)