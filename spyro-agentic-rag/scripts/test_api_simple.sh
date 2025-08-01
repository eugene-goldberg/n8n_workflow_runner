#!/bin/bash

# Simple API Test Script
# Tests API connectivity and basic functionality

# Configuration
API_URL="http://localhost:8000"
API_KEY="spyro-secret-key-123"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "SpyroSolutions Agentic RAG - Simple API Test"
echo "==========================================="
echo

# Test 1: Health Check
echo -e "${BLUE}1. Testing Health Check...${NC}"
health_response=$(curl -s "$API_URL/health")
health_status=$(echo "$health_response" | jq -r '.status' 2>/dev/null)

if [ "$health_status" = "healthy" ]; then
    echo -e "${GREEN}✓ API is healthy${NC}"
    echo "   Agent ready: $(echo "$health_response" | jq -r '.agent_ready')"
else
    echo -e "${RED}✗ API health check failed${NC}"
    exit 1
fi

echo

# Test 2: Basic Query
echo -e "${BLUE}2. Testing Basic Query...${NC}"
query_response=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"question": "List all customers"}')

if [ $? -eq 0 ] && [ ! -z "$query_response" ]; then
    answer=$(echo "$query_response" | jq -r '.answer' 2>/dev/null | head -c 100)
    if [ ! -z "$answer" ] && [ "$answer" != "null" ]; then
        echo -e "${GREEN}✓ Query successful${NC}"
        echo "   Answer preview: $answer..."
        
        # Show metadata
        exec_time=$(echo "$query_response" | jq -r '.metadata.execution_time_seconds' 2>/dev/null)
        tokens=$(echo "$query_response" | jq -r '.metadata.tokens_used' 2>/dev/null)
        echo "   Execution time: ${exec_time}s"
        echo "   Tokens used: $tokens"
    else
        echo -e "${RED}✗ Query returned empty answer${NC}"
    fi
else
    echo -e "${RED}✗ Query failed${NC}"
fi

echo

# Test 3: Product-specific Query (should use HybridSearch)
echo -e "${BLUE}3. Testing Product Query...${NC}"
product_response=$(curl -s -X POST "$API_URL/query" \
    -H "Content-Type: application/json" \
    -H "X-API-Key: $API_KEY" \
    -d '{"question": "What are SpyroCloud features?"}')

if [ $? -eq 0 ] && [ ! -z "$product_response" ]; then
    answer=$(echo "$product_response" | jq -r '.answer' 2>/dev/null | head -c 100)
    if [ ! -z "$answer" ] && [ "$answer" != "null" ]; then
        echo -e "${GREEN}✓ Product query successful${NC}"
        echo "   Answer preview: $answer..."
    else
        echo -e "${RED}✗ Product query returned empty answer${NC}"
    fi
else
    echo -e "${RED}✗ Product query failed${NC}"
fi

echo

# Test 4: Available Tools
echo -e "${BLUE}4. Checking Available Tools...${NC}"
tools_response=$(curl -s -H "X-API-Key: $API_KEY" "$API_URL/tools")
tools=$(echo "$tools_response" | jq -r '.tools[].name' 2>/dev/null)

if [ ! -z "$tools" ]; then
    echo -e "${GREEN}✓ Tools endpoint working${NC}"
    echo "   Available tools:"
    echo "$tools" | while read tool; do
        echo "   - $tool"
    done
else
    echo -e "${RED}✗ Failed to get tools${NC}"
fi

echo
echo "==========================================="
echo -e "${GREEN}Test completed!${NC}"