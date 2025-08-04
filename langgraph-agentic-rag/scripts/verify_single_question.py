#!/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/venv/bin/python3
"""Verify a single question and check if the answer is grounded in Neo4j data"""

import sys
import os
import asyncio
import json
import time
from datetime import datetime

# Override settings before importing anything else
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['OPENAI_MODEL'] = 'gpt-3.5-turbo'

# Suppress logging
import logging
logging.basicConfig(level=logging.ERROR)
for logger in ["httpx", "langsmith", "neo4j", "openai", "src", "httpcore", "langchain"]:
    logging.getLogger(logger).setLevel(logging.ERROR)

from src.agents.main_agent import AgentRunner


def is_answer_grounded(answer: str) -> bool:
    """Check if an answer is grounded in data"""
    if not answer or len(answer) < 50:
        return False
    
    answer_lower = answer.lower()
    
    negative_indicators = [
        "no results", "not available", "no specific", "sorry",
        "unable to", "did not return", "no information",
        "does not contain", "not found", "did not yield",
        "does not specify", "cannot provide", "graph query did not",
        "no data available", "not in the database", "couldn't find",
        "no relevant", "doesn't have", "no direct"
    ]
    
    return not any(indicator in answer_lower for indicator in negative_indicators)


async def verify_question(question: str) -> dict:
    """Verify a single question"""
    agent = AgentRunner()
    
    start_time = time.time()
    try:
        response = await agent.run(question)
        elapsed = time.time() - start_time
        
        answer = response.get('answer', 'No answer provided')
        is_grounded = is_answer_grounded(answer)
        
        return {
            'question': question,
            'answer': answer,
            'is_grounded': is_grounded,
            'elapsed': elapsed,
            'timestamp': datetime.now().isoformat(),
            'error': None
        }
        
    except Exception as e:
        return {
            'question': question,
            'answer': f"ERROR: {str(e)}",
            'is_grounded': False,
            'elapsed': time.time() - start_time,
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }


def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_single_question.py <question_number>")
        print("       python verify_single_question.py \"<question_text>\"")
        sys.exit(1)
    
    arg = sys.argv[1]
    
    # Check if it's a question number or question text
    if arg.isdigit():
        # Load question by number
        question_num = int(arg)
        
        # Parse questions from file
        questions_file = "/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/docs/BUSINESS_QUESTIONS.md"
        questions = []
        
        with open(questions_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('  -') or (line.startswith('-') and not line.startswith('--')):
                    question = line.lstrip('- ').strip()
                    if question:
                        questions.append(question)
        
        if question_num < 1 or question_num > len(questions):
            print(f"Error: Question number must be between 1 and {len(questions)}")
            sys.exit(1)
        
        question = questions[question_num - 1]
        print(f"Verifying Q{question_num}: {question[:60]}...")
    else:
        # Use provided question text
        question = arg
        print(f"Verifying: {question[:60]}...")
    
    # Run verification
    result = asyncio.run(verify_question(question))
    
    # Print result
    print(f"\nGrounded: {'✅ YES' if result['is_grounded'] else '❌ NO'}")
    print(f"Time: {result['elapsed']:.1f}s")
    print(f"\nAnswer: {result['answer'][:200]}...")
    
    # Save result to file
    output_file = f"verification_q{sys.argv[1]}.json" if sys.argv[1].isdigit() else "verification_custom.json"
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    # Return exit code based on grounding
    sys.exit(0 if result['is_grounded'] else 1)


if __name__ == "__main__":
    main()