#!/bin/bash

# Comprehensive Business Questions Test for SpyroSolutions Agentic RAG API
# This version saves complete questions and answers to a file

API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"

# Create results directory with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="test_results/business_questions_${TIMESTAMP}"
mkdir -p "$RESULTS_DIR"

# Output files
SUMMARY_FILE="$RESULTS_DIR/summary.txt"
DETAILS_FILE="$RESULTS_DIR/detailed_results.json"
FULL_RESPONSES_FILE="$RESULTS_DIR/full_responses.txt"

echo "SpyroSolutions Agentic RAG - Comprehensive Business Questions Test" | tee "$SUMMARY_FILE"
echo "=================================================================" | tee -a "$SUMMARY_FILE"
echo "Testing 60 real-world executive queries across 6 business domains" | tee -a "$SUMMARY_FILE"
echo "Results saved to: $RESULTS_DIR" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

# Initialize counters
TOTAL_TESTS=0
SUCCESSFUL_TESTS=0
FAILED_TESTS=0

# Initialize JSON array for detailed results
echo "[" > "$DETAILS_FILE"

# Function to test a query
test_query() {
    local question="$1"
    local category="$2"
    
    ((TOTAL_TESTS++))
    echo "[$TOTAL_TESTS] $question" | tee -a "$SUMMARY_FILE"
    
    # Log to full responses file
    echo "===========================================" >> "$FULL_RESPONSES_FILE"
    echo "Question #$TOTAL_TESTS - Category: $category" >> "$FULL_RESPONSES_FILE"
    echo "===========================================" >> "$FULL_RESPONSES_FILE"
    echo "QUESTION: $question" >> "$FULL_RESPONSES_FILE"
    echo "" >> "$FULL_RESPONSES_FILE"
    
    # Create JSON payload using jq for proper escaping
    json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    # Send request and save full response
    response_file="$RESULTS_DIR/response_${TOTAL_TESTS}.json"
    response=$(curl -s -m 30 -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload" \
        -w "\n|||STATUS|||%{http_code}" \
        -o "$response_file")
    
    # Extract status code
    status_code=$(echo "$response" | grep -o '|||STATUS|||[0-9]*' | sed 's/|||STATUS|||//')
    
    # Add comma separator for JSON (except for first entry)
    if [ $TOTAL_TESTS -gt 1 ]; then
        echo "," >> "$DETAILS_FILE"
    fi
    
    if [ "$status_code" = "200" ]; then
        # Extract full answer and metadata
        answer=$(jq -r '.answer' "$response_file" 2>/dev/null || echo "Error parsing response")
        exec_time=$(jq -r '.metadata.execution_time_seconds' "$response_file" 2>/dev/null || echo "N/A")
        tokens=$(jq -r '.metadata.tokens_used' "$response_file" 2>/dev/null || echo "N/A")
        model=$(jq -r '.metadata.model' "$response_file" 2>/dev/null || echo "N/A")
        
        # Save full answer to responses file
        echo "ANSWER:" >> "$FULL_RESPONSES_FILE"
        echo "$answer" >> "$FULL_RESPONSES_FILE"
        echo "" >> "$FULL_RESPONSES_FILE"
        echo "METADATA:" >> "$FULL_RESPONSES_FILE"
        echo "- Execution Time: ${exec_time}s" >> "$FULL_RESPONSES_FILE"
        echo "- Tokens Used: $tokens" >> "$FULL_RESPONSES_FILE"
        echo "- Model: $model" >> "$FULL_RESPONSES_FILE"
        echo "" >> "$FULL_RESPONSES_FILE"
        
        # Check if answer is meaningful
        if [[ "$answer" == *"Agent stopped"* ]] || [[ "$answer" == *"iteration limit"* ]]; then
            echo "   ⚠️  Partial - Agent hit limits" | tee -a "$SUMMARY_FILE"
            ((FAILED_TESTS++))
            success_status="partial"
        elif [[ "$answer" == *"no specific data"* ]] || [[ "$answer" == *"no available data"* ]]; then
            echo "   ⚠️  No Data - Missing information" | tee -a "$SUMMARY_FILE"
            ((FAILED_TESTS++))
            success_status="no_data"
        else
            echo "   ✓ Success" | tee -a "$SUMMARY_FILE"
            ((SUCCESSFUL_TESTS++))
            success_status="success"
            # Show first 100 chars in terminal
            echo "   Answer: ${answer:0:100}..." | tee -a "$SUMMARY_FILE"
        fi
        
        # Save to JSON details
        jq -n \
            --arg num "$TOTAL_TESTS" \
            --arg cat "$category" \
            --arg q "$question" \
            --arg a "$answer" \
            --arg status "$success_status" \
            --arg time "$exec_time" \
            --arg tokens "$tokens" \
            --arg model "$model" \
            '{
                test_number: $num,
                category: $cat,
                question: $q,
                answer: $a,
                status: $status,
                execution_time: $time,
                tokens_used: $tokens,
                model: $model
            }' >> "$DETAILS_FILE"
    else
        echo "   ✗ Failed - HTTP $status_code" | tee -a "$SUMMARY_FILE"
        ((FAILED_TESTS++))
        
        # Log error to full responses
        echo "ERROR: HTTP $status_code" >> "$FULL_RESPONSES_FILE"
        if [ -f "$response_file" ]; then
            cat "$response_file" >> "$FULL_RESPONSES_FILE"
        fi
        echo "" >> "$FULL_RESPONSES_FILE"
        
        # Save error to JSON
        jq -n \
            --arg num "$TOTAL_TESTS" \
            --arg cat "$category" \
            --arg q "$question" \
            --arg status "error" \
            --arg code "$status_code" \
            '{
                test_number: $num,
                category: $cat,
                question: $q,
                status: $status,
                http_code: $code
            }' >> "$DETAILS_FILE"
    fi
    echo "" | tee -a "$SUMMARY_FILE"
}

# Start testing
START_TIME=$(date +%s)

echo "=== REVENUE & FINANCIAL PERFORMANCE ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "Revenue Risk Analysis:" | tee -a "$SUMMARY_FILE"
test_query "How much revenue will be at risk if TechCorp misses their SLA next month?" "Revenue"
test_query "What percentage of our ARR is dependent on customers with success scores below 70?" "Revenue"
test_query "Which customers generate 80% of our revenue, and what are their current risk profiles?" "Revenue"
test_query "How much revenue is at risk from customers experiencing negative events in the last quarter?" "Revenue"
test_query "What is the projected revenue impact if we miss our roadmap deadlines for committed features?" "Revenue"

echo -e "\nCost & Profitability:" | tee -a "$SUMMARY_FILE"
test_query "How much does it cost to run each product across all regions?" "Revenue"
test_query "What is the profitability margin for each product line?" "Revenue"
test_query "How do operational costs impact profitability for our top 10 customers?" "Revenue"
test_query "Which teams have the highest operational costs relative to the revenue they support?" "Revenue"
test_query "What is the cost-per-customer for each product, and how does it vary by region?" "Revenue"

echo -e "\n=== CUSTOMER SUCCESS & RETENTION ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "Customer Health:" | tee -a "$SUMMARY_FILE"
test_query "What are the top 5 customers by revenue, and what are their current success scores?" "Customer"
test_query "Which customers have declining success scores, and what events are driving the decline?" "Customer"
test_query "How many customers have success scores below 60, and what is their combined ARR?" "Customer"
test_query "What percentage of customers experienced negative events in the last 90 days?" "Customer"
test_query "Which customers are at highest risk of churn based on success scores and recent events?" "Customer"

echo -e "\nCustomer Commitments & Satisfaction:" | tee -a "$SUMMARY_FILE"
test_query "What are the top customer commitments, and what are the current risks to achieving them?" "Customer"
test_query "Which features were promised to customers, and what is their delivery status?" "Customer"
test_query "What are the top customer concerns, and what is currently being done to address them?" "Customer"
test_query "How many customers are waiting for features currently on our roadmap?" "Customer"
test_query "Which customers have unmet SLA commitments in the last quarter?" "Customer"

echo -e "\n=== PRODUCT & FEATURE MANAGEMENT ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "Product Performance:" | tee -a "$SUMMARY_FILE"
test_query "Which products have the highest customer satisfaction scores?" "Product"
test_query "What features drive the most value for our enterprise customers?" "Product"
test_query "How many customers use each product, and what is the average subscription value?" "Product"
test_query "Which products have the most operational issues impacting customer success?" "Product"
test_query "What is the adoption rate of new features released in the last 6 months?" "Product"

echo -e "\nRoadmap & Delivery Risk:" | tee -a "$SUMMARY_FILE"
test_query "How much future revenue will be at risk if Multi-region deployment misses its deadline by 3 months?" "Product"
test_query "Which roadmap items are critical for customer retention?" "Product"
test_query "What percentage of roadmap items are currently behind schedule?" "Product"
test_query "Which teams are responsible for delayed roadmap items?" "Product"
test_query "How many customer commitments depend on roadmap items at risk?" "Product"

echo -e "\n=== RISK MANAGEMENT ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "Strategic Risk Assessment:" | tee -a "$SUMMARY_FILE"
test_query "What are the top risks related to achieving Market Expansion objective?" "Risk"
test_query "Which company objectives have the highest number of associated risks?" "Risk"
test_query "What is the potential revenue impact of our top 5 identified risks?" "Risk"
test_query "Which risks affect multiple objectives or customer segments?" "Risk"
test_query "How many high-severity risks are currently without mitigation strategies?" "Risk"

echo -e "\nOperational Risk:" | tee -a "$SUMMARY_FILE"
test_query "Which teams are understaffed relative to their project commitments?" "Risk"
test_query "What operational risks could impact product SLAs?" "Risk"
test_query "Which products have the highest operational risk exposure?" "Risk"
test_query "How do operational risks correlate with customer success scores?" "Risk"
test_query "What percentage of projects are at risk of missing deadlines?" "Risk"

echo -e "\n=== TEAM & RESOURCE MANAGEMENT ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "Team Performance:" | tee -a "$SUMMARY_FILE"
test_query "Which teams support the most revenue-generating products?" "Team"
test_query "What is the revenue-per-team-member for each department?" "Team"
test_query "Which teams are working on the most critical customer commitments?" "Team"
test_query "How are teams allocated across products and projects?" "Team"
test_query "Which teams have the highest impact on customer success scores?" "Team"

echo -e "\nProject Delivery:" | tee -a "$SUMMARY_FILE"
test_query "Which projects are critical for maintaining current revenue?" "Team"
test_query "What percentage of projects are delivering on schedule?" "Team"
test_query "Which projects have dependencies that could impact multiple products?" "Team"
test_query "How many projects are blocked by operational constraints?" "Team"
test_query "What is the success rate of projects by team and product area?" "Team"

echo -e "\n=== STRATEGIC PLANNING ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"
echo "Growth & Expansion:" | tee -a "$SUMMARY_FILE"
test_query "Which customer segments offer the highest growth potential?" "Strategic"
test_query "What products have the best profitability-to-cost ratio for scaling?" "Strategic"
test_query "Which regions show the most promise for expansion based on current metrics?" "Strategic"
test_query "What features could we develop to increase customer success scores?" "Strategic"
test_query "Which objectives are most critical for achieving our growth targets?" "Strategic"

echo -e "\nCompetitive Positioning:" | tee -a "$SUMMARY_FILE"
test_query "How do our SLAs compare to industry standards by product?" "Strategic"
test_query "Which features give us competitive advantage in each market segment?" "Strategic"
test_query "What operational improvements would most impact customer satisfaction?" "Strategic"
test_query "How can we reduce operational costs while maintaining service quality?" "Strategic"
test_query "Which customer segments are we best positioned to serve profitably?" "Strategic"

# Close JSON array
echo "]" >> "$DETAILS_FILE"

# Calculate results
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
SUCCESS_RATE=$(echo "scale=2; $SUCCESSFUL_TESTS * 100 / $TOTAL_TESTS" | bc)

echo -e "\n=================================================================" | tee -a "$SUMMARY_FILE"
echo "TEST SUMMARY" | tee -a "$SUMMARY_FILE"
echo "=================================================================" | tee -a "$SUMMARY_FILE"
echo "Total Questions Tested: $TOTAL_TESTS" | tee -a "$SUMMARY_FILE"
echo "Successful: $SUCCESSFUL_TESTS" | tee -a "$SUMMARY_FILE"
echo "Failed: $FAILED_TESTS" | tee -a "$SUMMARY_FILE"
echo "Success Rate: ${SUCCESS_RATE}%" | tee -a "$SUMMARY_FILE"
echo "Total Duration: ${DURATION} seconds" | tee -a "$SUMMARY_FILE"
echo "" | tee -a "$SUMMARY_FILE"

if (( $(echo "$SUCCESS_RATE >= 60" | bc -l) )); then
    echo "✅ TEST PASSED - System is providing useful business insights" | tee -a "$SUMMARY_FILE"
else
    echo "❌ TEST FAILED - System needs improvement" | tee -a "$SUMMARY_FILE"
fi

# Save final summary
FINAL_SUMMARY_FILE="$RESULTS_DIR/final_summary.json"
echo "{
  \"test_date\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\",
  \"total_tests\": $TOTAL_TESTS,
  \"successful\": $SUCCESSFUL_TESTS,
  \"failed\": $FAILED_TESTS,
  \"success_rate\": $SUCCESS_RATE,
  \"duration_seconds\": $DURATION,
  \"results_directory\": \"$RESULTS_DIR\"
}" > "$FINAL_SUMMARY_FILE"

echo "" | tee -a "$SUMMARY_FILE"
echo "Results saved to:" | tee -a "$SUMMARY_FILE"
echo "  Summary: $SUMMARY_FILE" | tee -a "$SUMMARY_FILE"
echo "  Full Q&A: $FULL_RESPONSES_FILE" | tee -a "$SUMMARY_FILE"
echo "  JSON Details: $DETAILS_FILE" | tee -a "$SUMMARY_FILE"
echo "  Individual Responses: $RESULTS_DIR/response_*.json" | tee -a "$SUMMARY_FILE"