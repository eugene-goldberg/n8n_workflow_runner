#!/bin/bash

# Sample Business Questions Test - One from each category

API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"

echo "SpyroSolutions Agentic RAG - Sample Business Questions Test"
echo "=========================================================="
echo "Testing 6 representative queries (one from each category)"
echo

# Initialize counters
TOTAL_TESTS=0
SUCCESSFUL_TESTS=0

# Function to test a query
test_query() {
    local question="$1"
    local category="$2"
    
    ((TOTAL_TESTS++))
    echo "[$TOTAL_TESTS] $category: $question"
    
    # Create JSON payload
    json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    # Send request
    START=$(date +%s)
    response=$(curl -s -m 30 -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload" \
        -w "\n|||STATUS|||%{http_code}")
    END=$(date +%s)
    DURATION=$((END - START))
    
    # Extract status code
    status_code=$(echo "$response" | grep -o '|||STATUS|||[0-9]*' | sed 's/|||STATUS|||//')
    
    if [ "$status_code" = "200" ]; then
        # Extract answer
        answer=$(echo "$response" | sed '/|||STATUS|||/d' | jq -r '.answer' 2>/dev/null || echo "Error parsing response")
        
        # Check answer quality
        if [[ "$answer" == *"Agent stopped"* ]] || [[ "$answer" == *"iteration limit"* ]]; then
            echo "   ⚠️  Partial Success (agent hit limits) - ${DURATION}s"
        elif [[ "$answer" == *"no specific data"* ]] || [[ "$answer" == *"no available data"* ]]; then
            echo "   ⚠️  No Data Available - ${DURATION}s"
        else
            echo "   ✓ Success - ${DURATION}s"
            ((SUCCESSFUL_TESTS++))
        fi
        # Show answer
        echo "   Answer: ${answer:0:150}..."
    else
        echo "   ✗ Failed - HTTP $status_code"
    fi
    echo
}

# Test one question from each category
echo "Testing one representative question from each business category..."
echo

test_query "What percentage of our ARR is dependent on customers with success scores below 70?" "Revenue"
test_query "Which customers have declining success scores, and what events are driving the decline?" "Customer"
test_query "What percentage of roadmap items are currently behind schedule?" "Product"
test_query "What are the top risks related to achieving Market Expansion objective?" "Risk"
test_query "Which teams support the most revenue-generating products?" "Team"
test_query "Which customer segments offer the highest growth potential?" "Strategic"

# Summary
echo "=========================================================="
echo "SUMMARY: $SUCCESSFUL_TESTS out of $TOTAL_TESTS queries returned useful answers"
echo

if [ $SUCCESSFUL_TESTS -ge 3 ]; then
    echo "✅ System is providing business value"
else
    echo "⚠️  System needs improvement"
fi