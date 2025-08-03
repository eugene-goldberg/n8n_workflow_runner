#!/bin/bash
# Test a sample of queries across the range

echo "Testing sample of 20 queries..."
echo "=============================="

GROUNDED=0
GENERIC=0

# Test a diverse sample
QUERIES=(21 25 30 34 37 40 41 44 45 48 49 50 51 54 55 56 57 59 60)

for i in "${QUERIES[@]}"; do
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
echo "Success rate: $(( GROUNDED * 100 / (GROUNDED + GENERIC) ))%"