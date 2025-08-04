#!/usr/bin/env python3
"""Simple test of graph retriever to debug structure"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.graphs import Neo4jGraph
from langchain.chains import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from config.settings import settings
import json

async def test_graph_qa():
    """Test GraphCypherQAChain directly"""
    
    print("=== TESTING GRAPH QA CHAIN ===\n")
    
    # Initialize components
    graph = Neo4jGraph(
        url=settings.neo4j.uri,
        username=settings.neo4j.username,
        password=settings.neo4j.password
    )
    
    llm = ChatOpenAI(
        api_key=settings.openai.api_key,
        model=settings.openai.model,
        temperature=0
    )
    
    # Simple prompt
    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question"],
        template="""Generate a Cypher query for the question: {question}
        
Schema: {schema}

Return only the Cypher query."""
    )
    
    # Create chain
    qa_chain = GraphCypherQAChain.from_llm(
        llm=llm,
        graph=graph,
        verbose=True,
        cypher_prompt=cypher_prompt,
        return_intermediate_steps=True,
        allow_dangerous_requests=True
    )
    
    # Test query
    query = "How many customers are there?"
    print(f"Query: {query}\n")
    
    result = qa_chain({"query": query})
    
    print("\n=== RESULT STRUCTURE ===")
    print(f"Keys: {result.keys()}")
    print(f"\nResult type: {type(result.get('result'))}")
    print(f"Result content: {result.get('result')}")
    
    if "intermediate_steps" in result:
        print(f"\nIntermediate steps count: {len(result['intermediate_steps'])}")
        for i, step in enumerate(result['intermediate_steps']):
            print(f"\nStep {i}:")
            print(f"  Type: {type(step)}")
            if isinstance(step, dict):
                print(f"  Keys: {step.keys()}")
                print(f"  Query: {step.get('query', 'N/A')}")
                print(f"  Context: {step.get('context', 'N/A')}")
            elif isinstance(step, tuple):
                print(f"  Length: {len(step)}")
                if len(step) > 0:
                    print(f"  Item 0: {step[0]}")
                if len(step) > 1:
                    print(f"  Item 1: {step[1]}")

if __name__ == "__main__":
    asyncio.run(test_graph_qa())