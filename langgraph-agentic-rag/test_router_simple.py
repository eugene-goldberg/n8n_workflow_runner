#!/usr/bin/env python3
"""Simple test script for the deterministic router"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Import only what we need
from app.agent.router import DeterministicRouter
from app.schemas.routing import RetrievalStrategy


def test_router():
    """Test the router with various query types"""
    router = DeterministicRouter()
    
    test_queries = [
        # Should route to GRAPH
        ("What is Disney's ARR?", RetrievalStrategy.GRAPH),
        ("How much revenue is at risk if Netflix churns?", RetrievalStrategy.GRAPH),
        ("Show me the relationship between Disney and their subscription revenue", RetrievalStrategy.GRAPH),
        ("Which teams work on the Analytics Platform?", RetrievalStrategy.GRAPH),
        ("What are the top 3 risks to our $10M ARR target?", RetrievalStrategy.GRAPH),
        
        # Should route to VECTOR
        ("What is an SLA?", RetrievalStrategy.VECTOR),
        ("Explain best practices for customer retention", RetrievalStrategy.VECTOR),
        ("What is the definition of monthly recurring revenue?", RetrievalStrategy.VECTOR),
        
        # Should route to HYBRID
        ("Compare Disney and Netflix subscription models", RetrievalStrategy.HYBRID_PARALLEL),
        ("Analyze the Platform Team's impact on customer retention", RetrievalStrategy.HYBRID_SEQUENTIAL),
        
        # Should route to NO_RETRIEVAL
        ("Hello", RetrievalStrategy.NO_RETRIEVAL),
        ("Thank you", RetrievalStrategy.NO_RETRIEVAL),
        
        # Natural business queries that should trigger GRAPH
        ("How much revenue at risk if Disney misses their SLA targets?", RetrievalStrategy.GRAPH),
        ("What concerns have been raised about our largest accounts?", RetrievalStrategy.GRAPH),
        ("Which customers have ARR over $1M?", RetrievalStrategy.GRAPH),
    ]
    
    print("🧪 Testing Deterministic Router\n")
    print("-" * 80)
    
    correct = 0
    total = len(test_queries)
    
    for query, expected_strategy in test_queries:
        result = router.route(query)
        
        # Check if correct
        is_correct = result.strategy == expected_strategy
        if is_correct:
            correct += 1
            
        # Color coding
        color = "\033[92m" if is_correct else "\033[91m"  # Green if correct, red if wrong
        reset = "\033[0m"
        
        print(f"Query: {query}")
        print(f"Expected: {expected_strategy.value}")
        print(f"Got: {color}{result.strategy.value}{reset} (confidence: {result.confidence:.2f})")
        print(f"Reasoning: {result.reasoning}")
        if result.detected_entities:
            print(f"Entities: {', '.join(result.detected_entities)}")
        print("-" * 80)
    
    # Summary
    accuracy = (correct / total) * 100
    print(f"\n✅ Accuracy: {correct}/{total} ({accuracy:.1f}%)")
    
    # Test some specific business queries
    print("\n📊 Business Query Analysis\n")
    business_queries = [
        "How much revenue at risk if Disney misses their SLA targets?",
        "What are the main concerns raised by our top customers?",
        "Which customers have subscription values over $100k?",
        "Show me teams working on high-priority projects",
    ]
    
    for query in business_queries:
        result = router.route(query)
        print(f"Query: {query}")
        print(f"→ Strategy: {result.strategy.value}")
        print(f"→ Entities: {result.detected_entities or 'None detected'}")
        print()


if __name__ == "__main__":
    test_router()