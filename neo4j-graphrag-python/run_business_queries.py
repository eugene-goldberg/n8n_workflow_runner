#!/usr/bin/env python3
"""
Run comprehensive business queries demonstrating graph and vector search
"""

import requests
import json
import time
from datetime import datetime

API_URL = "http://localhost:8000"
API_KEY = "spyro-secret-key-123"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Business queries requiring different types of search
BUSINESS_QUERIES = [
    # Vector Search Queries (Semantic Understanding)
    {
        "category": "🔍 VECTOR SEARCH - Semantic Understanding",
        "queries": [
            {
                "question": "Tell me about cloud infrastructure offerings",
                "use_cypher": False,
                "explanation": "Uses semantic similarity to find content about cloud products"
            },
            {
                "question": "What are the security capabilities?",
                "use_cypher": False,
                "explanation": "Semantic search for security-related features"
            },
            {
                "question": "Explain the company's AI services",
                "use_cypher": False,
                "explanation": "Vector search understands 'AI services' relates to analytics products"
            }
        ]
    },
    
    # Graph Traversal Queries (Relationship Navigation)
    {
        "category": "🕸️ GRAPH SEARCH - Relationship Traversal",
        "queries": [
            {
                "question": "Which customers use which products and what are their subscription values?",
                "use_cypher": True,
                "explanation": "Traverses Customer -> Product -> Subscription relationships"
            },
            {
                "question": "What projects are delivering features for which customers?",
                "use_cypher": True,
                "explanation": "Navigates Project -> Feature -> Customer relationships"
            },
            {
                "question": "Show me all risks and their impact on customers and revenue",
                "use_cypher": True,
                "explanation": "Explores Risk -> Customer and Risk -> ARR relationships"
            }
        ]
    },
    
    # Hybrid Queries (Combined Vector + Graph)
    {
        "category": "🔄 HYBRID SEARCH - Combined Capabilities",
        "queries": [
            {
                "question": "Find high-risk customers and their revenue impact",
                "use_cypher": True,
                "explanation": "Semantic understanding of 'high-risk' + graph traversal for revenue"
            },
            {
                "question": "Which teams manage products with the best performance metrics?",
                "use_cypher": True,
                "explanation": "Semantic 'best performance' + graph Team -> Product -> Stats"
            },
            {
                "question": "What are the profitability impacts of projects supporting global expansion?",
                "use_cypher": True,
                "explanation": "Semantic 'global expansion' + graph Project -> Objective -> Profitability"
            }
        ]
    },
    
    # Complex Business Intelligence Queries
    {
        "category": "💼 BUSINESS INTELLIGENCE - Complex Analysis",
        "queries": [
            {
                "question": "Analyze customer health: success scores, risks, and revenue",
                "use_cypher": True,
                "explanation": "Multi-hop graph traversal across customer relationships"
            },
            {
                "question": "What is the total operational cost vs profitability across all projects?",
                "use_cypher": True,
                "explanation": "Aggregation query across Project -> Cost/Profitability"
            },
            {
                "question": "Which products have SLA violations affecting customer satisfaction?",
                "use_cypher": True,
                "explanation": "Complex: Product -> SLA -> Stats -> Customer Success Score"
            }
        ]
    },
    
    # Entity-Specific Queries
    {
        "category": "🎯 ENTITY SEARCH - Specific Information",
        "queries": [
            {
                "question": "Tell me everything about TechCorp Industries",
                "use_cypher": True,
                "explanation": "Entity-centric search with all relationships"
            },
            {
                "question": "What is the status of Project Apollo?",
                "use_cypher": False,
                "explanation": "Direct entity search combining vector and keyword"
            },
            {
                "question": "Show me GlobalBank's complete profile",
                "use_cypher": True,
                "explanation": "Customer entity with all associated data"
            }
        ]
    }
]


def execute_query(question, use_cypher=False):
    """Execute a single query and return results"""
    payload = {
        "question": question,
        "use_cypher": use_cypher,
        "top_k": 10
    }
    
    try:
        response = requests.post(
            f"{API_URL}/query",
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}


def print_separator(char="-", length=80):
    print(char * length)


def main():
    print("🚀 SpyroSolutions Business Query Demonstration")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # Check API health first
    try:
        health = requests.get(f"{API_URL}/health", headers=headers).json()
        print(f"\n✅ API Status: {health['status']}")
        print(f"📊 Graph Nodes: {health['node_count']}")
        print(f"🔍 Indexes: {', '.join(health['indexes_available'])}")
    except:
        print("❌ API is not responding. Please start the API first.")
        return
    
    total_queries = 0
    successful_queries = 0
    total_time = 0
    
    # Execute all queries
    for category_info in BUSINESS_QUERIES:
        print(f"\n\n{category_info['category']}")
        print("=" * 80)
        
        for query_info in category_info['queries']:
            total_queries += 1
            
            print(f"\n📝 Query {total_queries}: {query_info['question']}")
            print(f"🔧 Type: {'Graph + Vector (Hybrid)' if query_info['use_cypher'] else 'Vector Search'}")
            print(f"💡 Purpose: {query_info['explanation']}")
            print_separator()
            
            # Execute query
            start_time = time.time()
            result = execute_query(query_info['question'], query_info['use_cypher'])
            elapsed = (time.time() - start_time) * 1000  # ms
            
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                successful_queries += 1
                total_time += result.get('processing_time_ms', elapsed)
                
                # Format answer for readability
                answer = result['answer']
                if len(answer) > 300:
                    answer = answer[:300] + "..."
                
                print(f"✅ Answer: {answer}")
                print(f"\n📈 Metrics:")
                print(f"   - Context items retrieved: {result['context_items']}")
                print(f"   - Retriever used: {result['retriever_type']}")
                print(f"   - Processing time: {result['processing_time_ms']:.2f}ms")
            
            print_separator()
    
    # Summary statistics
    print("\n\n" + "=" * 80)
    print("📊 QUERY EXECUTION SUMMARY")
    print("=" * 80)
    print(f"Total queries executed: {total_queries}")
    print(f"Successful queries: {successful_queries}")
    print(f"Success rate: {(successful_queries/total_queries)*100:.1f}%")
    print(f"Average response time: {total_time/successful_queries:.2f}ms" if successful_queries > 0 else "N/A")
    
    # Get system stats
    try:
        stats = requests.get(f"{API_URL}/stats", headers=headers).json()
        print(f"\n📈 System Statistics:")
        print(f"   - Total queries processed: {stats['total_queries']}")
        print(f"   - Average response time: {stats['average_response_time_ms']:.2f}ms")
        print(f"   - Queries by retriever: {stats['queries_by_retriever']}")
    except:
        pass
    
    print("\n✨ Demo Complete!")
    print("\nKey Insights:")
    print("- Vector search excels at semantic understanding and finding related concepts")
    print("- Graph search navigates relationships and aggregates connected data")
    print("- Hybrid search combines both for complex business intelligence queries")


if __name__ == "__main__":
    main()