#!/bin/bash
# Test 10 queries one at a time

echo "Testing 10 queries..."
echo "===================="

GROUNDED=0
GENERIC=0

# Test queries 11-20
for i in {11..20}; do
    echo -n "Q$i: "
    OUTPUT=$(source venv/bin/activate && python3 test_single_api_question.py $i 2>&1)
    
    if echo "$OUTPUT" | grep -q "✅ GROUNDED"; then
        echo "✅ GROUNDED"
        ((GROUNDED++))
    else
        echo "❌ GENERIC"
        ((GENERIC++))
    fi
    
    sleep 1
done

echo ""
echo "Summary: $GROUNDED grounded, $GENERIC generic"