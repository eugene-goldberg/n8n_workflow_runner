#!/bin/bash

# Test queries for newly-added SpyroSolutions entities and relationships

API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"

echo "Testing Newly-Added SpyroSolutions Entities and Relationships"
echo "============================================================="
echo

# Function to test a query
test_query() {
    local question="$1"
    local description="$2"
    
    echo "Testing: $description"
    echo "Query: $question"
    
    # Create JSON payload
    json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    # Send request
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload")
    
    # Extract and display answer
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null || echo "Error parsing response")
    echo "Answer: $answer"
    echo
    echo "---"
    echo
}

# Test 1: New Customers
test_query \
    "Who are InnovateTech Solutions and Global Manufacturing Corp, and what products are they using?" \
    "New Customer Information"

# Test 2: Team Projects
test_query \
    "What is the Cloud Platform Team working on, and what is their current capacity utilization?" \
    "Team and Project Relationships"

# Test 3: Project Titan
test_query \
    "What is Project Titan, what team is working on it, and what is the investment amount?" \
    "Strategic Project Details"

# Test 4: Critical Risks
test_query \
    "What are the customer concentration risks, and which customers represent the highest revenue exposure?" \
    "Risk Analysis"

# Test 5: Competitor Threats
test_query \
    "Who is NeuralStack AI and what competitive threats do they pose to SpyroSolutions?" \
    "Competitive Intelligence"

# Test 6: Financial Performance
test_query \
    "What was SpyroCloud's Q1 2025 revenue and what is its profitability margin?" \
    "Product Financial Metrics"

# Test 7: At-Risk Customers
test_query \
    "Which customers are experiencing performance issues and are evaluating competitors?" \
    "Customer Health and Retention"

# Test 8: Innovation Lab
test_query \
    "What is the Innovation Lab team working on and what is their budget?" \
    "New Team Initiatives"

# Test 9: Multi-Region Deployment
test_query \
    "What is the status of the multi-region deployment project and which customers are affected?" \
    "Critical Project Status"

# Test 10: Regulatory Risks
test_query \
    "What regulatory compliance requirements are affecting SpyroAI, and what are the deadlines?" \
    "Compliance and Regulatory"

echo "Test complete!"