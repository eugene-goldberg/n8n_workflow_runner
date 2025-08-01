#!/bin/bash

# SpyroSolutions Agentic RAG API Test Script
# This script submits business questions to the API using curl

# Configuration
API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"
OUTPUT_DIR="test_results"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Counter for test results
TOTAL_TESTS=0
SUCCESSFUL_TESTS=0
FAILED_TESTS=0

# Function to send query and save response
send_query() {
    local question="$1"
    local category="$2"
    local test_num="$3"
    
    echo -e "\n${BLUE}[$test_num] Testing:${NC} $question"
    echo -e "${BLUE}Category:${NC} $category"
    
    # Create JSON payload
    local json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    # Send request and capture response
    local response_file="$OUTPUT_DIR/test_${test_num}_response.json"
    local start_time=$(date +%s)
    
    # Send request and capture both response and HTTP code
    local http_response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload" \
        -w "\n|||HTTP_CODE|||%{http_code}" \
        -o "$response_file")
    
    local http_code=$(echo "$http_response" | grep -o "|||HTTP_CODE|||[0-9]*" | sed 's/|||HTTP_CODE|||//')
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Check if request was successful
    if [ "$http_code" = "200" ]; then
        # Extract execution time and tokens from response
        local exec_time=$(jq -r '.metadata.execution_time_seconds' "$response_file" 2>/dev/null || echo "N/A")
        local tokens=$(jq -r '.metadata.tokens_used' "$response_file" 2>/dev/null || echo "N/A")
        
        echo -e "${GREEN}✓ Success${NC} - HTTP $http_code - Time: ${exec_time}s - Tokens: $tokens"
        ((SUCCESSFUL_TESTS++))
    else
        echo -e "${RED}✗ Failed${NC} - HTTP $http_code"
        ((FAILED_TESTS++))
    fi
    
    ((TOTAL_TESTS++))
    
    # Brief pause between requests
    sleep 2
}

# Main test execution
echo "=========================================="
echo "SpyroSolutions Agentic RAG API Test Suite"
echo "=========================================="
echo "API URL: $API_URL"
echo "Starting tests at: $(date)"
echo

# Revenue & Financial Performance Questions
echo -e "\n${BLUE}=== Revenue & Financial Performance ===${NC}"
send_query "How much revenue will be at risk if TechCorp misses their SLA next month?" "Revenue" 1
send_query "What percentage of our ARR is dependent on customers with success scores below 70?" "Revenue" 2
send_query "Which customers generate 80% of our revenue, and what are their current risk profiles?" "Revenue" 3
send_query "How much revenue is at risk from customers experiencing negative events in the last quarter?" "Revenue" 4
send_query "What is the projected revenue impact if we miss our roadmap deadlines for committed features?" "Revenue" 5
send_query "How much does it cost to run SpyroCloud across all regions?" "Revenue" 6
send_query "What is the profitability margin for each product line?" "Revenue" 7
send_query "How do operational costs impact profitability for our top 10 customers?" "Revenue" 8
send_query "Which teams have the highest operational costs relative to the revenue they support?" "Revenue" 9
send_query "What is the cost-per-customer for SpyroAI?" "Revenue" 10

# Customer Success & Retention Questions
echo -e "\n${BLUE}=== Customer Success & Retention ===${NC}"
send_query "What are the top 5 customers by revenue, and what are their current success scores?" "Customer" 11
send_query "Which customers have declining success scores, and what events are driving the decline?" "Customer" 12
send_query "How many customers have success scores below 60, and what is their combined ARR?" "Customer" 13
send_query "What percentage of customers experienced negative events in the last 90 days?" "Customer" 14
send_query "Which customers are at highest risk of churn based on success scores and recent events?" "Customer" 15
send_query "What are the top customer commitments, and what are the current risks to achieving them?" "Customer" 16
send_query "Which features were promised to customers, and what is their delivery status?" "Customer" 17
send_query "What are the top customer concerns, and what is currently being done to address them?" "Customer" 18
send_query "How many customers are waiting for features currently on our roadmap?" "Customer" 19
send_query "Which customers have unmet SLA commitments in the last quarter?" "Customer" 20

# Product & Feature Management Questions
echo -e "\n${BLUE}=== Product & Feature Management ===${NC}"
send_query "Which products have the highest customer satisfaction scores?" "Product" 21
send_query "What features drive the most value for our enterprise customers?" "Product" 22
send_query "How many customers use SpyroCloud, and what is the average subscription value?" "Product" 23
send_query "Which products have the most operational issues impacting customer success?" "Product" 24
send_query "What is the adoption rate of SpyroAI features released in the last 6 months?" "Product" 25
send_query "How much future revenue will be at risk if the AI enhancement project misses its deadline by 3 months?" "Product" 26
send_query "Which roadmap items are critical for customer retention?" "Product" 27
send_query "What percentage of roadmap items are currently behind schedule?" "Product" 28
send_query "Which teams are responsible for delayed roadmap items?" "Product" 29
send_query "How many customer commitments depend on roadmap items at risk?" "Product" 30

# Risk Management Questions
echo -e "\n${BLUE}=== Risk Management ===${NC}"
send_query "What are the top risks related to achieving our expansion objective?" "Risk" 31
send_query "Which company objectives have the highest number of associated risks?" "Risk" 32
send_query "What is the potential revenue impact of our top 5 identified risks?" "Risk" 33
send_query "Which risks affect multiple objectives or customer segments?" "Risk" 34
send_query "How many high-severity risks are currently without mitigation strategies?" "Risk" 35
send_query "Which teams are understaffed relative to their project commitments?" "Risk" 36
send_query "What operational risks could impact product SLAs?" "Risk" 37
send_query "Which products have the highest operational risk exposure?" "Risk" 38
send_query "How do operational risks correlate with customer success scores?" "Risk" 39
send_query "What percentage of projects are at risk of missing deadlines?" "Risk" 40

# Team & Resource Management Questions
echo -e "\n${BLUE}=== Team & Resource Management ===${NC}"
send_query "Which teams support the most revenue-generating products?" "Team" 41
send_query "What is the revenue-per-team-member for each department?" "Team" 42
send_query "Which teams are working on the most critical customer commitments?" "Team" 43
send_query "How are teams allocated across products and projects?" "Team" 44
send_query "Which teams have the highest impact on customer success scores?" "Team" 45
send_query "Which projects are critical for maintaining current revenue?" "Team" 46
send_query "What percentage of projects are delivering on schedule?" "Team" 47
send_query "Which projects have dependencies that could impact multiple products?" "Team" 48
send_query "How many projects are blocked by operational constraints?" "Team" 49
send_query "What is the success rate of projects by team and product area?" "Team" 50

# Strategic Planning Questions
echo -e "\n${BLUE}=== Strategic Planning ===${NC}"
send_query "Which customer segments offer the highest growth potential?" "Strategy" 51
send_query "What products have the best profitability-to-cost ratio for scaling?" "Strategy" 52
send_query "Which regions show the most promise for expansion based on current metrics?" "Strategy" 53
send_query "What features could we develop to increase customer success scores?" "Strategy" 54
send_query "Which objectives are most critical for achieving our growth targets?" "Strategy" 55
send_query "How do SpyroCloud SLAs compare to industry standards?" "Strategy" 56
send_query "Which SpyroAI features give us competitive advantage in the enterprise market?" "Strategy" 57
send_query "What operational improvements would most impact customer satisfaction?" "Strategy" 58
send_query "How can we reduce operational costs while maintaining service quality?" "Strategy" 59
send_query "Which customer segments are we best positioned to serve profitably?" "Strategy" 60

# Summary Report
echo -e "\n${BLUE}=========================================="
echo "Test Summary"
echo "==========================================${NC}"
echo "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Successful: $SUCCESSFUL_TESTS${NC}"
echo -e "${RED}Failed: $FAILED_TESTS${NC}"
echo "Success Rate: $(( SUCCESSFUL_TESTS * 100 / TOTAL_TESTS ))%"
echo "Completed at: $(date)"
echo
echo "Results saved in: $OUTPUT_DIR/"

# Create summary report
summary_file="$OUTPUT_DIR/test_summary.json"
jq -n \
    --arg total "$TOTAL_TESTS" \
    --arg success "$SUCCESSFUL_TESTS" \
    --arg failed "$FAILED_TESTS" \
    --arg timestamp "$(date -Iseconds)" \
    '{
        total_tests: $total,
        successful_tests: $success,
        failed_tests: $failed,
        success_rate: (($success | tonumber) / ($total | tonumber) * 100),
        timestamp: $timestamp
    }' > "$summary_file"

echo "Summary report saved to: $summary_file"