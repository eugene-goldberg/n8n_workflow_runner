#!/bin/bash

# Quick API Test Script - Tests a subset of questions

# Configuration
API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "Quick API Test - SpyroSolutions Agentic RAG"
echo "=========================================="

# Test function
test_query() {
    local question="$1"
    echo -e "\n${BLUE}Testing:${NC} $question"
    
    # Send request
    response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "{\"question\": \"$question\"}" \
        -w "\nHTTP_CODE:%{http_code}")
    
    # Extract HTTP code
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    
    if [ "$http_code" = "200" ]; then
        # Extract answer (first 100 chars)
        answer=$(echo "$response" | sed 's/HTTP_CODE:.*//' | jq -r '.answer' 2>/dev/null | cut -c1-100)
        echo -e "${GREEN}✓ Success${NC} - Answer: $answer..."
    else
        echo -e "${RED}✗ Failed${NC} - HTTP $http_code"
    fi
    
    sleep 1
}

# Run quick tests
test_query "Which customers have subscriptions over \$5M?"
test_query "Tell me about SpyroAI capabilities"
test_query "What features does SpyroCloud include?"
test_query "What are the top risks for our objectives?"
test_query "Which teams support SpyroCloud?"

echo -e "\n${GREEN}Quick test completed!${NC}"