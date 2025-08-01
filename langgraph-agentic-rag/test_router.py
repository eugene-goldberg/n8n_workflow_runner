#!/usr/bin/env python3
"""Test script for the deterministic router"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.agent.router import DeterministicRouter
from app.schemas.routing import RetrievalStrategy


def test_router():
    """Test the router with various query types"""
    router = DeterministicRouter()
    
    test_queries = [
        # Should route to GRAPH
        "What is Disney's ARR?",
        "How much revenue is at risk if Netflix churns?",
        "Show me the relationship between Disney and their subscription revenue",
        "Which teams work on the Analytics Platform?",
        "What are the top 3 risks to our $10M ARR target?",
        
        # Should route to VECTOR
        "What is an SLA?",
        "Explain best practices for customer retention",
        "What is the definition of monthly recurring revenue?",
        
        # Should route to HYBRID
        "Compare Disney and Netflix subscription models",
        "Analyze the Platform Team's impact on customer retention",
        
        # Should route to NO_RETRIEVAL
        "Hello",
        "Thank you",
        
        # Natural business queries that should trigger GRAPH
        "How much revenue at risk if Disney misses their SLA targets?",
        "What concerns have been raised about our largest accounts?",
        "Which customers have ARR over $1M?",
    ]
    
    print("🧪 Testing Deterministic Router\n")
    print("-" * 80)
    
    for query in test_queries:
        result = router.route(query)
        
        # Color coding for strategies
        strategy_colors = {
            RetrievalStrategy.GRAPH: "\033[92m",  # Green
            RetrievalStrategy.VECTOR: "\033[94m",  # Blue
            RetrievalStrategy.HYBRID_SEQUENTIAL: "\033[93m",  # Yellow
            RetrievalStrategy.HYBRID_PARALLEL: "\033[93m",  # Yellow
            RetrievalStrategy.NO_RETRIEVAL: "\033[90m",  # Gray
        }
        
        color = strategy_colors.get(result.strategy, "\033[0m")
        reset = "\033[0m"
        
        print(f"Query: {query}")
        print(f"Strategy: {color}{result.strategy.value}{reset}")
        print(f"Confidence: {result.confidence:.2f}")
        print(f"Reasoning: {result.reasoning}")
        if result.detected_entities:
            print(f"Entities: {', '.join(result.detected_entities)}")
        print("-" * 80)
        
    # Test detailed explanation
    print("\n📊 Detailed Analysis Example\n")
    complex_query = "How does Disney's subscription model impact their revenue compared to Netflix?"
    explanation = router.explain_routing(complex_query)
    
    print(f"Query: {complex_query}")
    print(f"Selected Strategy: {explanation['decision']['strategy']}")
    print(f"Entity Analysis: {explanation['entity_analysis']}")
    

if __name__ == "__main__":
    test_router()