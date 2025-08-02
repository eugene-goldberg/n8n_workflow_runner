#!/bin/bash

# Test compatible queries against the updated API

echo "=== TESTING SCHEMA-COMPATIBLE SPYRO RAG API ==="
echo ""
echo "These queries will work with both Spyro RAG and LlamaIndex data..."
echo ""

# API configuration
API_URL="http://localhost:8001"
API_KEY="test-api-key-123"

# Test 1: List all customers (should find both formats)
echo "1. List all customers:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "List all customers with their subscription values"
  }' | jq '.'

echo -e "\n---\n"

# Test 2: Query for new LlamaIndex customer
echo "2. Query for InnovateTech Solutions (LlamaIndex format):"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Tell me about InnovateTech Solutions and their subscription"
  }' | jq '.'

echo -e "\n---\n"

# Test 3: Query for original Spyro customer
echo "3. Query for TechCorp (Spyro RAG format):"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "What is TechCorp subscription value and what products do they use?"
  }' | jq '.'

echo -e "\n---\n"

# Test 4: Aggregation across both formats
echo "4. Count all customers by format:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Count how many customers we have from each data source (Spyro vs LlamaIndex)"
  }' | jq '.'

echo -e "\n---\n"

# Test 5: High-value subscriptions
echo "5. High-value subscriptions (both formats):"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Which customers have subscriptions over $5M?"
  }' | jq '.'

echo -e "\n---\n"

# Test 6: Teams and products
echo "6. Teams and their products:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Show me all teams and the products they support"
  }' | jq '.'

echo -e "\n---\n"

# Test 7: Total ARR calculation
echo "7. Total ARR across both schemas:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "What is our total Annual Recurring Revenue?"
  }' | jq '.'

echo -e "\n---\n"

# Test 8: Risk assessment
echo "8. Customer risks (both formats):"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Show me all customers and their associated risks"
  }' | jq '.'

echo -e "\n=== END OF TESTS ==="