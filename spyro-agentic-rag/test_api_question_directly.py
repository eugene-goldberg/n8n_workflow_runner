#!/usr/bin/env python3
"""Test API questions directly through agent to verify no degradation"""

import sys
import time
from src.utils.config import Config
from src.agents.spyro_agent_enhanced_v3 import create_agent

# API question 2
question = "Which customers have success scores below 50?"

print(f"Testing API Question directly through agent:")
print(f"Question: {question}")
print("-" * 80)

config = Config.from_env()
agent = create_agent(config)

try:
    start_time = time.time()
    result = agent.query(question)
    execution_time = time.time() - start_time
    
    answer = result['answer']
    print(f"\nAnswer: {answer}")
    print(f"\nExecution time: {execution_time:.2f}s")
    
    # Simple check for grounded response
    if "StartupXYZ" in answer or "EduTech" in answer or "HealthTech" in answer:
        print("\n✅ GROUNDED - Contains specific customer names")
    else:
        print("\n❌ GENERIC - No specific data")
        
finally:
    agent.close()