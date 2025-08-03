#!/bin/bash
# Run business queries in batches

# Check if start and end arguments are provided
if [ $# -ne 2 ]; then
    echo "Usage: ./run_queries_batch.sh <start_query> <end_query>"
    echo "Example: ./run_queries_batch.sh 1 10"
    exit 1
fi

START=$1
END=$2

echo "Running queries from $START to $END"
echo "=================================="

for i in $(seq $START $END); do
    echo ""
    echo "Running query $i..."
    ./venv/bin/python test_single_business_query.py $i
    
    # Brief pause between queries
    sleep 2
done

echo ""
echo "Batch complete!"
echo ""
echo "Check results in: 60_queries_results_progressive.json"