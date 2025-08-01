#!/usr/bin/env python3
"""
True Agentic RAG for SpyroSolutions using neo4j-graphrag-python
This implements an LLM-powered agent that uses tool calling to autonomously
select and execute retrieval strategies.
"""

import asyncio
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
import json

import neo4j
from neo4j_graphrag.llm import OpenAILLM
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import HybridRetriever, Text2CypherRetriever, VectorRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.tool import Tool, ObjectParameter, StringParameter
from neo4j_graphrag.llm.types import ToolCallResponse

# Load environment variables
load_dotenv()

# Neo4j configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

# Schema definition
SPYRO_SCHEMA = """
Node properties:
- **Product**: name (STRING), type (STRING), description (STRING), features (LIST), market_focus (STRING)
- **Customer**: name (STRING), industry (STRING), size (STRING), region (STRING)
- **SaaSSubscription**: product (STRING), value (STRING), start_date (DATE), end_date (DATE), status (STRING)
- **AnnualRecurringRevenue**: amount (STRING), year (INTEGER)
- **Feature**: name (STRING), description (STRING), category (STRING)
- **RoadmapItem**: title (STRING), description (STRING), priority (STRING), estimated_completion (DATE), status (STRING)
- **Team**: name (STRING), department (STRING), size (INTEGER), focus_area (STRING)
- **Project**: name (STRING), description (STRING), status (STRING), technologies (LIST), team_size (INTEGER)
- **Risk**: type (STRING), description (STRING), severity (STRING), mitigation_strategy (STRING), status (STRING)
- **Objective**: title (STRING), description (STRING), target_date (DATE), progress (FLOAT), status (STRING)
- **CustomerSuccessScore**: score (FLOAT), factors (LIST), trend (STRING)
- **Event**: type (STRING), description (STRING), timestamp (DATETIME), impact (STRING)
- **OperationalCost**: category (STRING), amount (FLOAT), frequency (STRING), department (STRING)
- **Profitability**: metric (STRING), value (FLOAT), period (STRING), trend (STRING)

Relationship properties:
- **SUBSCRIBES_TO**: revenue (STRING), contract_length (INTEGER), renewal_probability (FLOAT)
- **HAS_FEATURE**: importance (STRING), usage_frequency (STRING)
- **SUPPORTS**: alignment_score (FLOAT), priority (STRING)
- **AT_RISK**: likelihood (FLOAT), impact (STRING), identified_date (DATE)
- **USES**: satisfaction_score (FLOAT), usage_level (STRING)
- **GENERATES**: monthly_value (FLOAT), growth_rate (FLOAT)
- **INFLUENCED_BY**: impact_level (STRING), sentiment (STRING)
- **AFFECTS**: correlation_strength (FLOAT), impact_type (STRING)
- **IMPACTS**: severity (STRING), recovery_time (STRING)

The relationships are:
(:Customer)-[:SUBSCRIBES_TO]->(:SaaSSubscription)
(:Product)-[:HAS_FEATURE]->(:Feature)
(:Team)-[:SUPPORTS]->(:Product)
(:Objective)-[:AT_RISK]->(:Risk)
(:Customer)-[:USES]->(:Product)
(:SaaSSubscription)-[:GENERATES]->(:AnnualRecurringRevenue)
(:Product)-[:HAS_ROADMAP]->(:RoadmapItem)
(:Team)-[:WORKS_ON]->(:Project)
(:Customer)-[:HAS_SUCCESS_SCORE]->(:CustomerSuccessScore)
(:CustomerSuccessScore)-[:INFLUENCED_BY]->(:Event)
(:OperationalCost)-[:AFFECTS]->(:Profitability)
(:Risk)-[:IMPACTS]->(:Objective)
"""


class SpyroAgenticRAG:
    """
    Agentic RAG system that uses OpenAI tool calling to intelligently
    select and execute retrieval strategies.
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
        
        # Initialize retrievers
        self._initialize_retrievers()
        
        # Create tools for each retriever
        self._create_retriever_tools()
        
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
            neo4j_schema=SPYRO_SCHEMA
        )
        
    def _create_retriever_tools(self):
        """Create tool definitions for each retriever"""
        # Vector search tool
        vector_params = ObjectParameter(
            description="Parameters for vector similarity search",
            properties={
                "query": StringParameter(
                    description="The search query for semantic similarity search",
                    required=True
                ),
            },
            required_properties=["query"],
        )
        self.vector_tool = Tool(
            name="vector_search",
            description="Semantic similarity search using embeddings. Best for conceptual questions, finding similar content, and understanding context.",
            parameters=vector_params,
            execute_func=self._execute_vector_search
        )
        
        # Hybrid search tool
        hybrid_params = ObjectParameter(
            description="Parameters for hybrid search",
            properties={
                "query": StringParameter(
                    description="The search query combining semantic and keyword search",
                    required=True
                ),
            },
            required_properties=["query"],
        )
        self.hybrid_tool = Tool(
            name="hybrid_search",
            description="Combines vector and keyword search. Best for balanced queries that need both semantic understanding and specific terms.",
            parameters=hybrid_params,
            execute_func=self._execute_hybrid_search
        )
        
        # Text2Cypher tool
        cypher_params = ObjectParameter(
            description="Parameters for graph query generation",
            properties={
                "query": StringParameter(
                    description="Natural language query to convert to Cypher for structured data retrieval",
                    required=True
                ),
            },
            required_properties=["query"],
        )
        self.cypher_tool = Tool(
            name="text2cypher",
            description="Converts natural language to graph queries. Best for specific entity queries, relationships, aggregations, and structured data retrieval.",
            parameters=cypher_params,
            execute_func=self._execute_text2cypher
        )
        
        # All tools list
        self.all_tools = [self.vector_tool, self.hybrid_tool, self.cypher_tool]
        
    def _execute_vector_search(self, query: str) -> Dict[str, Any]:
        """Execute vector search"""
        result = self.vector_retriever.search(query_text=query, top_k=5)
        return {
            "tool": "vector_search",
            "query": query,
            "results": [
                {"content": item.content, "metadata": item.metadata}
                for item in result.items
            ]
        }
        
    def _execute_hybrid_search(self, query: str) -> Dict[str, Any]:
        """Execute hybrid search"""
        result = self.hybrid_retriever.search(query_text=query, top_k=5)
        return {
            "tool": "hybrid_search", 
            "query": query,
            "results": [
                {"content": item.content, "metadata": item.metadata}
                for item in result.items
            ]
        }
        
    def _execute_text2cypher(self, query: str) -> Dict[str, Any]:
        """Execute Text2Cypher search"""
        result = self.text2cypher_retriever.search(query_text=query)
        return {
            "tool": "text2cypher",
            "query": query,
            "results": [
                {"content": item.content, "metadata": item.metadata}
                for item in result.items
            ]
        }
        
    async def _agent_plan_retrieval(self, user_query: str) -> ToolCallResponse:
        """
        The agent analyzes the query and decides which tools to use.
        This is where the agentic behavior happens.
        """
        planning_prompt = f"""You are an intelligent retrieval agent for the SpyroSolutions knowledge graph.

The knowledge graph contains:
- Products (SpyroCloud, SpyroAI, SpyroSecure) with features and roadmaps
- Customers with their subscriptions and success scores
- Teams, projects, and operational data
- Financial data (ARR, costs, profitability)
- Risks, objectives, and events

User Query: "{user_query}"

Analyze this query and use the appropriate retrieval tools. You can use multiple tools to gather comprehensive information.

Guidelines:
- Use text2cypher for specific entities, relationships, aggregations, or structured queries
- Use hybrid_search for queries that combine concepts with specific terms
- Use vector_search for conceptual or similarity-based questions
- Feel free to use multiple tools if they would provide complementary information

Create specific, optimized queries for each tool you choose to use."""

        # Get tool calls from the LLM
        response = await self.llm.ainvoke_with_tools(
            input=planning_prompt,
            tools=self.all_tools
        )
        
        return response
        
    async def _execute_tool_calls(self, tool_calls: List[Any]) -> List[Dict[str, Any]]:
        """Execute the tool calls decided by the agent"""
        results = []
        
        for tool_call in tool_calls:
            tool_name = tool_call.name
            args = tool_call.arguments
            
            # Find and execute the appropriate tool
            tool_map = {
                "vector_search": self.vector_tool,
                "hybrid_search": self.hybrid_tool,
                "text2cypher": self.cypher_tool
            }
            
            if tool_name in tool_map:
                tool = tool_map[tool_name]
                result = tool.execute_func(**args)
                results.append(result)
                
        return results
        
    async def _synthesize_answer(self, user_query: str, retrieval_results: List[Dict[str, Any]]) -> str:
        """Synthesize a comprehensive answer from multiple retrieval results"""
        # Prepare context from all retrievals
        context_parts = []
        for result in retrieval_results:
            tool_name = result["tool"]
            context_parts.append(f"\n=== Results from {tool_name} ===")
            for item in result["results"][:5]:  # Limit to top 5 per tool
                context_parts.append(str(item["content"]))
                
        full_context = "\n".join(context_parts)
        
        # Generate answer
        synthesis_prompt = f"""You are a helpful assistant for SpyroSolutions.
Based on the retrieval results, provide a comprehensive answer to the user's query.

User Query: {user_query}

Retrieved Context:
{full_context}

Instructions:
1. Synthesize information from all sources
2. Prioritize factual data from graph queries when available
3. Use vector/hybrid search results for additional context
4. Provide a clear, structured answer
5. Be specific and include relevant details

Answer:"""

        response = await self.llm.ainvoke(synthesis_prompt)
        return response.content
        
    async def query(self, user_query: str) -> Dict[str, Any]:
        """
        Main entry point for agentic queries.
        The agent will:
        1. Analyze the query and decide which tools to use
        2. Execute the chosen tools
        3. Synthesize results into a comprehensive answer
        """
        start_time = datetime.now()
        
        # Step 1: Agent plans which tools to use
        print(f"🤖 Agent analyzing query: {user_query}")
        tool_response = await self._agent_plan_retrieval(user_query)
        
        if not tool_response.tool_calls:
            # Fallback if no tools were called
            print("⚠️  No tools selected, using hybrid search as fallback")
            retrieval_results = [self._execute_hybrid_search(user_query)]
        else:
            # Step 2: Execute the tool calls
            print(f"🔧 Agent selected tools: {[tc.name for tc in tool_response.tool_calls]}")
            retrieval_results = await self._execute_tool_calls(tool_response.tool_calls)
        
        # Step 3: Synthesize answer
        print("📝 Synthesizing comprehensive answer...")
        answer = await self._synthesize_answer(user_query, retrieval_results)
        
        # Calculate execution time
        execution_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "query": user_query,
            "answer": answer,
            "agent_reasoning": tool_response.content if tool_response.content else "Agent decided on tools",
            "tools_used": [tc.name for tc in tool_response.tool_calls] if tool_response.tool_calls else ["hybrid_search"],
            "execution_time_seconds": execution_time,
            "retrieval_summary": {
                result["tool"]: len(result["results"]) 
                for result in retrieval_results
            }
        }
        
    def close(self):
        """Close database connection"""
        self.driver.close()


async def main():
    """Test the agentic RAG system"""
    agent = SpyroAgenticRAG()
    
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
        
        result = await agent.query(query)
        
        print(f"\n🤖 Agent Reasoning: {result['agent_reasoning']}")
        print(f"🔧 Tools Used: {result['tools_used']}")
        print(f"📊 Retrieval Summary: {result['retrieval_summary']}")
        print(f"\n💬 Answer:\n{result['answer']}")
        print(f"\n⏱️  Execution time: {result['execution_time_seconds']:.2f}s")
    
    agent.close()


if __name__ == "__main__":
    asyncio.run(main())