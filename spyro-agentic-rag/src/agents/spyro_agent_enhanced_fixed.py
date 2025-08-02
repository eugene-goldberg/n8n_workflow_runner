"""
SpyroSolutions LangChain Agent - Enhanced with schema source tracking
Implements true agentic RAG with autonomous tool selection and source visibility
"""

import os
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
import logging
import json
import re

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
from ..utils.cypher_examples_enhanced import ENHANCED_CYPHER_EXAMPLES, ENHANCED_CYPHER_INSTRUCTIONS

logger = logging.getLogger(__name__)


class SchemaTracker:
    """Tracks which schemas were used in a query"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset tracking for new query"""
        self.schemas_used = set()
        self.entity_sources = []
        self.query_patterns = []
    
    def add_entity(self, name: str, labels: List[str]):
        """Track an entity and its source schema"""
        if '__Entity__' in labels:
            schema = "LlamaIndex"
        elif any(label in ['Customer', 'Product', 'Team', 'Risk'] for label in labels):
            schema = "Spyro RAG"
        else:
            schema = "Unknown"
        
        self.schemas_used.add(schema)
        self.entity_sources.append({
            "entity": name,
            "schema": schema,
            "labels": labels
        })
    
    def add_query_pattern(self, pattern: str):
        """Track query patterns used"""
        self.query_patterns.append(pattern)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get tracking summary"""
        return {
            "schemas_accessed": list(self.schemas_used),
            "entity_count_by_schema": self._count_by_schema(),
            "sample_entities": self.entity_sources[:5],
            "query_patterns": list(set(self.query_patterns))
        }
    
    def _count_by_schema(self) -> Dict[str, int]:
        """Count entities by schema"""
        counts = {}
        for entity in self.entity_sources:
            schema = entity['schema']
            counts[schema] = counts.get(schema, 0) + 1
        return counts


class SpyroAgentEnhanced:
    """
    Enhanced LangChain-based agent with schema source tracking.
    Shows users which data sources (Spyro RAG vs LlamaIndex) are being queried.
    """
    
    def __init__(self, config: Config):
        self.config = config
        self.schema_tracker = SchemaTracker()
        
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
        
        logger.info("SpyroAgentEnhanced initialized successfully")
        
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
        
        # Text2Cypher Retriever with enhanced examples
        # Format examples for the retriever
        example_strings = []
        for example in ENHANCED_CYPHER_EXAMPLES:
            example_str = f"Question: {example['question']}\nCypher: {example['cypher']}"
            example_strings.append(example_str)
        
        # Use unified schema that describes both formats
        unified_schema = get_unified_schema()
        
        # Custom prompt for the Text2Cypher retriever
        custom_prompt = f"""You are a Neo4j Cypher query expert. 

{ENHANCED_CYPHER_INSTRUCTIONS}

Schema:
{{schema}}

Examples:
{{examples}}

User Query: {{query_text}}

Generate ONLY the Cypher query without any explanation or markdown formatting.
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
        
    def _analyze_query_results(self, results: Any) -> None:
        """Analyze query results to track schema sources"""
        try:
            # Handle different result types
            if hasattr(results, 'items'):
                for item in results.items:
                    if hasattr(item.content, '_properties'):
                        # Neo4j node
                        name = item.content._properties.get('name', 'Unknown')
                        labels = list(item.content._labels) if hasattr(item.content, '_labels') else []
                        self.schema_tracker.add_entity(name, labels)
            elif isinstance(results, list):
                for result in results:
                    if isinstance(result, dict):
                        name = result.get('name', 'Unknown')
                        labels = result.get('labels', [])
                        self.schema_tracker.add_entity(name, labels)
        except Exception as e:
            logger.debug(f"Could not analyze results: {e}")
        
    def _create_tools(self):
        """Create LangChain tools for each retriever with schema tracking"""
        
        def vector_search(query: str) -> str:
            """Execute semantic similarity search"""
            try:
                self.schema_tracker.add_query_pattern("Vector Search")
                result = self.vector_rag.search(
                    query_text=query,
                    retriever_config={"top_k": self.config.retriever_top_k}
                )
                self._analyze_query_results(result)
                return result.answer
            except Exception as e:
                logger.error(f"Vector search error: {e}")
                return f"Error in vector search: {str(e)}"
        
        def hybrid_search(query: str) -> str:
            """Execute combined vector and keyword search"""
            try:
                self.schema_tracker.add_query_pattern("Hybrid Search (Vector + Keyword)")
                result = self.hybrid_rag.search(
                    query_text=query,
                    retriever_config={"top_k": self.config.retriever_top_k}
                )
                self._analyze_query_results(result)
                return result.answer
            except Exception as e:
                logger.error(f"Hybrid search error: {e}")
                return f"Error in hybrid search: {str(e)}"
        
        def serialize_neo4j_value(value):
            """Convert Neo4j values to JSON-serializable format"""
            if hasattr(value, 'isoformat'):
                return value.isoformat()
            elif hasattr(value, 'to_native'):
                return str(value.to_native())
            elif isinstance(value, (list, tuple)):
                return [serialize_neo4j_value(v) for v in value]
            elif isinstance(value, dict):
                return {k: serialize_neo4j_value(v) for k, v in value.items()}
            return value
        
        def graph_query(query: str) -> str:
            """Execute graph queries for specific entities and relationships"""
            try:
                self.schema_tracker.add_query_pattern("Graph Query (Cypher)")
                
                result = self.text2cypher_retriever.search(query_text=query)
                if result.items:
                    # Format results and track schemas
                    formatted_results = []
                    for item in result.items[:10]:
                        content = item.content
                        
                        # Handle different content types
                        if hasattr(content, '__dict__'):
                            # Neo4j Record or Node
                            if hasattr(content, 'data'):
                                # It's a Record
                                record_dict = {}
                                for key in content.keys():
                                    record_dict[key] = serialize_neo4j_value(content[key])
                                formatted_results.append(record_dict)
                            elif hasattr(content, '_labels'):
                                # It's a Node
                                name = content._properties.get('name', 'Unknown') if hasattr(content, '_properties') else 'Unknown'
                                labels = list(content._labels)
                                self.schema_tracker.add_entity(name, labels)
                                formatted_results.append({
                                    'name': name,
                                    'labels': labels,
                                    'properties': serialize_neo4j_value(content._properties) if hasattr(content, '_properties') else {}
                                })
                            else:
                                formatted_results.append(str(content))
                        elif isinstance(content, dict):
                            # Dictionary result
                            if 'labels' in content and 'name' in content:
                                self.schema_tracker.add_entity(content['name'], content['labels'])
                            formatted_results.append(serialize_neo4j_value(content))
                        else:
                            # String or other
                            formatted_results.append(str(content))
                    
                    return json.dumps(formatted_results, indent=2)
                
                return "No results found for the graph query."
            except Exception as e:
                logger.error(f"Graph query error: {e}")
                return f"Error in graph query: {str(e)}"
        
        def unified_search(query: str) -> str:
            """Execute a search that automatically checks both schema formats"""
            try:
                self.schema_tracker.add_query_pattern("Unified Search")
                
                # Try different search strategies
                # 1. First try graph query for specific questions about entities
                if any(word in query.lower() for word in ['customer', 'product', 'team', 'revenue', 'cost', 'success score', 'risk']):
                    graph_result = graph_query(query)
                    if graph_result and "No results found" not in graph_result and "Error" not in graph_result:
                        return graph_result
                
                # 2. Try hybrid search for general queries
                return hybrid_search(query)
                    
            except Exception as e:
                logger.error(f"Unified search error: {e}")
                # Fall back to hybrid search on error
                return hybrid_search(query)
        
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
        
        logger.info(f"Created {len(self.tools)} tools with schema tracking")
        
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

Your primary goal is to provide accurate, data-grounded answers based on the actual data in our Neo4j knowledge graph.

IMPORTANT DATA CHARACTERISTICS:
- Subscription values are stored as strings like '$8M', '$5M', etc.
- Success scores might be in score or value properties
- Teams have monthly_cost or operational_cost properties
- Customer risks have severity levels: Low, Medium, High, Critical

TOOL SELECTION STRATEGY:
1. For questions about specific metrics, percentages, or calculations → Use GraphQuery
2. For exploring relationships and patterns → Use UnifiedSearch  
3. For finding documents or general information → Use HybridSearch
4. For conceptual or philosophical questions → Use VectorSearch

ANSWER REQUIREMENTS:
- Always provide specific numbers, names, and values from the database
- If a query returns no results, try rephrasing or using a different tool
- Never give generic business advice - always ground answers in actual data
- Include relevant details like success scores, risk levels, and monetary values

KEY ENTITIES IN OUR GRAPH:
- Customers: TechCorp ($8M), GlobalRetail ($9M), AutoDrive ($7.5M), CloudFirst ($7M), etc.
- Products: SpyroCloud, SpyroAI, SpyroSecure  
- Teams: AI Research Team, Security Team, Customer Success Team, DevOps Team
- Metrics: ARR totals ~$71.8M, various success scores, operational costs

When answering, be specific and data-driven. Users expect real insights from the knowledge graph, not general knowledge."""
            }
        )
        
        logger.info("Agent initialized with dual-schema support and tracking")
    
    def query(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Execute an agentic query with schema source tracking
        
        Args:
            user_query: The user's question
            session_id: Optional session ID for conversation tracking
            
        Returns:
            Dictionary with answer, metadata, and schema sources
        """
        start_time = datetime.now()
        
        # Reset schema tracker for new query
        self.schema_tracker.reset()
        
        try:
            # Track token usage
            with get_openai_callback() as cb:
                # Execute query
                response = self.agent.run(user_query)
                
                # Calculate metrics
                execution_time = (datetime.now() - start_time).total_seconds()
                
                # Get schema tracking summary
                schema_summary = self.schema_tracker.get_summary()
                
                result = {
                    "query": user_query,
                    "answer": response,
                    "metadata": {
                        "agent_type": "LangChain with OpenAI Functions (Enhanced)",
                        "model": self.config.agent_model,
                        "execution_time_seconds": execution_time,
                        "tokens_used": cb.total_tokens,
                        "cost_usd": cb.total_cost,
                        "tools_available": [tool.name for tool in self.tools],
                        "session_id": session_id,
                        "timestamp": datetime.now().isoformat(),
                        "schema_support": "Dual (Spyro RAG + LlamaIndex)"
                    },
                    "schema_sources": schema_summary
                }
                
                logger.info(f"Query completed in {execution_time:.2f}s using {cb.total_tokens} tokens")
                logger.info(f"Schemas accessed: {schema_summary['schemas_accessed']}")
                
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
                },
                "schema_sources": self.schema_tracker.get_summary()
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


def create_agent(config: Optional[Config] = None) -> SpyroAgentEnhanced:
    """Factory function to create a SpyroAgentEnhanced instance"""
    if config is None:
        config = Config()
    return SpyroAgentEnhanced(config)