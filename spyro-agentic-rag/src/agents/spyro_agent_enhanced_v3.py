"""
SpyroSolutions Enhanced Agent v3 - With Comprehensive Data Model Context
This version provides the agent with complete knowledge of the actual data model
to enable truly autonomous decision-making.
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from functools import lru_cache
import time

from langchain.agents import AgentExecutor, initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain_core.tools import Tool
from langchain_openai import ChatOpenAI
from neo4j import GraphDatabase
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.types import RetrieverResultItem
from neo4j_graphrag.retrievers import (
    VectorRetriever, VectorCypherRetriever, HybridRetriever,
    HybridCypherRetriever, Text2CypherRetriever
)

from ..utils.cypher_examples_enhanced_v3 import ENHANCED_CYPHER_EXAMPLES, CYPHER_GENERATION_INSTRUCTIONS
from ..utils.neo4j_data_model_context import DATA_MODEL_CONTEXT, QUERY_CONTEXT_HINTS
from ..utils.config import Config
from ..utils.logging import setup_logging
from ..utils.example_formatter import format_instructions, format_examples


logger = setup_logging(__name__)

# Create a separate logger for Cypher queries
import logging.handlers
cypher_logger = logging.getLogger('cypher_queries')
cypher_logger.setLevel(logging.INFO)

# Create file handler for Cypher queries
cypher_handler = logging.handlers.RotatingFileHandler(
    'cypher_queries.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
cypher_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
cypher_logger.addHandler(cypher_handler)


class CypherLoggingText2CypherRetriever(Text2CypherRetriever):
    """Wrapper for Text2CypherRetriever that logs all generated Cypher queries"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_cypher = None
        self._query_count = 0
    
    def get_search_results(self, *args, **kwargs):
        """Override to capture and log Cypher queries"""
        # Get the query text
        query_text = args[0] if args else kwargs.get('query_text', 'Unknown query')
        
        # Call parent method
        result = super().get_search_results(*args, **kwargs)
        
        # Try to extract the generated Cypher from the result
        try:
            # The retriever should have generated a Cypher query
            # Check various possible locations where it might be stored
            cypher_query = None
            
            # Try to get from internal state if available
            if hasattr(self, '_last_generated_cypher'):
                cypher_query = self._last_generated_cypher
            elif hasattr(result, 'metadata') and 'cypher' in result.metadata:
                cypher_query = result.metadata['cypher']
            elif hasattr(result, 'items') and result.items:
                # Try to extract from the first item's metadata
                first_item = result.items[0]
                if hasattr(first_item, 'metadata') and 'cypher' in first_item.metadata:
                    cypher_query = first_item.metadata['cypher']
            
            # If we couldn't find the query in the result, try to intercept it during generation
            if not cypher_query and hasattr(self, 'llm'):
                # This is a bit hacky but necessary to capture the query
                # We'll need to parse it from the LLM response
                pass
            
            if cypher_query:
                self._last_cypher = cypher_query
                self._query_count += 1
                
                # Log the query with context
                cypher_logger.info(f"Query #{self._query_count}")
                cypher_logger.info(f"User Question: {query_text}")
                cypher_logger.info(f"Generated Cypher: {cypher_query}")
                cypher_logger.info(f"Result Count: {len(result.items) if hasattr(result, 'items') else 0}")
                cypher_logger.info("-" * 80)
        except Exception as e:
            cypher_logger.error(f"Error capturing Cypher query: {e}")
        
        return result
    
    def search(self, query_text: str, *args, **kwargs):
        """Override search to capture queries"""
        self._query_count += 1
        
        # Log the incoming query
        cypher_logger.info(f"=== Text2Cypher Query #{self._query_count} ===")
        cypher_logger.info(f"Timestamp: {datetime.now().isoformat()}")
        cypher_logger.info(f"User Question: {query_text}")
        
        try:
            # We need to monkey-patch the LLM to capture its response
            original_llm_invoke = self.llm.invoke
            generated_cypher = None
            
            def capturing_invoke(prompt):
                nonlocal generated_cypher
                response = original_llm_invoke(prompt)
                
                # Extract Cypher from response
                response_text = str(response)
                if "```cypher" in response_text:
                    start = response_text.find("```cypher") + 9
                    end = response_text.find("```", start)
                    if end > start:
                        generated_cypher = response_text[start:end].strip()
                elif "```" in response_text:
                    start = response_text.find("```") + 3
                    end = response_text.find("```", start)
                    if end > start:
                        generated_cypher = response_text[start:end].strip()
                else:
                    # Try to extract any Cypher-like content
                    lines = response_text.split('\n')
                    cypher_lines = []
                    in_query = False
                    for line in lines:
                        if any(keyword in line.upper() for keyword in ['MATCH', 'WHERE', 'RETURN', 'WITH']):
                            in_query = True
                        if in_query:
                            cypher_lines.append(line)
                        if 'RETURN' in line.upper() and in_query:
                            break
                    if cypher_lines:
                        generated_cypher = '\n'.join(cypher_lines)
                
                if generated_cypher:
                    cypher_logger.info(f"Generated Cypher Query:\n{generated_cypher}")
                
                return response
            
            # Temporarily replace the invoke method
            self.llm.invoke = capturing_invoke
            
            # Call parent search
            result = super().search(query_text, *args, **kwargs)
            
            # Log results
            if hasattr(result, 'items'):
                cypher_logger.info(f"Results: {len(result.items)} items returned")
                if result.items and len(result.items) > 0:
                    cypher_logger.info(f"First result: {str(result.items[0])[:200]}...")
            
            # Restore original method
            self.llm.invoke = original_llm_invoke
            
        except Exception as e:
            cypher_logger.error(f"Error during search: {e}")
            cypher_logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            cypher_logger.error(f"Traceback: {traceback.format_exc()}")
            raise
        finally:
            cypher_logger.info("=" * 80 + "\n")
        
        return result


class SchemaSourceTracker:
    """Track which schema sources (Spyro/LlamaIndex) contributed to answers"""
    
    def __init__(self):
        self.entities_found = set()
        self.schemas_used = set()
        self.query_patterns = []
        
    def add_entity(self, entity_name: str, labels: List[str]):
        """Track entities and their schema sources"""
        self.entities_found.add(entity_name)
        if any('__' in label for label in labels):
            self.schemas_used.add('llamaindex')
        else:
            self.schemas_used.add('spyro')
    
    def add_query_pattern(self, pattern: str):
        """Track query patterns used"""
        self.query_patterns.append(pattern)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get tracking summary"""
        return {
            "entities_found": list(self.entities_found),
            "schemas_used": list(self.schemas_used),
            "query_patterns": self.query_patterns,
            "primary_schema": "llamaindex" if "llamaindex" in self.schemas_used else "spyro" if "spyro" in self.schemas_used else "none"
        }
    
    def reset(self):
        """Reset tracking for new query"""
        self.entities_found.clear()
        self.schemas_used.clear()
        self.query_patterns.clear()


class SpyroAgentEnhanced:
    """Enhanced agent with comprehensive data model knowledge for autonomous operation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.driver = None
        self.llm = None
        self.text2cypher_retriever = None
        self.vector_rag = None
        self.hybrid_rag = None
        self.memory = None
        self.agent = None
        self.schema_tracker = SchemaSourceTracker()
        self._initialize()
        
    def _initialize(self):
        """Initialize all components"""
        logger.info("Initializing SpyroSolutions Enhanced Agent v3...")
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(
            self.config.neo4j_uri,
            auth=(self.config.neo4j_username, self.config.neo4j_password)
        )
        
        # Initialize LLM for retrievers (use agent model config)
        self.llm = OpenAILLM(
            model_name=self.config.agent_model,
            model_params={
                "temperature": self.config.agent_temperature,
                "max_tokens": 4000
            }
        )
        
        # Initialize retrievers
        self._initialize_retrievers()
        
        # Create LangChain components
        self.chat_llm = ChatOpenAI(
            model=self.config.agent_model,
            temperature=self.config.agent_temperature
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Initialize conversation memory
        self._initialize_memory()
        
        # Initialize agent with enhanced context
        self._initialize_agent()
        
    def _initialize_retrievers(self):
        """Initialize all retriever types with enhanced examples"""
        # Text2Cypher with comprehensive examples
        cypher_instructions = format_instructions(
            DATA_MODEL_CONTEXT + "\n\n" + CYPHER_GENERATION_INSTRUCTIONS
        )
        
        # Format examples as strings for Text2CypherRetriever
        cypher_examples = []
        for example in ENHANCED_CYPHER_EXAMPLES:
            # Format each example as a string
            example_str = f"Question: {example['question']}\nCypher: {example['cypher'].strip()}"
            cypher_examples.append(example_str)
        
        self.text2cypher_retriever = CypherLoggingText2CypherRetriever(
            driver=self.driver,
            llm=self.llm,
            neo4j_schema=self._get_neo4j_schema(),
            examples=cypher_examples,
            custom_prompt=cypher_instructions
        )
        
        logger.info(f"Text2Cypher initialized with {len(ENHANCED_CYPHER_EXAMPLES)} comprehensive examples")
        
        # Vector retriever
        try:
            self.vector_rag = VectorRetriever(
                driver=self.driver,
                index_name=self.config.vector_index_name,
                embedder=self.llm,
                return_properties=["text", "id"]
            )
        except Exception as e:
            logger.warning(f"Vector retriever initialization failed: {e}")
            self.vector_rag = None
            
        # Hybrid retriever
        try:
            self.hybrid_rag = HybridRetriever(
                driver=self.driver,
                vector_index_name=self.config.vector_index_name,
                fulltext_index_name=self.config.fulltext_index_name,
                embedder=self.llm,
                return_properties=["text", "id"]
            )
        except Exception as e:
            logger.warning(f"Hybrid retriever initialization failed: {e}")
            self.hybrid_rag = None
    
    @lru_cache(maxsize=1)
    def _get_neo4j_schema(self) -> str:
        """Get and cache the Neo4j schema"""
        with self.driver.session() as session:
            # Get basic schema information
            result = session.run("CALL db.schema.visualization()")
            schema = result.single()
            
            # Add data model context
            enhanced_schema = f"""
{DATA_MODEL_CONTEXT}

Technical Schema Details:
{schema}
"""
            return enhanced_schema
    
    def _analyze_query_results(self, result):
        """Analyze query results to track schema sources"""
        try:
            if hasattr(result, 'items') and result.items:
                for item in result.items:
                    if hasattr(item, 'content'):
                        content = item.content
                        if hasattr(content, '_labels'):
                            # Neo4j node
                            name = content._properties.get('name', 'Unknown') if hasattr(content, '_properties') else 'Unknown'
                            labels = list(content._labels) if hasattr(content, '_labels') else []
                            self.schema_tracker.add_entity(name, labels)
        except Exception as e:
            logger.debug(f"Could not analyze results: {e}")
        
    def _create_tools(self):
        """Create LangChain tools with enhanced descriptions"""
        
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
            """Execute graph queries using natural language"""
            try:
                self.schema_tracker.add_query_pattern("Graph Query (Text2Cypher)")
                
                # Log the graph query invocation
                cypher_logger.info(f"=== GraphQuery Tool Invoked ===")
                cypher_logger.info(f"Agent Query: {query}")
                
                # Add context hints based on query type
                enhanced_query = query
                for keyword, hint in QUERY_CONTEXT_HINTS.items():
                    if keyword.lower() in query.lower():
                        enhanced_query = f"{query}\n\nContext: {hint}"
                        cypher_logger.info(f"Added context hint for '{keyword}': {hint}")
                        break
                
                result = self.text2cypher_retriever.search(query_text=enhanced_query)
                if result.items:
                    # Format results
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
            """Execute a comprehensive search across the knowledge graph"""
            try:
                self.schema_tracker.add_query_pattern("Unified Search")
                
                # Try Text2Cypher first for structured queries
                try:
                    graph_result = graph_query(query)
                    if graph_result and graph_result != "No results found for the graph query.":
                        return graph_result
                except:
                    pass
                
                # Fall back to hybrid search
                if self.hybrid_rag:
                    return hybrid_search(query)
                
                # Final fallback to vector search
                if self.vector_rag:
                    return vector_search(query)
                
                return "Unable to search - no retrievers available"
                
            except Exception as e:
                logger.error(f"Unified search error: {e}")
                return f"Error in unified search: {str(e)}"
        
        # Create tools with enhanced descriptions
        tools = [
            Tool(
                name="GraphQuery",
                func=graph_query,
                description="""Use this for specific questions about entities, relationships, metrics, and calculations in the knowledge graph.

IMPORTANT: Pass your question in NATURAL LANGUAGE, not Cypher queries!
Examples of correct usage:
- "What percentage of ARR depends on customers with low success scores?"
- "Which teams have high operational costs?"
- "How many active risks exist?"

DO NOT pass Cypher queries like "MATCH (c:Customer)..." - just ask in plain English!

BEST FOR:
- Customer metrics (ARR, success scores, risks)
- Product analytics (adoption, features, revenue)
- Team performance and costs
- Financial calculations and projections
- Risk analysis and mitigation status

The tool will automatically generate the appropriate Cypher query based on your natural language question."""
            ),
            Tool(
                name="UnifiedSearch",
                func=unified_search,
                description="""Use this for exploratory searches, finding patterns, or when you need a comprehensive view.

BEST FOR:
- Exploring relationships between entities
- Finding all information about a topic
- Pattern discovery
- When GraphQuery returns no results

Automatically tries multiple search strategies to find the best results."""
            )
        ]
        
        # Add optional tools if retrievers are available
        if self.hybrid_rag:
            tools.append(Tool(
                name="HybridSearch",
                func=hybrid_search,
                description="Search using both semantic similarity and keyword matching. Good for finding documents and general information."
            ))
            
        if self.vector_rag:
            tools.append(Tool(
                name="VectorSearch",
                func=vector_search,
                description="Pure semantic search based on meaning. Best for conceptual questions and finding related content."
            ))
        
        return tools
    
    def _initialize_memory(self):
        """Initialize conversation memory"""
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
    
    def _initialize_agent(self):
        """Initialize the agent with enhanced system prompt"""
        self.agent = initialize_agent(
            self.tools,
            self.chat_llm,
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=self.config.agent_verbose,
            memory=self.memory,
            max_iterations=self.config.agent_max_iterations,
            agent_kwargs={
                "system_message": f"""You are an intelligent assistant for SpyroSolutions with access to a comprehensive knowledge graph.

{DATA_MODEL_CONTEXT}

CRITICAL INSTRUCTIONS:
1. Always ground your answers in actual data from the Neo4j knowledge graph
2. Use the correct property names and relationships as documented above
3. Parse financial string values (e.g., '$8M' = 8000000) when doing calculations
4. Remember that many attributes are separate nodes, not properties
5. Use modern Cypher syntax (IS NOT NULL, not EXISTS)
6. When a direct query fails, explore alternative paths to find the data

TOOL SELECTION STRATEGY:
- GraphQuery: For specific metrics, calculations, and entity queries (preferred for most business questions)
  IMPORTANT: Always pass NATURAL LANGUAGE questions to tools, NOT Cypher queries!
  Example: ✓ "What is our total ARR?" NOT ✗ "MATCH (s:SUBSCRIPTION) RETURN SUM..."
- UnifiedSearch: For exploration, patterns, or when GraphQuery returns no results
- HybridSearch: For document search and general information
- VectorSearch: For conceptual questions and similarity-based queries

CRITICAL: Never write Cypher queries yourself. The tools will generate appropriate queries based on your natural language questions.

ANSWER REQUIREMENTS:
- Always provide specific numbers, names, and values from the database
- Show your reasoning when calculations are needed
- If data is missing or sparse, explain what you found and what's missing
- Never give generic responses - always check the actual data first

Remember: The data model documentation above is your source of truth. Use it to generate accurate queries."""
            }
        )
        
        logger.info("Agent initialized with comprehensive data model context")
    
    def query(self, user_query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Execute an agentic query with enhanced context"""
        start_time = datetime.now()
        
        # Reset schema tracker for new query
        self.schema_tracker.reset()
        
        try:
            # Log the query
            logger.info(f"Processing query: {user_query[:100]}...")
            
            # Execute agent
            response = self.agent.run(user_query)
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Get schema tracking summary
            schema_summary = self.schema_tracker.get_summary()
            
            # Estimate tokens (rough approximation)
            prompt_tokens = len(user_query.split()) * 1.3
            completion_tokens = len(response.split()) * 1.3
            total_tokens = int(prompt_tokens + completion_tokens)
            
            # Estimate cost (GPT-4 pricing)
            cost_per_1k_prompt = 0.03
            cost_per_1k_completion = 0.06
            cost = (prompt_tokens / 1000 * cost_per_1k_prompt) + \
                   (completion_tokens / 1000 * cost_per_1k_completion)
            
            result = {
                "query": user_query,
                "answer": response,
                "metadata": {
                    "agent_type": "enhanced_v3",
                    "model": self.config.agent_model,
                    "execution_time_seconds": round(execution_time, 2),
                    "tokens_used": total_tokens,
                    "cost_usd": round(cost, 4),
                    "tools_available": [tool.name for tool in self.tools],
                    "session_id": session_id,
                    "timestamp": datetime.now().isoformat(),
                    "schema_sources": schema_summary
                }
            }
            
            logger.info(f"Query completed in {execution_time:.2f}s using {schema_summary['primary_schema']} schema")
            return result
            
        except Exception as e:
            logger.error(f"Agent query error: {e}", exc_info=True)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "query": user_query,
                "answer": f"I encountered an error while processing your query: {str(e)}",
                "metadata": {
                    "agent_type": "enhanced_v3",
                    "model": self.config.agent_model,
                    "execution_time_seconds": round(execution_time, 2),
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
            }
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the conversation history"""
        messages = []
        if self.memory and hasattr(self.memory, 'chat_memory'):
            for message in self.memory.chat_memory.messages:
                if hasattr(message, 'type') and hasattr(message, 'content'):
                    messages.append({
                        "role": message.type,
                        "content": message.content
                    })
        return messages
    
    def clear_memory(self):
        """Clear conversation memory"""
        if self.memory:
            self.memory.clear()
            logger.info("Conversation memory cleared")
    
    def close(self):
        """Close connections and cleanup"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")


def create_agent(config: Config) -> SpyroAgentEnhanced:
    """Factory function to create an agent instance"""
    return SpyroAgentEnhanced(config)