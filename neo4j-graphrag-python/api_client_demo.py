#!/usr/bin/env python3
"""
Demo client for SpyroSolutions Agentic RAG API
Shows how to interact with all endpoints
"""

import requests
import json
from typing import Dict, List, Any
import time
from datetime import datetime

# API configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "spyro-secret-key-123"  # Default key for demo

# Headers
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


class SpyroRAGClient:
    """Client for interacting with SpyroSolutions RAG API"""
    
    def __init__(self, base_url: str = API_BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url
        self.headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key
        }
    
    def check_health(self) -> Dict[str, Any]:
        """Check API health"""
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        return response.json()
    
    def query(self, question: str, use_cypher: bool = False, top_k: int = 5) -> Dict[str, Any]:
        """Execute a single query"""
        payload = {
            "question": question,
            "use_cypher": use_cypher,
            "top_k": top_k
        }
        response = requests.post(
            f"{self.base_url}/query", 
            json=payload,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def batch_query(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute multiple queries"""
        response = requests.post(
            f"{self.base_url}/batch_query",
            json=queries,
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        response = requests.get(f"{self.base_url}/stats", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        response = requests.get(f"{self.base_url}/graph/stats", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_examples(self) -> Dict[str, Any]:
        """Get example queries"""
        response = requests.get(f"{self.base_url}/examples")
        response.raise_for_status()
        return response.json()


def demo_single_queries(client: SpyroRAGClient):
    """Demo single query functionality"""
    print("\n" + "="*60)
    print("SINGLE QUERY DEMO")
    print("="*60)
    
    queries = [
        ("What products does SpyroSolutions offer?", False),
        ("Which customers are at risk and why?", True),
        ("What is the total ARR across all customers?", True),
        ("Show me the customer success scores", False),
        ("Which teams manage which products?", True)
    ]
    
    for question, use_cypher in queries:
        print(f"\nQ: {question}")
        print(f"Using Cypher: {use_cypher}")
        
        try:
            result = client.query(question, use_cypher)
            print(f"A: {result['answer']}")
            print(f"Context items: {result['context_items']}")
            print(f"Time: {result['processing_time_ms']:.2f}ms")
        except Exception as e:
            print(f"Error: {e}")
        print("-" * 60)


def demo_batch_queries(client: SpyroRAGClient):
    """Demo batch query functionality"""
    print("\n" + "="*60)
    print("BATCH QUERY DEMO")
    print("="*60)
    
    batch_queries = [
        {"question": "What are the operational costs for all projects?", "use_cypher": True},
        {"question": "Which features are on the roadmap?", "use_cypher": True},
        {"question": "What events have affected our customers?", "use_cypher": True}
    ]
    
    print(f"\nSending {len(batch_queries)} queries in batch...")
    
    try:
        result = client.batch_query(batch_queries)
        
        for i, query_result in enumerate(result['results']):
            print(f"\nQuery {i+1}: {query_result['question']}")
            if query_result['status'] == 'success':
                print(f"Answer: {query_result['answer']}")
                print(f"Time: {query_result['processing_time_ms']:.2f}ms")
            else:
                print(f"Error: {query_result.get('error', 'Unknown error')}")
    except Exception as e:
        print(f"Batch query error: {e}")


def demo_statistics(client: SpyroRAGClient):
    """Demo statistics endpoints"""
    print("\n" + "="*60)
    print("STATISTICS DEMO")
    print("="*60)
    
    # System stats
    try:
        stats = client.get_stats()
        print("\nSystem Statistics:")
        print(f"Total queries: {stats['total_queries']}")
        print(f"Average response time: {stats['average_response_time_ms']:.2f}ms")
        print(f"Queries by retriever: {stats['queries_by_retriever']}")
        print(f"Recent queries: {len(stats['most_recent_queries'])}")
    except Exception as e:
        print(f"Stats error: {e}")
    
    # Graph stats
    try:
        graph_stats = client.get_graph_stats()
        print("\nGraph Statistics:")
        print(f"Total nodes: {graph_stats['total_nodes']}")
        print(f"Total relationships: {graph_stats['total_relationships']}")
        print("\nEntity counts:")
        for entity, count in graph_stats['entity_counts'].items():
            print(f"  {entity}: {count}")
    except Exception as e:
        print(f"Graph stats error: {e}")


def main():
    """Run all demos"""
    print("SpyroSolutions Agentic RAG API Client Demo")
    print("="*60)
    
    # Initialize client
    client = SpyroRAGClient()
    
    # Check health
    print("\nChecking API health...")
    try:
        health = client.check_health()
        print(f"Status: {health['status']}")
        print(f"Neo4j connected: {health['neo4j_connected']}")
        print(f"Node count: {health['node_count']}")
        print(f"Indexes: {', '.join(health['indexes_available'])}")
    except Exception as e:
        print(f"❌ API health check failed: {e}")
        print("\nPlease ensure the API is running with:")
        print("  python3 enhanced_spyro_api.py")
        return
    
    # Get examples
    print("\n" + "="*60)
    print("AVAILABLE EXAMPLE QUERIES")
    print("="*60)
    
    try:
        examples = client.get_examples()
        for category in examples['examples']:
            print(f"\n{category['category']}:")
            for query in category['queries']:
                print(f"  - {query['question']} (cypher: {query['use_cypher']})")
    except Exception as e:
        print(f"Examples error: {e}")
    
    # Run demos
    demo_single_queries(client)
    demo_batch_queries(client)
    demo_statistics(client)
    
    print("\n" + "="*60)
    print("Demo complete!")
    print("\nAPI Documentation available at: http://localhost:8000/docs")


if __name__ == "__main__":
    main()