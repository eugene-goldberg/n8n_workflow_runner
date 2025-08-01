#!/bin/bash

# Test queries that were previously failing

API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"

echo "Testing Previously Failed Queries"
echo "================================="
echo

# Function to test a query
test_query() {
    local question="$1"
    local category="$2"
    
    echo "Testing: $question"
    echo "Category: $category"
    
    json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    response=$(curl -s -m 30 -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload" \
        -w "\n|||STATUS|||%{http_code}")
    
    status_code=$(echo "$response" | grep -o '|||STATUS|||[0-9]*' | sed 's/|||STATUS|||//')
    
    if [ "$status_code" = "200" ]; then
        answer=$(echo "$response" | sed '/|||STATUS|||/d' | jq -r '.answer' 2>/dev/null || echo "Error parsing response")
        
        if [[ "$answer" == *"no specific data"* ]] || [[ "$answer" == *"no available data"* ]]; then
            echo "❌ Result: No data found"
        else
            echo "✅ Result: Success"
            echo "Answer: ${answer:0:200}..."
        fi
    else
        echo "❌ Result: HTTP Error $status_code"
    fi
    echo
    echo "---"
    echo
}

# Test queries that were failing before
test_query "Which features were promised to customers, and what is their delivery status?" "Customer"
test_query "What are the top customer concerns, and what is currently being done to address them?" "Customer"
test_query "Which teams have the highest impact on customer success scores?" "Team"
test_query "What is the cost-per-customer for each product, and how does it vary by region?" "Revenue"
test_query "Which customers have unmet SLA commitments in the last quarter?" "Customer"
test_query "How do operational risks correlate with customer success scores?" "Risk"

echo "Test complete!"