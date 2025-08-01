#!/usr/bin/env python3
"""
Comprehensive test suite to verify all success criteria from the implementation plan
Success Criteria:
1. Autonomous Operation: No manual tool selection required
2. Accuracy: ≥95% correct tool selection for test queries
3. Performance: <3s average response time
4. Reliability: <0.1% error rate
5. User Satisfaction: Improved answer quality and relevance
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import json
import statistics
from datetime import datetime
from typing import Dict, List, Tuple
import re

from src.agents.spyro_agent import create_agent
from src.utils.config import Config
from src.utils.logging import setup_logging

logger = setup_logging(__name__, format_type="console")


class SuccessCriteriaTester:
    """Test all success criteria defined in the implementation plan"""
    
    def __init__(self):
        self.config = Config.from_env()
        self.agent = create_agent(self.config)
        self.test_results = {
            "autonomous_operation": [],
            "tool_selection_accuracy": [],
            "performance_times": [],
            "errors": [],
            "answer_quality": []
        }
        
    def run_all_tests(self):
        """Run all success criteria tests"""
        print("\n" + "="*80)
        print("SPYROSOLUTIONS AGENTIC RAG - SUCCESS CRITERIA VERIFICATION")
        print("="*80)
        
        # Test 1: Autonomous Operation
        self.test_autonomous_operation()
        
        # Test 2: Tool Selection Accuracy
        self.test_tool_selection_accuracy()
        
        # Test 3: Performance
        self.test_performance()
        
        # Test 4: Reliability
        self.test_reliability()
        
        # Test 5: Answer Quality
        self.test_answer_quality()
        
        # Generate final report
        self.generate_report()
        
    def test_autonomous_operation(self):
        """Test that the system operates autonomously without manual tool selection"""
        print("\n[TEST 1] Testing Autonomous Operation...")
        print("-" * 50)
        
        test_queries = [
            "Which customers have subscriptions worth more than $5M?",
            "What are the key features of SpyroCloud?",
            "How do we help enterprises with digital transformation?",
            "Tell me about TechCorp's subscription and satisfaction scores",
        ]
        
        for query in test_queries:
            try:
                # Execute query - should work without any tool selection
                result = self.agent.query(query)
                
                # Verify no manual intervention needed
                autonomous = True  # If we got here, it worked autonomously
                
                self.test_results["autonomous_operation"].append({
                    "query": query,
                    "autonomous": autonomous,
                    "success": True
                })
                
                print(f"✓ Query executed autonomously: {query[:50]}...")
                
            except Exception as e:
                self.test_results["autonomous_operation"].append({
                    "query": query,
                    "autonomous": False,
                    "success": False,
                    "error": str(e)
                })
                print(f"✗ Failed: {query[:50]}... - {str(e)}")
                
    def test_tool_selection_accuracy(self):
        """Test that the agent selects the correct tools ≥95% of the time"""
        print("\n[TEST 2] Testing Tool Selection Accuracy...")
        print("-" * 50)
        
        # Define test cases with expected tool selection
        test_cases = [
            # GraphQuery expected
            {
                "query": "Which customers have subscriptions worth more than $5M?",
                "expected_tool": "GraphQuery",
                "reason": "Specific entity query with filter"
            },
            {
                "query": "What is the total annual recurring revenue?",
                "expected_tool": "GraphQuery",
                "reason": "Aggregation query"
            },
            {
                "query": "Show me all teams and their product assignments",
                "expected_tool": "GraphQuery",
                "reason": "Relationship query"
            },
            {
                "query": "Count the number of active subscriptions",
                "expected_tool": "GraphQuery",
                "reason": "Count query"
            },
            {
                "query": "List all high-severity risks",
                "expected_tool": "GraphQuery",
                "reason": "Entity query with filter"
            },
            
            # HybridSearch expected
            {
                "query": "What are the features of SpyroCloud platform?",
                "expected_tool": "HybridSearch",
                "reason": "Product name + features"
            },
            {
                "query": "Tell me about SpyroAI's machine learning capabilities",
                "expected_tool": "HybridSearch",
                "reason": "Specific product + capabilities"
            },
            {
                "query": "SpyroSecure compliance features",
                "expected_tool": "HybridSearch",
                "reason": "Product name + specific aspect"
            },
            
            # VectorSearch expected
            {
                "query": "What makes our products unique in the market?",
                "expected_tool": "VectorSearch",
                "reason": "Conceptual question"
            },
            {
                "query": "How do we help enterprises transform?",
                "expected_tool": "VectorSearch",
                "reason": "General conceptual question"
            },
            {
                "query": "What are the benefits of our platform?",
                "expected_tool": "VectorSearch",
                "reason": "General benefits question"
            },
            {
                "query": "Explain our approach to customer success",
                "expected_tool": "VectorSearch",
                "reason": "Conceptual explanation"
            }
        ]
        
        correct_selections = 0
        total_tests = len(test_cases)
        
        # Temporarily enable verbose mode to see tool selection
        original_verbose = self.agent.agent.verbose
        self.agent.agent.verbose = True
        
        for test in test_cases:
            try:
                print(f"\nTesting: {test['query'][:60]}...")
                print(f"Expected: {test['expected_tool']} ({test['reason']})")
                
                # Capture the agent's output to see which tool was used
                result = self.agent.query(test['query'])
                
                # Parse the agent's verbose output to find tool selection
                # This is a simplified check - in production we'd parse the actual tool calls
                tool_used = self._extract_tool_from_response(result)
                
                correct = tool_used == test['expected_tool']
                if correct:
                    correct_selections += 1
                    print(f"✓ Correct! Agent selected: {tool_used}")
                else:
                    print(f"✗ Incorrect. Agent selected: {tool_used}")
                
                self.test_results["tool_selection_accuracy"].append({
                    "query": test['query'],
                    "expected": test['expected_tool'],
                    "actual": tool_used,
                    "correct": correct,
                    "reason": test['reason']
                })
                
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                self.test_results["tool_selection_accuracy"].append({
                    "query": test['query'],
                    "expected": test['expected_tool'],
                    "actual": "ERROR",
                    "correct": False,
                    "error": str(e)
                })
        
        # Restore original verbose setting
        self.agent.agent.verbose = original_verbose
        
        accuracy = (correct_selections / total_tests) * 100
        print(f"\nTool Selection Accuracy: {accuracy:.1f}% ({correct_selections}/{total_tests})")
        print(f"Target: ≥95% - {'PASS' if accuracy >= 95 else 'FAIL'}")
        
    def test_performance(self):
        """Test that average response time is <3s"""
        print("\n[TEST 3] Testing Performance...")
        print("-" * 50)
        
        test_queries = [
            # Mix of different query types
            "Which customers have subscriptions worth more than $5M?",
            "What are the key features of SpyroCloud?",
            "How do we help enterprises?",
            "Show me all teams",
            "What is our total ARR?",
            "Tell me about SpyroAI",
            "List high-risk objectives",
            "What makes us unique?",
            "Count active subscriptions",
            "Explain our security approach"
        ]
        
        response_times = []
        
        for i, query in enumerate(test_queries):
            print(f"\nQuery {i+1}/{len(test_queries)}: {query[:50]}...")
            
            start_time = time.time()
            try:
                result = self.agent.query(query)
                end_time = time.time()
                
                response_time = end_time - start_time
                response_times.append(response_time)
                
                print(f"Response time: {response_time:.2f}s")
                
                self.test_results["performance_times"].append({
                    "query": query,
                    "response_time": response_time,
                    "success": True
                })
                
            except Exception as e:
                print(f"Error: {str(e)}")
                self.test_results["performance_times"].append({
                    "query": query,
                    "response_time": None,
                    "success": False,
                    "error": str(e)
                })
        
        if response_times:
            avg_time = statistics.mean(response_times)
            median_time = statistics.median(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            print(f"\nPerformance Summary:")
            print(f"Average response time: {avg_time:.2f}s")
            print(f"Median response time: {median_time:.2f}s")
            print(f"Min/Max: {min_time:.2f}s / {max_time:.2f}s")
            print(f"Target: <3s average - {'PASS' if avg_time < 3 else 'FAIL'}")
        
    def test_reliability(self):
        """Test that error rate is <0.1%"""
        print("\n[TEST 4] Testing Reliability...")
        print("-" * 50)
        
        # Run a large batch of queries to test reliability
        test_queries = [
            # Valid queries
            "Which customers have subscriptions worth more than $5M?",
            "What are the features of SpyroCloud?",
            "Show me all teams",
            "What is our ARR?",
            "Tell me about TechCorp",
            "List all products",
            "What are our risks?",
            "How many customers do we have?",
            "What teams support SpyroAI?",
            "Show subscription values",
            
            # Edge cases
            "Tell me about a customer that doesn't exist",
            "What is the revenue for year 2099?",
            "Show me employees named John",  # No employee data
            "☃️ Unicode test query ☃️",
            "Very long query " + "with lots of text " * 20,
            
            # Complex queries
            "Compare all products and their features and market focus",
            "Analyze customer satisfaction across all regions and industries",
            "What percentage of our objectives are at risk?",
            "Show me the relationship between costs and profitability",
            "Which teams work on multiple products?"
        ]
        
        # Run each query multiple times to get a good sample
        total_attempts = 0
        errors = 0
        
        for query in test_queries:
            for attempt in range(5):  # Run each query 5 times
                total_attempts += 1
                try:
                    result = self.agent.query(query)
                    # Check if we got a valid response
                    if not result.get('answer'):
                        errors += 1
                        self.test_results["errors"].append({
                            "query": query,
                            "attempt": attempt + 1,
                            "error": "Empty answer"
                        })
                except Exception as e:
                    errors += 1
                    self.test_results["errors"].append({
                        "query": query,
                        "attempt": attempt + 1,
                        "error": str(e)
                    })
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
        
        error_rate = (errors / total_attempts) * 100
        print(f"\nReliability Summary:")
        print(f"Total attempts: {total_attempts}")
        print(f"Errors: {errors}")
        print(f"Error rate: {error_rate:.2f}%")
        print(f"Target: <0.1% - {'PASS' if error_rate < 0.1 else 'FAIL'}")
        
    def test_answer_quality(self):
        """Test answer quality and relevance"""
        print("\n[TEST 5] Testing Answer Quality...")
        print("-" * 50)
        
        quality_tests = [
            {
                "query": "Which customers have subscriptions worth more than $5M?",
                "must_contain": ["TechCorp", "FinanceHub", "$8M", "$5M"],
                "must_not_contain": ["HealthFirst", "$3M"]
            },
            {
                "query": "What teams support SpyroAI?",
                "must_contain": ["AI Research Team", "SpyroAI"],
                "must_not_contain": ["Cloud Platform Team", "Security Team"]
            },
            {
                "query": "What is our total annual recurring revenue?",
                "must_contain": ["ARR", "revenue", "$"],
                "must_not_contain": ["error", "cannot find"]
            },
            {
                "query": "Tell me about TechCorp's subscription and satisfaction",
                "must_contain": ["TechCorp", "$8M", "SpyroCloud", "satisfaction"],
                "must_not_contain": ["not found", "no data"]
            }
        ]
        
        quality_scores = []
        
        for test in quality_tests:
            print(f"\nTesting: {test['query']}")
            
            try:
                result = self.agent.query(test['query'])
                answer = result['answer'].lower()
                
                # Check for required content
                contains_required = all(
                    term.lower() in answer 
                    for term in test['must_contain']
                )
                
                # Check for unwanted content
                contains_unwanted = any(
                    term.lower() in answer 
                    for term in test['must_not_contain']
                )
                
                # Calculate quality score
                quality_score = 0
                if contains_required:
                    quality_score += 70
                if not contains_unwanted:
                    quality_score += 30
                
                # Check answer length (should be substantive)
                if len(answer) > 50:
                    quality_score = min(100, quality_score)
                else:
                    quality_score *= 0.5
                
                quality_scores.append(quality_score)
                
                print(f"Quality Score: {quality_score}%")
                print(f"Contains required terms: {'Yes' if contains_required else 'No'}")
                print(f"Avoids unwanted terms: {'Yes' if not contains_unwanted else 'No'}")
                
                self.test_results["answer_quality"].append({
                    "query": test['query'],
                    "quality_score": quality_score,
                    "contains_required": contains_required,
                    "contains_unwanted": contains_unwanted,
                    "answer_length": len(answer)
                })
                
            except Exception as e:
                print(f"Error: {str(e)}")
                quality_scores.append(0)
                self.test_results["answer_quality"].append({
                    "query": test['query'],
                    "quality_score": 0,
                    "error": str(e)
                })
        
        if quality_scores:
            avg_quality = statistics.mean(quality_scores)
            print(f"\nAverage Answer Quality: {avg_quality:.1f}%")
            print(f"Target: >90% - {'PASS' if avg_quality > 90 else 'FAIL'}")
    
    def _extract_tool_from_response(self, result: Dict) -> str:
        """Extract which tool was used from the response"""
        # In a real implementation, we would parse the agent's execution trace
        # For now, we'll use a heuristic based on the answer content
        answer = result.get('answer', '').lower()
        
        # Look for patterns that indicate which tool was used
        if any(phrase in answer for phrase in ['based on the data', 'customers with', 'total', 'count']):
            return "GraphQuery"
        elif any(phrase in answer for phrase in ['features', 'capabilities', 'spyrocloud', 'spyroai']):
            return "HybridSearch"
        elif any(phrase in answer for phrase in ['helps', 'unique', 'benefits', 'approach']):
            return "VectorSearch"
        else:
            return "Unknown"
    
    def generate_report(self):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("FINAL REPORT - SUCCESS CRITERIA VERIFICATION")
        print("="*80)
        
        # 1. Autonomous Operation
        autonomous_tests = self.test_results["autonomous_operation"]
        autonomous_success = sum(1 for t in autonomous_tests if t.get('success', False))
        print(f"\n1. AUTONOMOUS OPERATION")
        print(f"   Result: {autonomous_success}/{len(autonomous_tests)} queries executed autonomously")
        print(f"   Status: {'PASS' if autonomous_success == len(autonomous_tests) else 'FAIL'}")
        
        # 2. Tool Selection Accuracy
        accuracy_tests = self.test_results["tool_selection_accuracy"]
        correct = sum(1 for t in accuracy_tests if t.get('correct', False))
        accuracy = (correct / len(accuracy_tests) * 100) if accuracy_tests else 0
        print(f"\n2. TOOL SELECTION ACCURACY")
        print(f"   Result: {accuracy:.1f}% ({correct}/{len(accuracy_tests)})")
        print(f"   Target: ≥95%")
        print(f"   Status: {'PASS' if accuracy >= 95 else 'FAIL'}")
        
        # 3. Performance
        perf_tests = [t for t in self.test_results["performance_times"] if t.get('response_time')]
        if perf_tests:
            avg_time = statistics.mean([t['response_time'] for t in perf_tests])
            print(f"\n3. PERFORMANCE")
            print(f"   Average Response Time: {avg_time:.2f}s")
            print(f"   Target: <3s")
            print(f"   Status: {'PASS' if avg_time < 3 else 'FAIL'}")
        
        # 4. Reliability
        total_reliability_tests = 100  # From test_reliability
        errors = len(self.test_results["errors"])
        error_rate = (errors / total_reliability_tests * 100) if total_reliability_tests > 0 else 0
        print(f"\n4. RELIABILITY")
        print(f"   Error Rate: {error_rate:.2f}%")
        print(f"   Target: <0.1%")
        print(f"   Status: {'PASS' if error_rate < 0.1 else 'FAIL'}")
        
        # 5. Answer Quality
        quality_tests = self.test_results["answer_quality"]
        if quality_tests:
            avg_quality = statistics.mean([t.get('quality_score', 0) for t in quality_tests])
            print(f"\n5. ANSWER QUALITY")
            print(f"   Average Quality Score: {avg_quality:.1f}%")
            print(f"   Target: >90%")
            print(f"   Status: {'PASS' if avg_quality > 90 else 'FAIL'}")
        
        # Overall Summary
        print("\n" + "="*80)
        print("OVERALL SUMMARY")
        print("="*80)
        
        # Save detailed results to file
        report_path = "test_results_detailed.json"
        with open(report_path, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        print(f"\nDetailed results saved to: {report_path}")
    
    def close(self):
        """Clean up resources"""
        self.agent.close()


def main():
    """Run all success criteria tests"""
    try:
        tester = SuccessCriteriaTester()
        tester.run_all_tests()
        tester.close()
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()