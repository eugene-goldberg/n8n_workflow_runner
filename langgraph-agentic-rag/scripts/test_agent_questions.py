#!/usr/bin/env python3
"""Test the LangGraph agent with business questions from BUSINESS_QUESTIONS.md"""

import sys
import os
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.main_agent import AgentRunner
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
# Suppress some verbose logs
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("langsmith").setLevel(logging.WARNING)

async def test_agent_with_questions():
    """Test agent with business questions from BUSINESS_QUESTIONS.md"""
    
    print("=== TESTING LANGGRAPH AGENT WITH BUSINESS QUESTIONS ===\n")
    
    # Select specific business questions from the file
    business_questions = [
        # Revenue Risk Analysis
        "What percentage of our ARR is dependent on customers with success scores below 70?",
        
        # Customer Health
        "How many customers have success scores below 60, and what is their combined ARR?",
        "What percentage of customers experienced negative events in the last 90 days?",
        "Which customers are at highest risk of churn based on success scores and recent events?",
        
        # Product Performance
        "How many customers use each product, and what is the average subscription value?",
        
        # Team Performance
        "Which teams have the highest operational costs relative to the revenue they support?",
        
        # Risk Management
        "How many high-severity risks are currently without mitigation strategies?",
        "What is the potential revenue impact of our top 5 identified risks?",
        
        # Project Delivery
        "What percentage of projects are at risk of missing deadlines?",
        
        # Strategic Planning
        "Which customer segments offer the highest growth potential?"
    ]
    
    try:
        agent = AgentRunner()
        
        # Test first 5 questions to avoid rate limits
        for i, question in enumerate(business_questions[:5], 1):
            print(f"\n{'='*80}")
            print(f"Question {i}: {question}")
            print(f"{'='*80}")
            
            try:
                result = await agent.run(question)
                
                print(f"\n📊 Answer:")
                print(f"{result['answer']}")
                
                print(f"\n🔍 Metadata:")
                print(f"  - Route: {result['metadata'].get('route')}")
                print(f"  - Tools used: {result['metadata'].get('tools_used')}")
                print(f"  - Errors: {result['metadata'].get('error_count', 0)}")
                
                # Add a small delay to avoid rate limits
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"\n❌ Error: {e}")
                import traceback
                traceback.print_exc()
    
    except Exception as e:
        print(f"Failed to initialize agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent_with_questions())