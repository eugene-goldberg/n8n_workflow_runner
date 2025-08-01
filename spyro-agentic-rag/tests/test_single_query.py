#!/usr/bin/env python3
"""Test a single query to debug"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.agents.spyro_agent import create_agent
from src.utils.config import Config

config = Config.from_env()
agent = create_agent(config)

# Enable verbose to see tool selection
agent.agent.verbose = True

print("Testing: 'What are SpyroCloud features?'")
print("-" * 40)

try:
    result = agent.query("What are SpyroCloud features?")
    print(f"\nAnswer: {result['answer'][:100]}...")
except Exception as e:
    print(f"Error: {e}")

agent.close()