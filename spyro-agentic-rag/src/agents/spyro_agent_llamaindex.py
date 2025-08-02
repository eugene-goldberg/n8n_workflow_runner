"""
SpyroSolutions LangChain Agent - LlamaIndex Schema Only
Implements true agentic RAG with autonomous tool selection using only LlamaIndex schema
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
from ..utils.llamaindex_schema import LLAMAINDEX_SCHEMA
from ..utils.cypher_examples_llamaindex import LLAMAINDEX_CYPHER_EXAMPLES, LLAMAINDEX_CYPHER_INSTRUCTIONS
from ..utils.cypher_examples_extracted import EXTRACTED_CYPHER_EXAMPLES, EXTRACTED_CYPHER_INSTRUCTIONS

logger = logging.getLogger(__name__)


class SpyroAgentLlamaIndex:
    """
    LangChain-based agent for SpyroSolutions that uses only LlamaIndex schema.
    All entities follow the :__Entity__:TYPE pattern.
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
        
        logger.info("SpyroAgentLlamaIndex initialized successfully")
        
    def _initialize_retrievers(self):
        """Initialize all neo4j-graphrag retrievers with LlamaIndex schema"""
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
        
        # Text2Cypher Retriever with both LlamaIndex and Extracted examples
        # Combine examples from both sources for better coverage
        example_strings = []
        
        # Add extracted examples (prioritize these as they match our actual data)
        for example in EXTRACTED_CYPHER_EXAMPLES:
            example_str = f"Question: {example['question']}\nCypher: {example['cypher']}"
            example_strings.append(example_str)
        
        # Add original LlamaIndex examples for fallback
        for example in LLAMAINDEX_CYPHER_EXAMPLES:
            example_str = f"Question: {example['question']}\nCypher: {example['cypher']}"
            example_strings.append(example_str)
        
        self.text2cypher_retriever = Text2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=LLAMAINDEX_SCHEMA,
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
        
        logger.info("Retrievers initialized with LlamaIndex schema")
        
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
        
        # Define tools with detailed descriptions
        self.tools = [
            Tool(
                name="GraphQuery",
                func=graph_query,
                description="""Use this tool for queries about specific entities, relationships, counts, and aggregations in the knowledge graph.
                PERFECT FOR: Finding specific customers, costs, commitments, SLAs, satisfaction scores, team metrics, and financial data.
                EXAMPLES: 
                - 'How much does it cost to run each product across all regions?'
                - 'What is the cost-per-customer for SpyroAI by region?'
                - 'Which customer commitments are at high risk?'
                - 'What are the satisfaction scores for each product?'
                - 'Which teams have the highest costs relative to revenue?'
                - 'Show me SLA violations for customers'
                - 'What features were promised to customers?'
                DO NOT USE for: General feature descriptions or conceptual questions."""
            ),
            Tool(
                name="HybridSearch",
                func=hybrid_search,
                description="""Use this tool when the query mentions ANY SPECIFIC PRODUCT NAME (SpyroCloud, SpyroAI, SpyroSecure) along with features, capabilities, or characteristics.
                PERFECT FOR: Product-specific information, features of named products, capabilities of specific offerings.
                MUST USE WHEN: Query contains 'SpyroCloud', 'SpyroAI', or 'SpyroSecure'
                EXAMPLES:
                - 'What are SpyroCloud features?'
                - 'Tell me about SpyroAI capabilities'
                - 'SpyroSecure security features'
                - 'How does SpyroCloud handle scalability?'
                - 'SpyroAI machine learning features'
                DO NOT USE for: General conceptual questions without specific product names."""
            ),
            Tool(
                name="VectorSearch",
                func=vector_search,
                description="""Use this tool ONLY for general conceptual questions that do NOT mention specific product names or entities.
                PERFECT FOR: Abstract concepts, general benefits, overall approach, philosophy questions.
                EXAMPLES:
                - 'What makes our products unique?' (no specific product mentioned)
                - 'How do we help enterprises?' (general question)
                - 'What are the benefits of cloud computing?' (conceptual)
                - 'Explain our approach to security' (general approach)
                DO NOT USE when: Query mentions SpyroCloud, SpyroAI, SpyroSecure, or asks for specific entity data."""
            )
        ]
        
        logger.info(f"Created {len(self.tools)} tools")
        
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

IMPORTANT: All entities in our knowledge graph use LlamaIndex schema format:
- Customers are stored as :__Entity__:CUSTOMER
- Products are stored as :__Entity__:PRODUCT
- Teams are stored as :__Entity__:TEAM
- And so on...

Your knowledge includes:
- Products: SpyroCloud (platform), SpyroAI (AI/ML features), SpyroSecure (security)
- Customers: InnovateTech Solutions, Global Manufacturing Corp, TechCorp, FinanceHub, and more
- Financial: Annual Recurring Revenue (ARR), subscription values, operational costs
- Operations: Teams, projects, risks, objectives
- Relationships: How entities connect and influence each other

Tool Selection Guide:
- GraphQuery: For specific data (customers, revenue, teams, counts)
- HybridSearch: ALWAYS when SpyroCloud, SpyroAI, or SpyroSecure are mentioned
- VectorSearch: ONLY for general concepts without specific product/entity names

Remember: All data uses the LlamaIndex schema format with :__Entity__:TYPE labels."""
            }
        )
        
        logger.info("Agent initialized with LlamaIndex schema")
    
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
                        "agent_type": "LangChain with OpenAI Functions",
                        "model": self.config.agent_model,
                        "execution_time_seconds": execution_time,
                        "tokens_used": cb.total_tokens,
                        "cost_usd": cb.total_cost,
                        "tools_available": [tool.name for tool in self.tools],
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "schema": "LlamaIndex"
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


def create_agent(config: Optional[Config] = None) -> SpyroAgentLlamaIndex:
    """Factory function to create a SpyroAgentLlamaIndex instance"""
    if config is None:
        config = Config()
    return SpyroAgentLlamaIndex(config)