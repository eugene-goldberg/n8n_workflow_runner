#!/usr/bin/env python3
"""
SpyroSolutions Agentic RAG using LangChain + neo4j-graphrag-python
This is the proper way to implement agentic RAG with neo4j-graphrag-python
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain.agents import initialize_agent, Tool, AgentType
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory

import neo4j
from neo4j_graphrag.embeddings import OpenAIEmbeddings
from neo4j_graphrag.retrievers import VectorRetriever, HybridRetriever, Text2CypherRetriever
from neo4j_graphrag.generation import GraphRAG
from neo4j_graphrag.llm import OpenAILLM

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


class SpyroLangChainAgent:
    """
    Agentic RAG using LangChain agents with neo4j-graphrag-python retrievers
    """
    
    def __init__(self):
        # Initialize Neo4j driver
        self.driver = neo4j.GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
        )
        
        # Initialize embeddings and LLM
        self.embedder = OpenAIEmbeddings()
        self.llm = OpenAILLM(
            model_name="gpt-4o",
            model_params={"temperature": 0}
        )
        
        # Initialize retrievers
        self._initialize_retrievers()
        
        # Create LangChain tools
        self._create_langchain_tools()
        
        # Initialize LangChain agent
        self._initialize_agent()
        
    def _initialize_retrievers(self):
        """Initialize all neo4j-graphrag retrievers"""
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
        
        # Create GraphRAG instances for each retriever
        self.vector_rag = GraphRAG(
            retriever=self.vector_retriever,
            llm=self.llm
        )
        
        self.hybrid_rag = GraphRAG(
            retriever=self.hybrid_retriever,
            llm=self.llm
        )
        
    def _create_langchain_tools(self):
        """Create LangChain tools for each retriever"""
        # Vector search tool
        def vector_search(query: str) -> str:
            """Semantic similarity search using embeddings"""
            result = self.vector_rag.search(
                query_text=query,
                retriever_config={"top_k": 5}
            )
            return result.answer
            
        # Hybrid search tool
        def hybrid_search(query: str) -> str:
            """Combined vector and keyword search"""
            result = self.hybrid_rag.search(
                query_text=query,
                retriever_config={"top_k": 5}
            )
            return result.answer
            
        # Graph query tool
        def graph_query(query: str) -> str:
            """Direct graph queries for specific entities and relationships"""
            result = self.text2cypher_retriever.search(
                query_text=query
            )
            if result.items:
                # Format the results
                formatted = []
                for item in result.items[:10]:  # Limit to 10 results
                    formatted.append(str(item.content))
                return "\n".join(formatted)
            return "No results found for the graph query."
            
        # Create LangChain tools
        self.tools = [
            Tool(
                name="VectorSearch",
                func=vector_search,
                description="""Useful for semantic similarity search and finding conceptually related information.
                Best for: general questions about features, benefits, concepts, and finding similar content.
                Input should be a natural language question."""
            ),
            Tool(
                name="HybridSearch",
                func=hybrid_search,
                description="""Useful for queries that need both semantic understanding and specific keyword matching.
                Best for: searching for specific terms while also understanding context, product names with features.
                Input should be a natural language question."""
            ),
            Tool(
                name="GraphQuery",
                func=graph_query,
                description="""Useful for specific queries about entities, relationships, counts, and aggregations.
                Best for: finding specific customers, subscriptions, revenue data, team assignments, risks, objectives.
                Examples: 'Which customers have subscriptions over $5M?', 'What are the risks for TechCorp?', 'Count products by type'.
                Input should be a natural language question."""
            )
        ]
        
    def _initialize_agent(self):
        """Initialize the LangChain agent"""
        # Create memory for conversation
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize the agent
        self.agent = initialize_agent(
            tools=self.tools,
            llm=ChatOpenAI(temperature=0, model_name='gpt-4o'),
            agent=AgentType.OPENAI_FUNCTIONS,
            verbose=True,
            memory=self.memory,
            agent_kwargs={
                "system_message": """You are an intelligent assistant for SpyroSolutions.
                You have access to multiple search tools to help answer questions about:
                - Products (SpyroCloud, SpyroAI, SpyroSecure) and their features
                - Customers, subscriptions, and revenue data
                - Teams, projects, and operational information
                - Risks, objectives, and business metrics
                
                Always think about which tool would be most appropriate:
                - Use GraphQuery for specific entities, counts, relationships, or financial data
                - Use HybridSearch when you need both keywords and context
                - Use VectorSearch for general conceptual questions
                
                You can use multiple tools to provide comprehensive answers."""
            }
        )
        
    def query(self, user_query: str) -> Dict[str, Any]:
        """
        Execute an agentic query using LangChain
        The agent will autonomously decide which tools to use
        """
        try:
            # Let the agent handle the query
            response = self.agent.run(user_query)
            
            return {
                "query": user_query,
                "answer": response,
                "agent_type": "LangChain with OpenAI Functions",
                "tools_available": [tool.name for tool in self.tools]
            }
            
        except Exception as e:
            return {
                "query": user_query,
                "answer": f"Error processing query: {str(e)}",
                "agent_type": "LangChain with OpenAI Functions",
                "error": str(e)
            }
            
    def close(self):
        """Close database connection"""
        self.driver.close()


def main():
    """Test the LangChain agent"""
    agent = SpyroLangChainAgent()
    
    test_queries = [
        # Should use GraphQuery
        "Which customers have subscriptions worth more than $5M?",
        
        # Should use VectorSearch or HybridSearch
        "What are the key benefits of SpyroCloud's security features?",
        
        # Should use multiple tools
        "Tell me about TechCorp's subscription value and what products they use",
        
        # Complex query
        "How many high-risk objectives do we have and what's their impact?"
    ]
    
    for query in test_queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print('='*80)
        
        result = agent.query(query)
        
        print(f"\nAnswer: {result['answer']}")
        
    agent.close()


if __name__ == "__main__":
    main()