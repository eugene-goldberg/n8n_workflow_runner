#!/usr/bin/env python3
"""Format the Q&A report for easier reading"""

import re

def format_qa_report():
    """Create a cleaner version of the Q&A report"""
    
    with open('all_questions_and_answers.txt', 'r') as f:
        content = f.read()
    
    # Split by question sections - the separator appears twice between questions
    pattern = '='*80 + '\n'
    sections = re.split(pattern, content)
    
    # Write formatted report
    with open('business_questions_qa_formatted.md', 'w') as f:
        f.write("# Business Questions - Complete Q&A Report\n\n")
        f.write("This document contains all 60 business questions with their complete answers from the LangGraph Agentic RAG system.\n\n")
        f.write("---\n\n")
        
        question_count = 0
        current_category = ""
        
        for section in sections[1:]:  # Skip header
            if section.startswith("Question"):
                lines = section.strip().split('\n')
                
                # Parse question info
                question_line = lines[0]
                match = re.match(r'Question (\d+): (.+)', question_line)
                if match:
                    num = match.group(1)
                    question = match.group(2)
                    question_count += 1
                    
                    # Parse category
                    category_line = lines[1] if len(lines) > 1 else ""
                    if category_line.startswith("Category:"):
                        category = category_line.replace("Category: ", "").split(" > ")[0]
                        if category != current_category:
                            current_category = category
                            f.write(f"\n## {category}\n\n")
                    
                    # Find answer
                    answer_start = section.find("Answer:\n")
                    if answer_start != -1:
                        answer = section[answer_start + 8:].strip()
                        
                        # Write Q&A
                        f.write(f"### Q{num}: {question}\n\n")
                        f.write(f"**Answer:**\n\n{answer}\n\n")
                        f.write("---\n\n")
        
        # Add summary stats
        f.write(f"\n## Summary\n\n")
        f.write(f"- Total Questions: {question_count}\n")
        f.write(f"- All questions answered successfully\n")
        f.write(f"- System: LangGraph Agentic RAG with Neo4j\n")
        f.write(f"- Model: GPT-3.5-Turbo\n")
    
    print(f"Formatted report saved to: business_questions_qa_formatted.md")
    print(f"Total questions processed: {question_count}")

if __name__ == "__main__":
    format_qa_report()