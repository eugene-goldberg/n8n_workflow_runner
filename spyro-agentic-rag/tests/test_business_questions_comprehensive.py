#!/usr/bin/env python3
"""
Comprehensive test suite with real business questions from SpyroSolutions executives
Tests the system's ability to handle complex, real-world queries
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


class BusinessQuestionsTester:
    """Test suite for comprehensive business questions"""
    
    def __init__(self):
        self.config = Config.from_env()
        self.config.agent_verbose = False  # Disable verbose for cleaner output
        self.agent = create_agent(self.config)
        self.results = {
            "tool_selection": [],
            "performance": [],
            "answer_quality": [],
            "errors": [],
            "by_category": {}
        }
        
    def get_business_questions(self) -> Dict[str, List[Tuple[str, str]]]:
        """Get categorized business questions with expected tool types"""
        return {
            "Revenue & Financial Performance": [
                # Revenue Risk Analysis
                ("How much revenue will be at risk if TechCorp misses their SLA next month?", "GraphQuery"),
                ("What percentage of our ARR is dependent on customers with success scores below 70?", "GraphQuery"),
                ("Which customers generate 80% of our revenue, and what are their current risk profiles?", "GraphQuery"),
                ("How much revenue is at risk from customers experiencing negative events in the last quarter?", "GraphQuery"),
                ("What is the projected revenue impact if we miss our roadmap deadlines for committed features?", "GraphQuery"),
                
                # Cost & Profitability
                ("How much does it cost to run SpyroCloud across all regions?", "GraphQuery"),
                ("What is the profitability margin for each product line?", "GraphQuery"),
                ("How do operational costs impact profitability for our top 10 customers?", "GraphQuery"),
                ("Which teams have the highest operational costs relative to the revenue they support?", "GraphQuery"),
                ("What is the cost-per-customer for SpyroAI?", "GraphQuery"),
            ],
            
            "Customer Success & Retention": [
                # Customer Health
                ("What are the top 5 customers by revenue, and what are their current success scores?", "GraphQuery"),
                ("Which customers have declining success scores, and what events are driving the decline?", "GraphQuery"),
                ("How many customers have success scores below 60, and what is their combined ARR?", "GraphQuery"),
                ("What percentage of customers experienced negative events in the last 90 days?", "GraphQuery"),
                ("Which customers are at highest risk of churn based on success scores and recent events?", "GraphQuery"),
                
                # Customer Commitments & Satisfaction
                ("What are the top customer commitments, and what are the current risks to achieving them?", "GraphQuery"),
                ("Which features were promised to customers, and what is their delivery status?", "GraphQuery"),
                ("What are the top customer concerns, and what is currently being done to address them?", "VectorSearch"),
                ("How many customers are waiting for features currently on our roadmap?", "GraphQuery"),
                ("Which customers have unmet SLA commitments in the last quarter?", "GraphQuery"),
            ],
            
            "Product & Feature Management": [
                # Product Performance
                ("Which products have the highest customer satisfaction scores?", "GraphQuery"),
                ("What features drive the most value for our enterprise customers?", "VectorSearch"),
                ("How many customers use SpyroCloud, and what is the average subscription value?", "GraphQuery"),
                ("Which products have the most operational issues impacting customer success?", "GraphQuery"),
                ("What is the adoption rate of SpyroAI features released in the last 6 months?", "HybridSearch"),
                
                # Roadmap & Delivery Risk
                ("How much future revenue will be at risk if the AI enhancement project misses its deadline by 3 months?", "GraphQuery"),
                ("Which roadmap items are critical for customer retention?", "GraphQuery"),
                ("What percentage of roadmap items are currently behind schedule?", "GraphQuery"),
                ("Which teams are responsible for delayed roadmap items?", "GraphQuery"),
                ("How many customer commitments depend on roadmap items at risk?", "GraphQuery"),
            ],
            
            "Risk Management": [
                # Strategic Risk Assessment
                ("What are the top risks related to achieving our expansion objective?", "GraphQuery"),
                ("Which company objectives have the highest number of associated risks?", "GraphQuery"),
                ("What is the potential revenue impact of our top 5 identified risks?", "GraphQuery"),
                ("Which risks affect multiple objectives or customer segments?", "GraphQuery"),
                ("How many high-severity risks are currently without mitigation strategies?", "GraphQuery"),
                
                # Operational Risk
                ("Which teams are understaffed relative to their project commitments?", "GraphQuery"),
                ("What operational risks could impact product SLAs?", "GraphQuery"),
                ("Which products have the highest operational risk exposure?", "GraphQuery"),
                ("How do operational risks correlate with customer success scores?", "GraphQuery"),
                ("What percentage of projects are at risk of missing deadlines?", "GraphQuery"),
            ],
            
            "Team & Resource Management": [
                # Team Performance
                ("Which teams support the most revenue-generating products?", "GraphQuery"),
                ("What is the revenue-per-team-member for each department?", "GraphQuery"),
                ("Which teams are working on the most critical customer commitments?", "GraphQuery"),
                ("How are teams allocated across products and projects?", "GraphQuery"),
                ("Which teams have the highest impact on customer success scores?", "GraphQuery"),
                
                # Project Delivery
                ("Which projects are critical for maintaining current revenue?", "GraphQuery"),
                ("What percentage of projects are delivering on schedule?", "GraphQuery"),
                ("Which projects have dependencies that could impact multiple products?", "GraphQuery"),
                ("How many projects are blocked by operational constraints?", "GraphQuery"),
                ("What is the success rate of projects by team and product area?", "GraphQuery"),
            ],
            
            "Strategic Planning": [
                # Growth & Expansion
                ("Which customer segments offer the highest growth potential?", "GraphQuery"),
                ("What products have the best profitability-to-cost ratio for scaling?", "GraphQuery"),
                ("Which regions show the most promise for expansion based on current metrics?", "GraphQuery"),
                ("What features could we develop to increase customer success scores?", "VectorSearch"),
                ("Which objectives are most critical for achieving our growth targets?", "GraphQuery"),
                
                # Competitive Positioning
                ("How do SpyroCloud SLAs compare to industry standards?", "HybridSearch"),
                ("Which SpyroAI features give us competitive advantage in the enterprise market?", "HybridSearch"),
                ("What operational improvements would most impact customer satisfaction?", "VectorSearch"),
                ("How can we reduce operational costs while maintaining service quality?", "VectorSearch"),
                ("Which customer segments are we best positioned to serve profitably?", "GraphQuery"),
            ]
        }
    
    def extract_tool_used(self, query: str) -> str:
        """Extract which tool was used by running query with verbose output"""
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            self.agent.agent.verbose = True
            try:
                self.agent.query(query)
            except:
                pass
            self.agent.agent.verbose = False
        
        output = f.getvalue()
        
        if "Invoking: `GraphQuery`" in output:
            return "GraphQuery"
        elif "Invoking: `HybridSearch`" in output:
            return "HybridSearch"
        elif "Invoking: `VectorSearch`" in output:
            return "VectorSearch"
        return "Unknown"
    
    def test_category(self, category: str, questions: List[Tuple[str, str]]) -> Dict:
        """Test all questions in a category"""
        print(f"\n[Testing {category}]")
        print("-" * 60)
        
        category_results = {
            "total": len(questions),
            "correct_tool": 0,
            "successful": 0,
            "avg_time": 0,
            "times": [],
            "failures": []
        }
        
        for i, (question, expected_tool) in enumerate(questions, 1):
            print(f"\r  Question {i}/{len(questions)}: Testing...", end="", flush=True)
            
            start_time = time.time()
            
            try:
                # Test tool selection
                actual_tool = self.extract_tool_used(question)
                tool_correct = (actual_tool == expected_tool)
                
                # Test execution
                result = self.agent.query(question)
                elapsed = time.time() - start_time
                
                # Check answer quality
                answer = result.get('answer', '')
                is_successful = len(answer) > 50 and "error" not in answer.lower()
                
                if tool_correct:
                    category_results["correct_tool"] += 1
                if is_successful:
                    category_results["successful"] += 1
                
                category_results["times"].append(elapsed)
                
                self.results["tool_selection"].append({
                    "category": category,
                    "question": question,
                    "expected_tool": expected_tool,
                    "actual_tool": actual_tool,
                    "correct": tool_correct
                })
                
                self.results["performance"].append(elapsed)
                
                if not tool_correct or not is_successful:
                    category_results["failures"].append({
                        "question": question[:50] + "...",
                        "issue": f"Tool: {actual_tool} (expected {expected_tool})" if not tool_correct else "Poor answer quality"
                    })
                
            except Exception as e:
                self.results["errors"].append({
                    "category": category,
                    "question": question[:50] + "...",
                    "error": str(e)
                })
                category_results["failures"].append({
                    "question": question[:50] + "...",
                    "issue": f"Error: {str(e)[:50]}"
                })
            
            # Brief pause between questions
            if i % 5 == 0:
                time.sleep(1)
        
        category_results["avg_time"] = statistics.mean(category_results["times"]) if category_results["times"] else 0
        
        # Print category summary
        tool_accuracy = (category_results["correct_tool"] / category_results["total"]) * 100
        success_rate = (category_results["successful"] / category_results["total"]) * 100
        
        print(f"\r  ✓ Completed {category_results['total']} questions")
        print(f"    Tool Accuracy: {tool_accuracy:.1f}%")
        print(f"    Success Rate: {success_rate:.1f}%")
        print(f"    Avg Time: {category_results['avg_time']:.2f}s")
        
        return category_results
    
    def run_comprehensive_test(self):
        """Run the complete test suite"""
        print("\n" + "="*80)
        print("COMPREHENSIVE BUSINESS QUESTIONS TEST")
        print("Testing real-world executive queries across all business domains")
        print("="*80)
        
        questions_by_category = self.get_business_questions()
        total_questions = sum(len(q) for q in questions_by_category.values())
        
        print(f"\nTotal questions to test: {total_questions}")
        print(f"Categories: {len(questions_by_category)}")
        
        # Test each category
        for category, questions in questions_by_category.items():
            category_results = self.test_category(category, questions)
            self.results["by_category"][category] = category_results
        
        # Generate final report
        self.generate_report(total_questions)
    
    def generate_report(self, total_questions: int):
        """Generate comprehensive test report"""
        print("\n" + "="*80)
        print("FINAL REPORT")
        print("="*80)
        
        # Overall tool selection accuracy
        tool_correct = sum(1 for r in self.results["tool_selection"] if r["correct"])
        tool_accuracy = (tool_correct / len(self.results["tool_selection"])) * 100 if self.results["tool_selection"] else 0
        
        print(f"\n1. TOOL SELECTION ACCURACY: {tool_accuracy:.1f}%")
        print(f"   Correct: {tool_correct}/{len(self.results['tool_selection'])}")
        print(f"   Target: ≥95% - {'PASS' if tool_accuracy >= 95 else 'FAIL'}")
        
        # Performance metrics
        if self.results["performance"]:
            avg_time = statistics.mean(self.results["performance"])
            median_time = statistics.median(self.results["performance"])
            print(f"\n2. PERFORMANCE METRICS:")
            print(f"   Average Response Time: {avg_time:.2f}s")
            print(f"   Median Response Time: {median_time:.2f}s")
            print(f"   Min/Max: {min(self.results['performance']):.2f}s / {max(self.results['performance']):.2f}s")
        
        # Error rate
        error_rate = (len(self.results["errors"]) / total_questions) * 100
        print(f"\n3. RELIABILITY:")
        print(f"   Error Rate: {error_rate:.2f}%")
        print(f"   Errors: {len(self.results['errors'])}/{total_questions}")
        print(f"   Target: <0.1% - {'PASS' if error_rate < 0.1 else 'FAIL'}")
        
        # Category breakdown
        print(f"\n4. RESULTS BY CATEGORY:")
        print("-" * 60)
        for category, results in self.results["by_category"].items():
            tool_acc = (results["correct_tool"] / results["total"]) * 100
            success = (results["successful"] / results["total"]) * 100
            print(f"\n{category}:")
            print(f"  Questions: {results['total']}")
            print(f"  Tool Accuracy: {tool_acc:.1f}%")
            print(f"  Success Rate: {success:.1f}%")
            print(f"  Avg Time: {results['avg_time']:.2f}s")
            
            if results["failures"]:
                print(f"  Failures ({len(results['failures'])}):")
                for f in results["failures"][:3]:  # Show first 3 failures
                    print(f"    - {f['question']}: {f['issue']}")
        
        # Save detailed results
        report_data = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_questions": total_questions,
                "tool_accuracy": tool_accuracy,
                "avg_response_time": avg_time if self.results["performance"] else 0,
                "error_rate": error_rate,
                "categories_tested": len(self.results["by_category"])
            },
            "details": self.results
        }
        
        with open("business_questions_test_report.json", "w") as f:
            json.dump(report_data, f, indent=2)
        
        print(f"\n\nDetailed report saved to: business_questions_test_report.json")
        
        # Final verdict
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY")
        print("="*80)
        
        criteria_met = 0
        criteria_total = 3
        
        if tool_accuracy >= 95:
            criteria_met += 1
            print("✅ Tool Selection: EXCELLENT")
        else:
            print("❌ Tool Selection: Needs improvement")
            
        if error_rate < 0.1:
            criteria_met += 1
            print("✅ Reliability: EXCELLENT")
        else:
            print("❌ Reliability: Needs improvement")
            
        # Overall business readiness
        business_ready = tool_accuracy >= 90 and error_rate < 5
        if business_ready:
            criteria_met += 1
            print("✅ Business Readiness: READY")
        else:
            print("❌ Business Readiness: Not ready")
        
        print(f"\nOVERALL: {criteria_met}/{criteria_total} criteria met")
        print("="*80)
    
    def close(self):
        """Clean up resources"""
        self.agent.close()


def main():
    """Run the comprehensive business questions test"""
    try:
        print("SpyroSolutions Agentic RAG - Business Questions Test")
        print("This test validates the system with real executive queries")
        
        tester = BusinessQuestionsTester()
        tester.run_comprehensive_test()
        tester.close()
        
        print("\nTest completed successfully!")
        
    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()