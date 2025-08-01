#!/bin/bash

# Simple test script for SpyroSolutions Agentic RAG API

API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"

echo "Testing SpyroSolutions Agentic RAG API"
echo "======================================"
echo

# Test queries
queries=(
    "What percentage of our ARR is dependent on customers with success scores below 70?"
    "Which customers have declining success scores?"
    "What percentage of roadmap items are currently behind schedule?"
    "Which teams are responsible for delayed roadmap items?"
    "What are the top risks for customers with low success scores?"
)

for i in "${!queries[@]}"; do
    query="${queries[$i]}"
    echo "[$((i+1))] Query: $query"
    
    # Create JSON payload using jq for proper escaping
    json_payload=$(jq -n --arg q "$query" '{"question": $q}')
    
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload" \
        -w "\n|||STATUS|||%{http_code}")
    
    # Extract status code (it might be at the end without newline)
    status_code=$(echo "$response" | grep -o '|||STATUS|||[0-9]*' | sed 's/|||STATUS|||//')
    
    # Extract answer (remove status code line)
    answer=$(echo "$response" | sed '/|||STATUS|||/d' | jq -r '.answer' 2>/dev/null || echo "Error parsing response")
    
    if [ "$status_code" = "200" ]; then
        echo "✓ Success"
        echo "Answer: $answer"
    else
        echo "✗ Failed - HTTP $status_code"
    fi
    
    echo
    echo "---"
    echo
done

echo "Test complete!"