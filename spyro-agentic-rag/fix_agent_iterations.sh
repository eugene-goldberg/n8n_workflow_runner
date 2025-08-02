#!/bin/bash

# Fix for agent iteration limits hitting on complex graph queries

echo "Fixing agent iteration limits for complex graph queries..."

# Set the environment variable to increase max iterations
export AGENT_MAX_ITERATIONS=10

echo "AGENT_MAX_ITERATIONS set to 10 (was 3)"
echo ""
echo "To make this permanent, add to your .env file:"
echo "AGENT_MAX_ITERATIONS=10"
echo ""
echo "Or run the API with:"
echo "AGENT_MAX_ITERATIONS=10 python src/api/main_enhanced.py"
echo ""
echo "The API needs to be restarted for this change to take effect."