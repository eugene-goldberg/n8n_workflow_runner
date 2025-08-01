#!/bin/bash

# Test Script to Identify Data Gaps in SpyroSolutions Agentic RAG
# This script captures full responses including errors to identify missing data

# Configuration
API_URL="http://localhost:8000/query"
API_KEY="spyro-secret-key-123"
OUTPUT_DIR="data_gap_analysis"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Summary file
SUMMARY_FILE="$OUTPUT_DIR/data_gaps_summary.txt"
echo "DATA GAP ANALYSIS - $(date)" > "$SUMMARY_FILE"
echo "======================================" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

# Function to send query and analyze response
analyze_query() {
    local question="$1"
    local category="$2"
    local test_num="$3"
    
    echo -e "\n${BLUE}[$test_num] Testing:${NC} $question"
    echo -e "${BLUE}Category:${NC} $category"
    
    # Create JSON payload
    local json_payload=$(jq -n --arg q "$question" '{"question": $q}')
    
    # Send request and capture full response
    local response_file="$OUTPUT_DIR/test_${test_num}_full_response.json"
    local response=$(curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -H "X-API-Key: $API_KEY" \
        -d "$json_payload")
    
    # Save full response
    echo "$response" > "$response_file"
    
    # Extract key information
    local answer=$(echo "$response" | jq -r '.answer' 2>/dev/null)
    local exec_time=$(echo "$response" | jq -r '.metadata.execution_time_seconds' 2>/dev/null)
    local tokens=$(echo "$response" | jq -r '.metadata.tokens_used' 2>/dev/null)
    
    # Display answer
    echo -e "${GREEN}Answer:${NC} $(echo "$answer" | head -c 200)..."
    echo -e "Execution: ${exec_time}s | Tokens: $tokens"
    
    # Analyze for data gaps
    echo "" >> "$SUMMARY_FILE"
    echo "[$test_num] $question" >> "$SUMMARY_FILE"
    echo "Category: $category" >> "$SUMMARY_FILE"
    
    # Check for common error patterns and missing data indicators
    if echo "$answer" | grep -q "no specific data available"; then
        echo -e "${YELLOW}⚠ DATA GAP: No specific data available${NC}"
        echo "DATA GAP: No specific data available" >> "$SUMMARY_FILE"
    fi
    
    if echo "$answer" | grep -q "division by zero"; then
        echo -e "${YELLOW}⚠ DATA GAP: Division by zero (likely no matching records)${NC}"
        echo "DATA GAP: Division by zero error - no matching records" >> "$SUMMARY_FILE"
    fi
    
    if echo "$answer" | grep -q "property key is not in the database"; then
        echo -e "${YELLOW}⚠ SCHEMA GAP: Missing property in database${NC}"
        echo "SCHEMA GAP: Missing property" >> "$SUMMARY_FILE"
        # Extract missing property name
        local missing_prop=$(echo "$answer" | grep -o "missing property name is: [^)]*" | cut -d: -f2 | xargs)
        if [ ! -z "$missing_prop" ]; then
            echo "  Missing property: $missing_prop" >> "$SUMMARY_FILE"
        fi
    fi
    
    if echo "$answer" | grep -q "label is not in the database"; then
        echo -e "${YELLOW}⚠ SCHEMA GAP: Missing label/entity in database${NC}"
        echo "SCHEMA GAP: Missing label/entity" >> "$SUMMARY_FILE"
        # Extract missing label
        local missing_label=$(echo "$answer" | grep -o "missing label name is: [^)]*" | cut -d: -f2 | xargs)
        if [ ! -z "$missing_label" ]; then
            echo "  Missing label: $missing_label" >> "$SUMMARY_FILE"
        fi
    fi
    
    if echo "$answer" | grep -q "No results found"; then
        echo -e "${YELLOW}⚠ DATA GAP: Query returned no results${NC}"
        echo "DATA GAP: No results found" >> "$SUMMARY_FILE"
    fi
    
    if echo "$answer" | grep -q "Agent stopped due to iteration limit"; then
        echo -e "${RED}⚠ ERROR: Agent hit iteration limit${NC}"
        echo "ERROR: Agent iteration limit reached" >> "$SUMMARY_FILE"
    fi
    
    if echo "$answer" | grep -q "Type mismatch"; then
        echo -e "${RED}⚠ QUERY ERROR: Type mismatch in Cypher query${NC}"
        echo "QUERY ERROR: Type mismatch" >> "$SUMMARY_FILE"
    fi
    
    if echo "$answer" | grep -q "Invalid input"; then
        echo -e "${RED}⚠ QUERY ERROR: Invalid Cypher syntax${NC}"
        echo "QUERY ERROR: Invalid Cypher syntax" >> "$SUMMARY_FILE"
    fi
    
    # Brief pause between requests
    sleep 1
}

# Main execution
echo "=========================================="
echo "SpyroSolutions Data Gap Analysis"
echo "=========================================="
echo "This analysis identifies missing data and schema gaps"
echo

# Test key questions from each category
echo -e "\n${BLUE}=== Testing Key Business Questions ===${NC}"

# Revenue & Financial
analyze_query "What percentage of our ARR is dependent on customers with success scores below 70?" "Revenue" 1
analyze_query "How much revenue will be at risk if TechCorp misses their SLA next month?" "Revenue" 2
analyze_query "Which customers generate 80% of our revenue, and what are their current risk profiles?" "Revenue" 3
analyze_query "What is the profitability margin for each product line?" "Revenue" 4
analyze_query "How do operational costs impact profitability for our top 10 customers?" "Revenue" 5

# Customer Success
analyze_query "Which customers have declining success scores, and what events are driving the decline?" "Customer" 6
analyze_query "What percentage of customers experienced negative events in the last 90 days?" "Customer" 7
analyze_query "Which features were promised to customers, and what is their delivery status?" "Customer" 8

# Product Management
analyze_query "What percentage of roadmap items are currently behind schedule?" "Product" 9
analyze_query "Which teams are responsible for delayed roadmap items?" "Product" 10
analyze_query "How many customer commitments depend on roadmap items at risk?" "Product" 11

# Risk Management
analyze_query "What are the top risks related to achieving our expansion objective?" "Risk" 12
analyze_query "Which teams are understaffed relative to their project commitments?" "Risk" 13

# Team Management
analyze_query "What is the revenue-per-team-member for each department?" "Team" 14
analyze_query "Which teams have the highest impact on customer success scores?" "Team" 15

# Generate consolidated report
echo -e "\n${BLUE}=========================================="
echo "Generating Consolidated Report..."
echo "==========================================${NC}"

# Count data gaps
MISSING_DATA=$(grep -c "DATA GAP" "$SUMMARY_FILE")
SCHEMA_GAPS=$(grep -c "SCHEMA GAP" "$SUMMARY_FILE")
QUERY_ERRORS=$(grep -c "QUERY ERROR" "$SUMMARY_FILE")

echo "" >> "$SUMMARY_FILE"
echo "======================================" >> "$SUMMARY_FILE"
echo "SUMMARY OF GAPS" >> "$SUMMARY_FILE"
echo "======================================" >> "$SUMMARY_FILE"
echo "Total Data Gaps: $MISSING_DATA" >> "$SUMMARY_FILE"
echo "Total Schema Gaps: $SCHEMA_GAPS" >> "$SUMMARY_FILE"
echo "Total Query Errors: $QUERY_ERRORS" >> "$SUMMARY_FILE"

# Extract unique missing properties
echo "" >> "$SUMMARY_FILE"
echo "MISSING PROPERTIES:" >> "$SUMMARY_FILE"
grep "Missing property:" "$SUMMARY_FILE" | sort | uniq >> "$SUMMARY_FILE"

echo "" >> "$SUMMARY_FILE"
echo "MISSING LABELS:" >> "$SUMMARY_FILE"
grep "Missing label:" "$SUMMARY_FILE" | sort | uniq >> "$SUMMARY_FILE"

# Display summary
echo
echo -e "${GREEN}Analysis Complete!${NC}"
echo -e "Data Gaps Found: ${YELLOW}$MISSING_DATA${NC}"
echo -e "Schema Gaps Found: ${YELLOW}$SCHEMA_GAPS${NC}"
echo -e "Query Errors Found: ${RED}$QUERY_ERRORS${NC}"
echo
echo "Full report saved to: $SUMMARY_FILE"
echo "Individual responses saved in: $OUTPUT_DIR/"

# Create actionable recommendations
RECOMMENDATIONS_FILE="$OUTPUT_DIR/recommendations.txt"
echo "ACTIONABLE RECOMMENDATIONS" > "$RECOMMENDATIONS_FILE"
echo "=========================" >> "$RECOMMENDATIONS_FILE"
echo "" >> "$RECOMMENDATIONS_FILE"
echo "Based on the data gap analysis, here are the recommended actions:" >> "$RECOMMENDATIONS_FILE"
echo "" >> "$RECOMMENDATIONS_FILE"

if grep -q "Missing property: timestamp" "$SUMMARY_FILE"; then
    echo "1. Add 'timestamp' property to Event nodes" >> "$RECOMMENDATIONS_FILE"
fi

if grep -q "Missing property: trend" "$SUMMARY_FILE"; then
    echo "2. Add 'trend' property to CustomerSuccessScore nodes" >> "$RECOMMENDATIONS_FILE"
fi

if grep -q "Missing label: RoadmapItem" "$SUMMARY_FILE"; then
    echo "3. Create RoadmapItem nodes and connect to Products" >> "$RECOMMENDATIONS_FILE"
fi

if grep -q "Division by zero" "$SUMMARY_FILE"; then
    echo "4. Add more diverse customer data with varying success scores" >> "$RECOMMENDATIONS_FILE"
fi

if grep -q "profitability" "$SUMMARY_FILE"; then
    echo "5. Add Profitability nodes and relationships to OperationalCost" >> "$RECOMMENDATIONS_FILE"
fi

echo "" >> "$RECOMMENDATIONS_FILE"
echo "See $SUMMARY_FILE for complete details." >> "$RECOMMENDATIONS_FILE"

echo
echo "Recommendations saved to: $RECOMMENDATIONS_FILE"