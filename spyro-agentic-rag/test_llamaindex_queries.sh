#!/bin/bash

# Test queries for LlamaIndex-only schema

echo "=== TESTING LLAMAINDEX SCHEMA QUERIES ==="
echo ""
echo "All queries now use LlamaIndex schema (:__Entity__:TYPE)"
echo ""

# API configuration
API_URL="http://localhost:8000"
API_KEY="spyro-secret-key-123"

# Test 1: List all customers
echo "1. List all customers:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "List all customers with their subscription values"
  }' | jq '.'

echo -e "\n---\n"

# Test 2: Query for specific customer
echo "2. Query for InnovateTech Solutions:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Tell me about InnovateTech Solutions and their subscription"
  }' | jq '.'

echo -e "\n---\n"

# Test 3: High-value subscriptions
echo "3. High-value subscriptions:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Which customers have subscriptions over $5M?"
  }' | jq '.'

echo -e "\n---\n"

# Test 4: Teams and products
echo "4. Teams and their products:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Show me all teams and the products they support"
  }' | jq '.'

echo -e "\n---\n"

# Test 5: Total ARR
echo "5. Total Annual Recurring Revenue:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "What is our total Annual Recurring Revenue?"
  }' | jq '.'

echo -e "\n---\n"

# Test 6: Customer risks
echo "6. Customer risks:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Show me all customers and their associated risks"
  }' | jq '.'

echo -e "\n---\n"

# Test 7: Product features
echo "7. SpyroCloud features:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "What are the key features of SpyroCloud?"
  }' | jq '.'

echo -e "\n---\n"

# Test 8: Count entities
echo "8. Count all entity types:"
curl -X POST "$API_URL/query" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "question": "Count the number of customers, products, teams, and risks in our system"
  }' | jq '.'

echo -e "\n=== END OF TESTS ==="