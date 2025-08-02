#!/bin/bash

# Comprehensive Business Questions Test with Full Answer Capture
# This version saves complete answers to identify data gaps

API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"
OUTPUT_DIR="test_results/full_answers_$(date +%Y%m%d_%H%M%S)"
SUMMARY_FILE="$OUTPUT_DIR/summary.md"
GAPS_FILE="$OUTPUT_DIR/data_gaps.md"

# Create output directory
mkdir -p "$OUTPUT_DIR"

echo "SpyroSolutions Agentic RAG - Full Answer Analysis"
echo "================================================"
echo "Output directory: $OUTPUT_DIR"
echo

# Initialize counters
TOTAL_TESTS=0
SUCCESSFUL_TESTS=0
FAILED_TESTS=0
NO_DATA_TESTS=0
PARTIAL_TESTS=0

# Arrays to track data gaps
declare -a NO_DATA_QUESTIONS=()
declare -a PARTIAL_DATA_QUESTIONS=()
declare -a GENERIC_ANSWER_QUESTIONS=()

# Initialize summary file
cat > "$SUMMARY_FILE" << EOF
# SpyroSolutions Agentic RAG Test Results
Date: $(date)

## Summary
EOF

# Initialize gaps file
cat > "$GAPS_FILE" << EOF
# Identified Data Gaps
Date: $(date)

## Overview
This document identifies areas where data is missing or incomplete based on the test results.

EOF

# Function to test a query and save full answer
test_query() {
    local question="$1"
    local category="$2"
    
    ((TOTAL_TESTS++))
    echo "[$TOTAL_TESTS] $question"
    
    # Create JSON payload using jq for proper escaping
    json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    # Create individual output file
    output_file="$OUTPUT_DIR/q${TOTAL_TESTS}_${category}.json"
    
    # Send request and save full response
    response=$(curl -s -m 30 -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload")
    
    # Save full response
    echo "$response" > "$output_file"
    
    # Extract status and answer
    status_code=$(echo "$response" | jq -r '.metadata.agent_type' &>/dev/null && echo "200" || echo "error")
    answer=$(echo "$response" | jq -r '.answer' 2>/dev/null || echo "Error parsing response")
    
    # Analyze answer quality
    if [ "$status_code" != "200" ]; then
        echo "   ✗ Failed - HTTP Error"
        ((FAILED_TESTS++))
        status="FAILED"
    elif [[ "$answer" == *"Agent stopped"* ]] || [[ "$answer" == *"iteration limit"* ]]; then
        echo "   ⚠️  Partial - Agent hit limits"
        ((PARTIAL_TESTS++))
        PARTIAL_DATA_QUESTIONS+=("$question")
        status="PARTIAL"
    elif [[ "$answer" == *"no specific data"* ]] || [[ "$answer" == *"no available data"* ]] || [[ "$answer" == *"no direct data"* ]] || [[ "$answer" == *"seems there are no"* ]] || [[ "$answer" == *"couldn't find"* ]]; then
        echo "   ⚠️  No Data - Missing information"
        ((NO_DATA_TESTS++))
        NO_DATA_QUESTIONS+=("$question")
        status="NO_DATA"
    elif [[ "$answer" == *"typically"* ]] || [[ "$answer" == *"consider"* ]] || [[ "$answer" == *"strategies"* ]] && [[ ! "$answer" == *"$"* ]]; then
        echo "   ⚠️  Generic - No specific data"
        ((NO_DATA_TESTS++))
        GENERIC_ANSWER_QUESTIONS+=("$question")
        status="GENERIC"
    else
        echo "   ✓ Success"
        ((SUCCESSFUL_TESTS++))
        status="SUCCESS"
    fi
    
    # Write to summary
    echo -e "\n### Question $TOTAL_TESTS: $question" >> "$SUMMARY_FILE"
    echo "**Category:** $category | **Status:** $status" >> "$SUMMARY_FILE"
    echo -e "\n**Answer:**" >> "$SUMMARY_FILE"
    echo '```' >> "$SUMMARY_FILE"
    echo "$answer" >> "$SUMMARY_FILE"
    echo '```' >> "$SUMMARY_FILE"
    
    # Show first 200 chars of answer
    echo "   Answer preview: ${answer:0:200}..."
    echo
}

# Function to analyze gaps by category
analyze_gaps() {
    local category="$1"
    shift
    local questions=("$@")
    
    if [ ${#questions[@]} -gt 0 ]; then
        echo -e "\n### $category" >> "$GAPS_FILE"
        for q in "${questions[@]}"; do
            echo "- $q" >> "$GAPS_FILE"
        done
    fi
}

# Start testing
START_TIME=$(date +%s)

echo "=== REVENUE & FINANCIAL PERFORMANCE ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

echo "Revenue Risk Analysis:"
test_query "How much revenue will be at risk if TechCorp misses their SLA next month?" "Revenue"
test_query "What percentage of our ARR is dependent on customers with success scores below 70?" "Revenue"
test_query "Which customers generate 80% of our revenue, and what are their current risk profiles?" "Revenue"
test_query "How much revenue is at risk from customers experiencing negative events in the last quarter?" "Revenue"
test_query "What is the projected revenue impact if we miss our roadmap deadlines for committed features?" "Revenue"

echo -e "\nCost & Profitability:"
test_query "How much does it cost to run each product across all regions?" "Revenue"
test_query "What is the profitability margin for each product line?" "Revenue"
test_query "How do operational costs impact profitability for our top 10 customers?" "Revenue"
test_query "Which teams have the highest operational costs relative to the revenue they support?" "Revenue"
test_query "What is the cost-per-customer for each product, and how does it vary by region?" "Revenue"

echo -e "\n=== CUSTOMER SUCCESS & RETENTION ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

echo "Customer Health:"
test_query "What are the top 5 customers by revenue, and what are their current success scores?" "Customer"
test_query "Which customers have declining success scores, and what events are driving the decline?" "Customer"
test_query "How many customers have success scores below 60, and what is their combined ARR?" "Customer"
test_query "What percentage of customers experienced negative events in the last 90 days?" "Customer"
test_query "Which customers are at highest risk of churn based on success scores and recent events?" "Customer"

echo -e "\nCustomer Commitments & Satisfaction:"
test_query "What are the top customer commitments, and what are the current risks to achieving them?" "Customer"
test_query "Which features were promised to customers, and what is their delivery status?" "Customer"
test_query "What are the top customer concerns, and what is currently being done to address them?" "Customer"
test_query "How many customers are waiting for features currently on our roadmap?" "Customer"
test_query "Which customers have unmet SLA commitments in the last quarter?" "Customer"

echo -e "\n=== PRODUCT & FEATURE MANAGEMENT ===" | tee -a "$SUMMARY_FILE"
echo "----------------------------------------" | tee -a "$SUMMARY_FILE"

echo "Product Performance:"
test_query "Which products have the highest customer satisfaction scores?" "Product"
test_query "What features drive the most value for our enterprise customers?" "Product"
test_query "How many customers use each product, and what is the average subscription value?" "Product"
test_query "Which products have the most operational issues impacting customer success?" "Product"
test_query "What is the adoption rate of new features released in the last 6 months?" "Product"

echo -e "\nRoadmap & Delivery Risk:"
test_query "How much future revenue will be at risk if Multi-region deployment misses its deadline by 3 months?" "Product"
test_query "Which roadmap items are critical for customer retention?" "Product"
test_query "What percentage of roadmap items are currently behind schedule?" "Product"
test_query "Which teams are responsible for delayed roadmap items?" "Product"
test_query "How many customer commitments depend on roadmap items at risk?" "Product"

# Calculate results
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
SUCCESS_RATE=$(echo "scale=2; $SUCCESSFUL_TESTS * 100 / $TOTAL_TESTS" | bc)

# Write final summary
cat >> "$SUMMARY_FILE" << EOF

## Test Statistics
- **Total Questions:** $TOTAL_TESTS
- **Successful:** $SUCCESSFUL_TESTS
- **No Data:** $NO_DATA_TESTS
- **Partial Data:** $PARTIAL_TESTS
- **Failed:** $FAILED_TESTS
- **Success Rate:** ${SUCCESS_RATE}%
- **Duration:** ${DURATION} seconds
EOF

# Analyze data gaps
echo "## Detailed Gap Analysis" >> "$GAPS_FILE"

analyze_gaps "Questions with No Data" "${NO_DATA_QUESTIONS[@]}"
analyze_gaps "Questions with Partial Data" "${PARTIAL_DATA_QUESTIONS[@]}"
analyze_gaps "Questions with Generic Answers" "${GENERIC_ANSWER_QUESTIONS[@]}"

# Suggest data to create
cat >> "$GAPS_FILE" << EOF

## Recommended Data to Create

Based on the gaps identified, consider creating PDF reports with the following data:

### 1. Regional Cost Analysis Report
- Operational costs by product and region
- Cost-per-customer breakdowns
- Regional pricing strategies
- Infrastructure costs by geographic area

### 2. Team Performance & Resource Report
- Team operational costs vs revenue supported
- Staffing levels vs project commitments
- Team productivity metrics
- Resource allocation analysis

### 3. Customer Commitment Tracking Report
- Feature promises and delivery status
- Customer-specific commitments
- SLA performance history
- Commitment risk analysis

### 4. Product Operational Health Report
- Operational issues by product
- Impact on customer success
- Feature adoption metrics
- Product-specific SLA performance

### 5. Project Dependencies & Risk Report
- Project interdependencies
- Revenue impact analysis
- Deadline risk assessment
- Resource constraints

### 6. Feature Value Analysis Report
- Feature usage by customer segment
- Value metrics for enterprise features
- Adoption rates over time
- Feature ROI analysis
EOF

echo
echo "================================================================="
echo "TEST SUMMARY"
echo "================================================================="
echo "Total Questions Tested: $TOTAL_TESTS (first 30 of 60)"
echo "Successful: $SUCCESSFUL_TESTS"
echo "No Data: $NO_DATA_TESTS"
echo "Partial: $PARTIAL_TESTS"
echo "Failed: $FAILED_TESTS"
echo "Success Rate: ${SUCCESS_RATE}%"
echo
echo "Full results saved to: $OUTPUT_DIR"
echo "Summary report: $SUMMARY_FILE"
echo "Data gaps analysis: $GAPS_FILE"
echo
echo "Next steps:"
echo "1. Review $GAPS_FILE for missing data areas"
echo "2. Create PDF reports to fill the identified gaps"
echo "3. Ingest the PDFs using LlamaIndex pipeline"
echo "4. Re-run tests to verify improvements"