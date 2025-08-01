#!/usr/bin/env python3
"""
True Agentic RAG System for SpyroSolutions
An LLM-powered agent that intelligently selects and uses multiple tools
to construct comprehensive answers
"""

import asyncio
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from dotenv import load_dotenv
import json

import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import HybridRetriever, Text2CypherRetriever, VectorRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.types import RetrieverResult, RetrieverResultItem

from pydantic import BaseModel
from enum import Enum

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")


class RetrievalTool(str, Enum):
    """Available retrieval tools"""
    VECTOR_SEARCH = "vector_search"
    HYBRID_SEARCH = "hybrid_search"
    TEXT2CYPHER = "text2cypher"
    FULLTEXT_SEARCH = "fulltext_search"


class ToolDecision(BaseModel):
    """Agent's decision about which tools to use"""
    tools: List[RetrievalTool]
    reasoning: str
    specific_queries: Dict[str, str]  # tool -> specific query for that tool


class AgenticRAG:
    """
    Agentic RAG system that intelligently selects and uses multiple retrieval tools
    based on the user's query to construct comprehensive answers
    """
    
    def __init__(self):
        # Initialize Neo4j driver
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Initialize LLM and embedder
        self.llm = OpenAILLM(
            model_name="gpt-4o",
            model_params={"temperature": 0}
        )
        self.embedder = OpenAIEmbeddings()
        
        # Initialize all available retrievers
        self._initialize_retrievers()
        
        # Tool descriptions for the agent
        self.tool_descriptions = {
            RetrievalTool.VECTOR_SEARCH: "Semantic similarity search using embeddings. Best for conceptual questions, finding similar content, and understanding context.",
            RetrievalTool.HYBRID_SEARCH: "Combines vector and keyword search. Best for balanced queries that need both semantic understanding and specific terms.",
            RetrievalTool.TEXT2CYPHER: "Converts natural language to graph queries. Best for specific entity queries, relationships, aggregations, and structured data retrieval.",
            RetrievalTool.FULLTEXT_SEARCH: "Keyword-based search. Best for finding exact terms, names, or specific phrases."
        }
        
    def _initialize_retrievers(self):
        """Initialize all retrieval tools"""
        # Vector Retriever
        self.vector_retriever = VectorRetriever(
            driver=self.driver,
            index_name="spyro_vector_index",
            embedder=self.embedder
        )
        
        # Hybrid Retriever (Vector + Fulltext)
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
            neo4j_schema=self._get_schema()
        )
        
        # Create GraphRAG for answer generation
        self.graph_rag = GraphRAG(
            retriever=self.hybrid_retriever,
            llm=self.llm
        )
        
    def _get_schema(self) -> str:
        """Get the Neo4j schema for Text2Cypher"""
        from enhanced_spyro_api_v2 import SPYRO_SCHEMA
        return SPYRO_SCHEMA
        
    async def _decide_tools(self, query: str) -> ToolDecision:
        """
        Agent decides which tools to use based on the query
        This is the core of the agentic behavior
        """
        decision_prompt = f"""
You are an intelligent retrieval agent for the SpyroSolutions knowledge graph.
Analyze the user's query and decide which retrieval tools to use.

Available tools:
{json.dumps({tool.value: desc for tool, desc in self.tool_descriptions.items()}, indent=2)}

The knowledge graph contains:
- Products (SpyroCloud, SpyroAI, SpyroSecure)
- Customers and their subscriptions
- Teams and projects
- Financial data (ARR, costs, profitability)
- Risks and objectives
- Features and roadmaps

User Query: "{query}"

Analyze this query and decide:
1. Which tools would be most effective (you can use multiple tools)
2. Your reasoning for choosing these tools
3. Specific queries optimized for each tool

Consider:
- Does the query ask for specific entities or relationships? (Use text2cypher)
- Does it ask for conceptual or general information? (Use vector/hybrid search)
- Does it contain specific keywords or exact terms? (Use fulltext/hybrid search)
- Would multiple tools provide complementary information? (Use multiple)

Return a JSON object with:
{{
    "tools": ["tool1", "tool2", ...],
    "reasoning": "explanation of why these tools are appropriate",
    "specific_queries": {{
        "tool1": "optimized query for tool1",
        "tool2": "optimized query for tool2"
    }}
}}
"""
        
        # Request JSON format
        response = await self.llm.ainvoke(decision_prompt, model_params={
            "temperature": 0,
            "response_format": {"type": "json_object"}
        })
        
        # Parse the response
        try:
            # Handle different response formats
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)
                
            decision_data = json.loads(response_text)
            return ToolDecision(**decision_data)
        except Exception as e:
            logger.error(f"Error parsing tool decision: {e}")
            # Fallback to hybrid search
            return ToolDecision(
                tools=[RetrievalTool.HYBRID_SEARCH],
                reasoning="Fallback to hybrid search due to decision parsing error",
                specific_queries={RetrievalTool.HYBRID_SEARCH.value: query}
            )
    
    async def _execute_tool(self, tool: RetrievalTool, query: str) -> Tuple[str, RetrieverResult]:
        """Execute a specific retrieval tool"""
        logger.info(f"Executing {tool.value} with query: {query}")
        
        if tool == RetrievalTool.VECTOR_SEARCH:
            result = self.vector_retriever.search(query)
            tool_name = "Vector Search"
        elif tool == RetrievalTool.HYBRID_SEARCH:
            result = self.hybrid_retriever.search(query)
            tool_name = "Hybrid Search"
        elif tool == RetrievalTool.TEXT2CYPHER:
            result = self.text2cypher_retriever.search(query)
            tool_name = "Text2Cypher"
        else:  # FULLTEXT_SEARCH
            # Use hybrid retriever with vector weight = 0 for pure fulltext
            result = self.hybrid_retriever.search(query, retrieval_params={"vector_weight": 0})
            tool_name = "Fulltext Search"
            
        return tool_name, result
    
    async def _synthesize_answer(self, query: str, tool_results: Dict[str, RetrieverResult], decision: ToolDecision) -> str:
        """Synthesize a comprehensive answer from multiple tool results"""
        # Prepare context from all tools
        context_parts = []
        
        for tool_name, result in tool_results.items():
            if result.items:
                context_parts.append(f"\n=== Results from {tool_name} ===")
                for item in result.items[:5]:  # Limit to top 5 per tool
                    context_parts.append(str(item.content))
        
        full_context = "\n".join(context_parts)
        
        # Generate comprehensive answer
        synthesis_prompt = f"""
You are a helpful assistant for SpyroSolutions. 
Based on the retrieval results from multiple tools, provide a comprehensive answer to the user's query.

User Query: {query}

Tools Used and Reasoning:
{decision.reasoning}

Retrieved Context:
{full_context}

Instructions:
1. Synthesize information from all sources
2. Prioritize factual data from Text2Cypher results when available
3. Use vector/hybrid search results for additional context and explanations
4. Provide a clear, structured answer
5. If results contradict, mention this and explain possible reasons

Answer:
"""
        
        response = await self.llm.ainvoke(synthesis_prompt)
        return response.content
    
    async def query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point for agentic RAG queries
        The agent will:
        1. Analyze the query
        2. Decide which tools to use
        3. Execute chosen tools (potentially in parallel)
        4. Synthesize results into a comprehensive answer
        """
        start_time = datetime.now()
        
        # Step 1: Agent decides which tools to use
        logger.info(f"Analyzing query: {user_query}")
        decision = await self._decide_tools(user_query)
        logger.info(f"Agent decision - Tools: {[t.value for t in decision.tools]}, Reasoning: {decision.reasoning}")
        
        # Step 2: Execute tools in parallel
        tool_tasks = []
        for tool in decision.tools:
            specific_query = decision.specific_queries.get(tool.value, user_query)
            tool_tasks.append(self._execute_tool(tool, specific_query))
        
        # Execute all tools concurrently
        tool_results_list = await asyncio.gather(*tool_tasks)
        
        # Convert to dict
        tool_results = {
            tool_name: result 
            for tool_name, result in tool_results_list
        }
        
        # Step 3: Synthesize answer
        answer = await self._synthesize_answer(user_query, tool_results, decision)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        # Prepare detailed response
        return {
            "query": user_query,
            "answer": answer,
            "agent_decision": {
                "tools_used": [t.value for t in decision.tools],
                "reasoning": decision.reasoning,
                "specific_queries": decision.specific_queries
            },
            "execution_time_seconds": execution_time,
            "tool_results_summary": {
                tool_name: {
                    "items_retrieved": len(result.items),
                    "sample": str(result.items[0].content) if result.items else None
                }
                for tool_name, result in tool_results.items()
            }
        }
    
    def close(self):
        """Close database connection"""
        self.driver.close()


async def main():
    """Test the agentic RAG system with various queries"""
    agentic_rag = AgenticRAG()
    
    # Test queries that should trigger different tool combinations
    test_queries = [
        # Should use Text2Cypher
        "Which customers have subscriptions worth more than $5M?",
        
        # Should use Hybrid/Vector search
        "What are the key benefits of SpyroCloud's security features?",
        
        # Should use multiple tools
        "Tell me about TechCorp's subscription, their risks, and what products they use",
        
        # Complex query requiring multiple tools
        "How do operational costs impact profitability and which objectives are at risk?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        result = await agentic_rag.query(query)
        
        print(f"\nAgent Decision:")
        print(f"  Tools: {result['agent_decision']['tools_used']}")
        print(f"  Reasoning: {result['agent_decision']['reasoning']}")
        
        print(f"\nTool Results Summary:")
        for tool, summary in result['tool_results_summary'].items():
            print(f"  {tool}: {summary['items_retrieved']} items")
            
        print(f"\nAnswer:")
        print(result['answer'])
        
        print(f"\nExecution time: {result['execution_time_seconds']:.2f}s")
    
    agentic_rag.close()


if __name__ == "__main__":
    asyncio.run(main())