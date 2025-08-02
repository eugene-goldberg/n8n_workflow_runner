#!/usr/bin/env python3
"""
Analyze test results to identify data gaps and suggest PDF reports to create
"""

import json
import os
import sys
from datetime import datetime
from collections import defaultdict
import re

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents.spyro_agent_llamaindex import create_agent
from utils.config import Config


def analyze_answer(answer):
    """Analyze an answer to determine data quality"""
    if not answer:
        return "ERROR", "No answer provided"
    
    # Check for agent limits
    if "Agent stopped" in answer or "iteration limit" in answer:
        return "PARTIAL", "Agent hit processing limits"
    
    # Check for missing data indicators
    no_data_phrases = [
        "no specific data",
        "no available data", 
        "no direct data",
        "seems there are no",
        "seems there is no",
        "couldn't find",
        "no specific records",
        "no specific entries",
        "currently no",
        "there are no",
        "0% of",
        "0 entities"
    ]
    
    for phrase in no_data_phrases:
        if phrase in answer.lower():
            return "NO_DATA", f"Missing data: {phrase}"
    
    # Check for generic answers (no specific data)
    if ("typically" in answer or "consider" in answer or "strategies" in answer) and "$" not in answer and "%" not in answer:
        return "GENERIC", "Generic answer without specific data"
    
    # Check if answer has specific data
    has_numbers = bool(re.search(r'\$[\d,]+[MK]?|\d+%|\d+ (customers?|teams?|products?|projects?)', answer))
    has_names = bool(re.search(r'(TechCorp|CloudFirst|GlobalRetail|SpyroCloud|SpyroAI|SpyroSecure)', answer))
    
    if has_numbers or has_names:
        return "SUCCESS", "Contains specific data"
    
    return "GENERIC", "Answer lacks specific data"


def test_all_questions():
    """Test all 60 business questions and analyze results"""
    
    # Initialize agent
    config = Config()
    agent = create_agent(config)
    
    # Define all 60 questions
    questions = [
        # Revenue & Financial Performance
        ("How much revenue will be at risk if TechCorp misses their SLA next month?", "Revenue"),
        ("What percentage of our ARR is dependent on customers with success scores below 70?", "Revenue"),
        ("Which customers generate 80% of our revenue, and what are their current risk profiles?", "Revenue"),
        ("How much revenue is at risk from customers experiencing negative events in the last quarter?", "Revenue"),
        ("What is the projected revenue impact if we miss our roadmap deadlines for committed features?", "Revenue"),
        ("How much does it cost to run each product across all regions?", "Cost"),
        ("What is the profitability margin for each product line?", "Cost"),
        ("How do operational costs impact profitability for our top 10 customers?", "Cost"),
        ("Which teams have the highest operational costs relative to the revenue they support?", "Cost"),
        ("What is the cost-per-customer for each product, and how does it vary by region?", "Cost"),
        
        # Customer Success & Retention
        ("What are the top 5 customers by revenue, and what are their current success scores?", "Customer"),
        ("Which customers have declining success scores, and what events are driving the decline?", "Customer"),
        ("How many customers have success scores below 60, and what is their combined ARR?", "Customer"),
        ("What percentage of customers experienced negative events in the last 90 days?", "Customer"),
        ("Which customers are at highest risk of churn based on success scores and recent events?", "Customer"),
        ("What are the top customer commitments, and what are the current risks to achieving them?", "Commitment"),
        ("Which features were promised to customers, and what is their delivery status?", "Commitment"),
        ("What are the top customer concerns, and what is currently being done to address them?", "Commitment"),
        ("How many customers are waiting for features currently on our roadmap?", "Commitment"),
        ("Which customers have unmet SLA commitments in the last quarter?", "Commitment"),
        
        # Product & Feature Management
        ("Which products have the highest customer satisfaction scores?", "Product"),
        ("What features drive the most value for our enterprise customers?", "Product"),
        ("How many customers use each product, and what is the average subscription value?", "Product"),
        ("Which products have the most operational issues impacting customer success?", "Product"),
        ("What is the adoption rate of new features released in the last 6 months?", "Product"),
        ("How much future revenue will be at risk if Multi-region deployment misses its deadline by 3 months?", "Roadmap"),
        ("Which roadmap items are critical for customer retention?", "Roadmap"),
        ("What percentage of roadmap items are currently behind schedule?", "Roadmap"),
        ("Which teams are responsible for delayed roadmap items?", "Roadmap"),
        ("How many customer commitments depend on roadmap items at risk?", "Roadmap"),
        
        # Risk Management
        ("What are the top risks related to achieving Market Expansion objective?", "Risk"),
        ("Which company objectives have the highest number of associated risks?", "Risk"),
        ("What is the potential revenue impact of our top 5 identified risks?", "Risk"),
        ("Which risks affect multiple objectives or customer segments?", "Risk"),
        ("How many high-severity risks are currently without mitigation strategies?", "Risk"),
        ("Which teams are understaffed relative to their project commitments?", "Operational"),
        ("What operational risks could impact product SLAs?", "Operational"),
        ("Which products have the highest operational risk exposure?", "Operational"),
        ("How do operational risks correlate with customer success scores?", "Operational"),
        ("What percentage of projects are at risk of missing deadlines?", "Operational"),
        
        # Team & Resource Management
        ("Which teams support the most revenue-generating products?", "Team"),
        ("What is the revenue-per-team-member for each department?", "Team"),
        ("Which teams are working on the most critical customer commitments?", "Team"),
        ("How are teams allocated across products and projects?", "Team"),
        ("Which teams have the highest impact on customer success scores?", "Team"),
        ("Which projects are critical for maintaining current revenue?", "Project"),
        ("What percentage of projects are delivering on schedule?", "Project"),
        ("Which projects have dependencies that could impact multiple products?", "Project"),
        ("How many projects are blocked by operational constraints?", "Project"),
        ("What is the success rate of projects by team and product area?", "Project"),
        
        # Strategic Planning
        ("Which customer segments offer the highest growth potential?", "Strategic"),
        ("What products have the best profitability-to-cost ratio for scaling?", "Strategic"),
        ("Which regions show the most promise for expansion based on current metrics?", "Strategic"),
        ("What features could we develop to increase customer success scores?", "Strategic"),
        ("Which objectives are most critical for achieving our growth targets?", "Strategic"),
        ("How do our SLAs compare to industry standards by product?", "Competitive"),
        ("Which features give us competitive advantage in each market segment?", "Competitive"),
        ("What operational improvements would most impact customer satisfaction?", "Competitive"),
        ("How can we reduce operational costs while maintaining service quality?", "Competitive"),
        ("Which customer segments are we best positioned to serve profitably?", "Competitive"),
    ]
    
    # Test each question
    results = []
    gap_analysis = defaultdict(list)
    
    print("Analyzing all 60 business questions...")
    print("=" * 80)
    
    for i, (question, category) in enumerate(questions, 1):
        print(f"\n[{i}/60] Testing: {question}")
        
        try:
            # Query the agent
            result = agent.query(question)
            answer = result.get('answer', '')
            
            # Analyze the answer
            status, reason = analyze_answer(answer)
            
            # Store result
            results.append({
                'number': i,
                'question': question,
                'category': category,
                'status': status,
                'reason': reason,
                'answer': answer
            })
            
            # Track gaps
            if status in ['NO_DATA', 'GENERIC', 'PARTIAL']:
                gap_analysis[category].append({
                    'question': question,
                    'status': status,
                    'reason': reason
                })
            
            print(f"   Status: {status} - {reason}")
            
        except Exception as e:
            print(f"   ERROR: {str(e)}")
            results.append({
                'number': i,
                'question': question,
                'category': category,
                'status': 'ERROR',
                'reason': str(e),
                'answer': ''
            })
    
    # Generate report
    generate_gap_report(results, gap_analysis)
    
    # Close agent
    agent.close()


def generate_gap_report(results, gap_analysis):
    """Generate comprehensive gap analysis report"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_dir = f"test_results/gap_analysis_{timestamp}"
    os.makedirs(report_dir, exist_ok=True)
    
    # Save raw results
    with open(f"{report_dir}/raw_results.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate markdown report
    with open(f"{report_dir}/gap_analysis.md", 'w') as f:
        f.write("# SpyroSolutions Data Gap Analysis\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary statistics
        total = len(results)
        success = sum(1 for r in results if r['status'] == 'SUCCESS')
        no_data = sum(1 for r in results if r['status'] == 'NO_DATA')
        generic = sum(1 for r in results if r['status'] == 'GENERIC')
        partial = sum(1 for r in results if r['status'] == 'PARTIAL')
        errors = sum(1 for r in results if r['status'] == 'ERROR')
        
        f.write("## Summary Statistics\n\n")
        f.write(f"- Total Questions: {total}\n")
        f.write(f"- Successful (with specific data): {success} ({success/total*100:.1f}%)\n")
        f.write(f"- No Data Available: {no_data} ({no_data/total*100:.1f}%)\n")
        f.write(f"- Generic Answers: {generic} ({generic/total*100:.1f}%)\n")
        f.write(f"- Partial Data: {partial} ({partial/total*100:.1f}%)\n")
        f.write(f"- Errors: {errors} ({errors/total*100:.1f}%)\n\n")
        
        # Gaps by category
        f.write("## Data Gaps by Category\n\n")
        for category, gaps in sorted(gap_analysis.items()):
            f.write(f"### {category} ({len(gaps)} gaps)\n\n")
            for gap in gaps:
                f.write(f"- **{gap['question']}**\n")
                f.write(f"  - Status: {gap['status']}\n")
                f.write(f"  - Reason: {gap['reason']}\n\n")
        
        # Recommended PDF reports
        f.write("## Recommended PDF Reports to Create\n\n")
        
        recommendations = {
            "Cost": {
                "title": "Operational Cost Analysis Report",
                "content": [
                    "Product operational costs by region (SpyroCloud, SpyroAI, SpyroSecure)",
                    "Cost-per-customer breakdown with regional variations",
                    "Team operational costs vs revenue supported",
                    "Infrastructure and support costs by product line",
                    "Profitability margins for each product"
                ]
            },
            "Commitment": {
                "title": "Customer Commitments & Feature Promises Report",
                "content": [
                    "List of all feature promises to customers with delivery dates",
                    "Customer-specific commitments and their status",
                    "Top customer concerns and resolution plans",
                    "Features requested by customers on roadmap",
                    "SLA commitment history and violations"
                ]
            },
            "Product": {
                "title": "Product Health & Adoption Report",
                "content": [
                    "Customer satisfaction scores by product",
                    "Operational issues impacting each product",
                    "Feature adoption rates for last 6 months",
                    "Feature value metrics for enterprise customers",
                    "Product usage patterns and trends"
                ]
            },
            "Operational": {
                "title": "Operational Risk & Resource Report",
                "content": [
                    "Team staffing levels vs project commitments",
                    "Operational risks by product and severity",
                    "Correlation between operational issues and customer success",
                    "Project deadline risks and dependencies",
                    "Resource constraints and bottlenecks"
                ]
            },
            "Project": {
                "title": "Project Portfolio Status Report",
                "content": [
                    "Revenue criticality of each project",
                    "Project delivery status and success rates",
                    "Project dependencies and impact analysis",
                    "Operational constraints blocking projects",
                    "Team-wise project success metrics"
                ]
            },
            "Strategic": {
                "title": "Strategic Growth Analysis Report",
                "content": [
                    "Customer segment growth potential metrics",
                    "Product profitability-to-cost ratios",
                    "Regional expansion opportunities with data",
                    "Critical objectives for growth targets",
                    "Competitive positioning by market segment"
                ]
            }
        }
        
        for category, gaps in gap_analysis.items():
            if category in recommendations:
                rec = recommendations[category]
                f.write(f"### {rec['title']}\n\n")
                f.write("**Purpose:** Fill data gaps in " + category.lower() + " questions\n\n")
                f.write("**Recommended Content:**\n")
                for content in rec['content']:
                    f.write(f"- {content}\n")
                f.write("\n")
        
        # Specific missing entities
        f.write("## Specific Missing Data Points\n\n")
        f.write("Based on the analysis, create data for:\n\n")
        f.write("- Regional cost multipliers and base costs\n")
        f.write("- Team operational cost figures\n")
        f.write("- Product profitability margins\n")
        f.write("- Feature adoption metrics with dates\n")
        f.write("- Customer commitment tracking\n")
        f.write("- Project success rates by team\n")
        f.write("- Operational risk assessments\n")
        f.write("- Industry benchmark comparisons\n")
    
    print(f"\n\nGap analysis complete!")
    print(f"Results saved to: {report_dir}")
    print(f"- Raw results: {report_dir}/raw_results.json")
    print(f"- Gap analysis: {report_dir}/gap_analysis.md")


if __name__ == "__main__":
    test_all_questions()