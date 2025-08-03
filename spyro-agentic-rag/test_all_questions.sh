#!/bin/bash

# Test all 60 business questions through the API
echo "TESTING ALL 60 BUSINESS QUESTIONS THROUGH API"
echo "=============================================="
echo "Start Time: $(date)"
echo ""

# Initialize counters
TOTAL=0
GROUNDED=0
GENERIC=0
FAILED=0

# Results file
RESULTS_FILE="api_test_results_detailed.txt"
echo "API Test Results - $(date)" > $RESULTS_FILE
echo "=======================================" >> $RESULTS_FILE
echo "" >> $RESULTS_FILE

# Test each question
for i in {1..60}; do
    echo "Testing Q$i..."
    
    # Run the test and capture output
    OUTPUT=$(source venv/bin/activate && python3 test_single_api_question.py $i 2>&1)
    
    # Check if grounded, generic, or failed
    if echo "$OUTPUT" | grep -q "✅ GROUNDED"; then
        ((GROUNDED++))
        STATUS="GROUNDED"
    elif echo "$OUTPUT" | grep -q "❌ GENERIC"; then
        ((GENERIC++))
        STATUS="GENERIC"
    elif echo "$OUTPUT" | grep -q "Status: FAILED\|Status: ERROR"; then
        ((FAILED++))
        STATUS="FAILED"
    else
        ((GENERIC++))
        STATUS="UNKNOWN"
    fi
    
    ((TOTAL++))
    
    # Save detailed output
    echo "Q$i: $STATUS" >> $RESULTS_FILE
    echo "$OUTPUT" >> $RESULTS_FILE
    echo "----------------------------------------" >> $RESULTS_FILE
    echo "" >> $RESULTS_FILE
    
    # Brief console output
    echo "Q$i: $STATUS"
    
    # Small delay between requests
    sleep 1
done

# Summary
echo ""
echo "TEST SUMMARY"
echo "============"
echo "Total Questions: $TOTAL"
echo "Grounded: $GROUNDED"
echo "Generic: $GENERIC"
echo "Failed: $FAILED"
echo "Success Rate: $(( GROUNDED * 100 / TOTAL ))%"
echo ""
echo "Detailed results saved to: $RESULTS_FILE"

# Save summary
echo "" >> $RESULTS_FILE
echo "SUMMARY" >> $RESULTS_FILE
echo "=======" >> $RESULTS_FILE
echo "Total Questions: $TOTAL" >> $RESULTS_FILE
echo "Grounded: $GROUNDED" >> $RESULTS_FILE
echo "Generic: $GENERIC" >> $RESULTS_FILE
echo "Failed: $FAILED" >> $RESULTS_FILE
echo "Success Rate: $(( GROUNDED * 100 / TOTAL ))%" >> $RESULTS_FILE