"""
SpyroSolutions LangChain Agent - Compatible with both Spyro RAG and LlamaIndex schemas
Implements true agentic RAG with autonomous tool selection
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_community.callbacks import get_openai_callback

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM

from ..utils.config import Config
from ..utils.schema_compatibility import get_unified_schema, get_compatible_cypher
from ..utils.cypher_examples_compatible import COMPATIBLE_CYPHER_EXAMPLES, COMPATIBLE_CYPHER_INSTRUCTIONS

logger = logging.getLogger(__name__)


class SpyroAgentCompatible:
    """
    LangChain-based agent for SpyroSolutions that autonomously selects
    and executes retrieval strategies using neo4j-graphrag-python.
    Compatible with both Spyro RAG and LlamaIndex label formats.
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
            model_name=config.agent_model,
            model_params={"temperature": config.agent_temperature}
        )
        
        # Initialize retrievers
        self._initialize_retrievers()
        
        # Create LangChain tools
        self._create_tools()
        
        # Initialize agent
        self._initialize_agent()
        
        logger.info("SpyroAgentCompatible initialized successfully")
        
    def _initialize_retrievers(self):
        """Initialize all neo4j-graphrag retrievers with schema compatibility"""
        # Vector Retriever
        self.vector_retriever = VectorRetriever(
            driver=self.driver,
            index_name=self.config.vector_index_name,
            embedder=self.embedder
        )
        
        # Hybrid Retriever (Vector + Fulltext)
        self.hybrid_retriever = HybridRetriever(
            driver=self.driver,
            vector_index_name=self.config.vector_index_name,
            fulltext_index_name=self.config.fulltext_index_name,
            embedder=self.embedder
        )
        
        # Text2Cypher Retriever with compatible examples
        # Format examples for the retriever
        example_strings = []
        for example in COMPATIBLE_CYPHER_EXAMPLES:
            example_str = f"Question: {example['question']}\nCypher: {example['cypher']}"
            example_strings.append(example_str)
        
        # Use unified schema that describes both formats
        unified_schema = get_unified_schema()
        
        # Custom prompt for the Text2Cypher retriever
        custom_prompt = f"""You are a Neo4j Cypher query expert. 
Convert the user's question into a Cypher query that works with BOTH labeling conventions:
- Spyro RAG format: (c:Customer)
- LlamaIndex format: (c:__Entity__:CUSTOMER)

Always use flexible patterns like:
(c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))

{COMPATIBLE_CYPHER_INSTRUCTIONS}

Schema:
{unified_schema}

Examples are provided to help you.
"""
        
        self.text2cypher_retriever = Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=unified_schema,
            examples=example_strings,
            custom_prompt=custom_prompt
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
        
        logger.info("Retrievers initialized with schema compatibility")
        
    def _create_tools(self):
        """Create LangChain tools for each retriever"""
        
        def vector_search(query: str) -> str:
            """Execute semantic similarity search"""
            try:
                result = self.vector_rag.search(
                    query_text=query,
                    retriever_config={"top_k": self.config.retriever_top_k}
                )
                return result.answer
            except Exception as e:
                logger.error(f"Vector search error: {e}")
                return f"Error in vector search: {str(e)}"
        
        def hybrid_search(query: str) -> str:
            """Execute combined vector and keyword search"""
            try:
                result = self.hybrid_rag.search(
                    query_text=query,
                    retriever_config={"top_k": self.config.retriever_top_k}
                )
                return result.answer
            except Exception as e:
                logger.error(f"Hybrid search error: {e}")
                return f"Error in hybrid search: {str(e)}"
        
        def graph_query(query: str) -> str:
            """Execute graph queries for specific entities and relationships"""
            try:
                # Add hints for common patterns to help Text2Cypher
                enhanced_query = query
                if "more than" in query.lower() and "$" in query:
                    # Help with monetary comparisons
                    enhanced_query += " (Note: subscription values are stored as strings like '$8M', '$5M')"
                
                # Add hint about dual schema
                enhanced_query += "\n(Remember: We have data in both Spyro RAG format (Customer) and LlamaIndex format (__Entity__:CUSTOMER))"
                
                result = self.text2cypher_retriever.search(query_text=enhanced_query)
                if result.items:
                    # Format results - handle different types of content
                    formatted = []
                    for item in result.items[:10]:
                        content = item.content
                        if hasattr(content, '__dict__'):
                            # Neo4j Record or Node
                            formatted.append(str(content))
                        elif isinstance(content, dict):
                            # Dictionary result
                            formatted.append(json.dumps(content, indent=2))
                        else:
                            # String or other
                            formatted.append(str(content))
                    
                    return "Graph query results:\n" + "\n".join(formatted)
                
                # If no results, try to provide helpful info
                if "customer" in query.lower() or "subscription" in query.lower():
                    # Run a simple diagnostic query
                    diagnostic = self.text2cypher_retriever.search("Show me all customers and their subscription values")
                    if diagnostic.items:
                        return f"No exact matches found. Available data:\n" + "\n".join(str(item.content) for item in diagnostic.items[:5])
                
                return "No results found for the graph query."
            except Exception as e:
                logger.error(f"Graph query error: {e}")
                return f"Error in graph query: {str(e)}"
        
        def unified_search(query: str) -> str:
            """Execute a search that automatically checks both schema formats"""
            try:
                # First try graph query for specific entity requests
                if any(word in query.lower() for word in ['customer', 'team', 'product', 'risk', 'subscription']):
                    result = graph_query(query)
                    if result and "No results found" not in result and "Error" not in result:
                        return result
                
                # Fall back to hybrid search
                return hybrid_search(query)
            except Exception as e:
                logger.error(f"Unified search error: {e}")
                return f"Error in unified search: {str(e)}"
        
        # Define tools with detailed descriptions
        self.tools = [
            Tool(
                name="UnifiedSearch",
                func=unified_search,
                description="""Primary search tool that automatically handles both Spyro RAG and LlamaIndex schemas.
                USE THIS FIRST for any query about customers, products, teams, or other entities.
                It will automatically check both label formats and return comprehensive results.
                EXAMPLES: 
                - 'Show me all customers'
                - 'Which teams support which products?'
                - 'List customers with high-value subscriptions'"""
            ),
            Tool(
                name="GraphQuery",
                func=graph_query,
                description="""Advanced graph query tool for complex queries needing specific Cypher patterns.
                Handles both Spyro RAG (:Customer) and LlamaIndex (:__Entity__:CUSTOMER) formats.
                PERFECT FOR: Aggregations, counts, complex relationship queries.
                EXAMPLES: 
                - 'What percentage of ARR comes from enterprise customers?'
                - 'Count risks by severity across all customers'
                - 'Show revenue breakdown by region'"""
            ),
            Tool(
                name="HybridSearch",
                func=hybrid_search,
                description="""Combined vector and keyword search for content queries.
                Works with documents from both ingestion pipelines.
                PERFECT FOR: Feature descriptions, product capabilities, general information.
                EXAMPLES:
                - 'What are SpyroCloud features?'
                - 'Explain our AI capabilities'
                - 'Security features across products'"""
            ),
            Tool(
                name="VectorSearch",
                func=vector_search,
                description="""Semantic similarity search for conceptual queries.
                PERFECT FOR: Abstract concepts, philosophy, general approach questions.
                EXAMPLES:
                - 'What makes our products unique?'
                - 'How do we approach customer success?'
                - 'Our competitive advantages'"""
            )
        ]
        
        logger.info(f"Created {len(self.tools)} tools with schema compatibility")
        
    def _initialize_agent(self):
        """Initialize the LangChain agent"""
        # Create memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Create agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=ChatOpenAI(
                temperature=self.config.agent_temperature,
                model_name=self.config.agent_model,
                openai_api_key=self.config.openai_api_key
            ),
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.config.agent_verbose,
            memory=self.memory,
            max_iterations=self.config.agent_max_iterations,
            agent_kwargs={
                "system_message": """You are an intelligent assistant for SpyroSolutions with access to a comprehensive knowledge graph.

IMPORTANT: Our knowledge graph contains data from TWO sources with different labeling:
1. Spyro RAG format: Uses labels like :Customer, :Product, :Team
2. LlamaIndex format: Uses labels like :__Entity__:CUSTOMER, :__Entity__:PRODUCT, :__Entity__:TEAM

Both formats contain the same business data - just with different labels.

TOOL SELECTION GUIDE:
1. UnifiedSearch - Use FIRST for most queries. It handles both schemas automatically.
2. GraphQuery - Use for complex aggregations or when UnifiedSearch needs refinement.
3. HybridSearch - Use for content/feature searches across documents.
4. VectorSearch - Use for abstract conceptual questions.

Your knowledge includes:
- Products: SpyroCloud (platform), SpyroAI (AI/ML features), SpyroSecure (security)
- Customers: Including both original (TechCorp, FinanceHub) and new (InnovateTech Solutions, Global Manufacturing Corp)
- Financial: Annual Recurring Revenue (ARR), subscription values, operational costs
- Operations: Teams, projects, risks, objectives
- Relationships: How entities connect and influence each other

Remember: Always try UnifiedSearch first - it knows about both schemas!"""
            }
        )
        
        logger.info("Agent initialized with dual-schema support")
    
    def query(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an agentic query
        
        Args:
            user_query: The user's question
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Dictionary with answer and metadata
        """
        start_time = datetime.now()
        
        try:
            # Track token usage
            with get_openai_callback() as cb:
                # Execute query
                response = self.agent.run(user_query)
                
                # Calculate metrics
                execution_time = (datetime.now() - start_time).total_seconds()
                
                result = {
                    "query": user_query,
                    "answer": response,
                    "metadata": {
                        "agent_type": "LangChain with OpenAI Functions (Schema-Compatible)",
                        "model": self.config.agent_model,
                        "execution_time_seconds": execution_time,
                        "tokens_used": cb.total_tokens,
                        "cost_usd": cb.total_cost,
                        "tools_available": [tool.name for tool in self.tools],
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "schema_support": "Dual (Spyro RAG + LlamaIndex)"
                    }
                }
                
                logger.info(f"Query completed in {execution_time:.2f}s using {cb.total_tokens} tokens")
                
                return result
                
        except Exception as e:
            logger.error(f"Query error: {e}", exc_info=True)
            
            return {
                "query": user_query,
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "metadata": {
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time_seconds": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def clear_memory(self):
        """Clear conversation memory"""
        self.memory.clear()
        logger.info("Conversation memory cleared")
        
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history"""
        messages = self.memory.chat_memory.messages
        history = []
        
        for msg in messages:
            history.append({
                "role": "human" if msg.type == "human" else "assistant",
                "content": msg.content
            })
            
        return history
    
    def close(self):
        """Close database connection"""
        self.driver.close()
        logger.info("Database connection closed")


def create_agent(config: Optional[Config] = None) -> SpyroAgentCompatible:
    """Factory function to create a SpyroAgentCompatible instance"""
    if config is None:
        config = Config()
    return SpyroAgentCompatible(config)