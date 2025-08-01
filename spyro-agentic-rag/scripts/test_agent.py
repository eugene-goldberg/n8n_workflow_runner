#!/usr/bin/env python3
"""
Test script for SpyroSolutions Agentic RAG system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
from datetime import datetime
from typing import List, Dict

from src.agents.spyro_agent import create_agent
from src.utils.config import Config
from src.utils.logging import setup_logging

logger = setup_logging(__name__, format_type="console")


class AgentTester:
    def __init__(self):
        self.config = Config.from_env()
        self.agent = create_agent(self.config)
        self.test_results = []
        
    def run_tests(self):
        """Run all test queries"""
        test_queries = [
            # Should use GraphQuery tool
            {
                "category": "Graph Query",
                "query": "Which customers have subscriptions worth more than $5M?",
                "expected_tool": "GraphQuery"
            },
            {
                "category": "Graph Query",
                "query": "What is the total annual recurring revenue for 2024?",
                "expected_tool": "GraphQuery"
            },
            {
                "category": "Graph Query",
                "query": "Show me all teams and which products they support",
                "expected_tool": "GraphQuery"
            },
            
            # Should use HybridSearch tool
            {
                "category": "Hybrid Search",
                "query": "What are the key features of SpyroCloud platform?",
                "expected_tool": "HybridSearch"
            },
            {
                "category": "Hybrid Search",
                "query": "Tell me about SpyroAI's machine learning capabilities",
                "expected_tool": "HybridSearch"
            },
            
            # Should use VectorSearch tool
            {
                "category": "Vector Search",
                "query": "What makes our products unique in the market?",
                "expected_tool": "VectorSearch"
            },
            {
                "category": "Vector Search",
                "query": "How do we help enterprises with digital transformation?",
                "expected_tool": "VectorSearch"
            },
            
            # Complex queries that might use multiple tools
            {
                "category": "Complex Query",
                "query": "Tell me about TechCorp's subscription details and their satisfaction with our products",
                "expected_tool": "Multiple"
            },
            {
                "category": "Complex Query",
                "query": "What are the risks affecting our objectives and how are we mitigating them?",
                "expected_tool": "Multiple"
            }
        ]
        
        logger.info(f"Running {len(test_queries)} test queries...")
        print("\n" + "="*80)
        
        for i, test in enumerate(test_queries, 1):
            print(f"\nTest {i}/{len(test_queries)}: {test['category']}")
            print(f"Query: {test['query']}")
            print("-" * 40)
            
            start_time = datetime.now()
            
            try:
                # Execute query
                result = self.agent.query(test['query'])
                
                # Extract execution details
                execution_time = result['metadata']['execution_time_seconds']
                tokens_used = result['metadata'].get('tokens_used', 0)
                cost = result['metadata'].get('cost_usd', 0)
                
                # Display results
                print(f"Answer: {result['answer'][:200]}..." if len(result['answer']) > 200 else f"Answer: {result['answer']}")
                print(f"\nExecution Time: {execution_time:.2f}s")
                print(f"Tokens Used: {tokens_used}")
                print(f"Cost: ${cost:.4f}" if cost else "Cost: N/A")
                
                # Store test result
                self.test_results.append({
                    "test_number": i,
                    "category": test['category'],
                    "query": test['query'],
                    "success": True,
                    "execution_time": execution_time,
                    "tokens_used": tokens_used,
                    "cost": cost,
                    "answer_length": len(result['answer'])
                })
                
            except Exception as e:
                print(f"ERROR: {str(e)}")
                logger.error(f"Test {i} failed", exc_info=True)
                
                self.test_results.append({
                    "test_number": i,
                    "category": test['category'],
                    "query": test['query'],
                    "success": False,
                    "error": str(e)
                })
            
            print("="*80)
            
            # Add delay between queries to avoid rate limiting
            if i < len(test_queries):
                print("\nWaiting 2 seconds before next query...")
                import time
                time.sleep(2)
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)
        
        successful = sum(1 for r in self.test_results if r.get('success', False))
        failed = len(self.test_results) - successful
        
        print(f"\nTotal Tests: {len(self.test_results)}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(successful/len(self.test_results)*100):.1f}%")
        
        if successful > 0:
            # Calculate averages for successful tests
            avg_time = sum(r['execution_time'] for r in self.test_results if r.get('success', False)) / successful
            avg_tokens = sum(r.get('tokens_used', 0) for r in self.test_results if r.get('success', False)) / successful
            total_cost = sum(r.get('cost', 0) for r in self.test_results if r.get('success', False))
            
            print(f"\nAverage Execution Time: {avg_time:.2f}s")
            print(f"Average Tokens Used: {avg_tokens:.0f}")
            print(f"Total Cost: ${total_cost:.4f}")
        
        # Show failed tests
        if failed > 0:
            print("\nFailed Tests:")
            for r in self.test_results:
                if not r.get('success', False):
                    print(f"  - Test {r['test_number']}: {r['query'][:50]}...")
                    print(f"    Error: {r.get('error', 'Unknown error')}")
    
    def test_conversation_memory(self):
        """Test conversation memory functionality"""
        print("\n" + "="*80)
        print("TESTING CONVERSATION MEMORY")
        print("="*80)
        
        # Clear memory first
        self.agent.clear_memory()
        print("\nMemory cleared")
        
        # First query
        print("\nQuery 1: Tell me about TechCorp")
        result1 = self.agent.query("Tell me about TechCorp")
        print(f"Answer: {result1['answer'][:150]}...")
        
        # Follow-up query (should remember context)
        print("\nQuery 2: What products do they use?")
        result2 = self.agent.query("What products do they use?")
        print(f"Answer: {result2['answer'][:150]}...")
        
        # Check conversation history
        history = self.agent.get_conversation_history()
        print(f"\nConversation history has {len(history)} messages")
        
    def close(self):
        """Close agent connection"""
        self.agent.close()


def main():
    """Main test function"""
    print("SpyroSolutions Agentic RAG Test Suite")
    print("=====================================")
    
    try:
        tester = AgentTester()
        
        # Run query tests
        tester.run_tests()
        
        # Print summary
        tester.print_summary()
        
        # Test conversation memory
        tester.test_conversation_memory()
        
        # Close connection
        tester.close()
        
        print("\nTest suite completed!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()