#!/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/venv/bin/python3
"""Final verification of all 60 questions after improvements"""

import subprocess
import time
from datetime import datetime

print("=== FINAL VERIFICATION OF ALL 60 QUESTIONS ===")
print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nThis will test all 60 questions to measure the final success rate.\n")

# Run the comprehensive verification script
start_time = time.time()

result = subprocess.run(
    ['/Users/eugene/dev/apps/n8n_workflow_runner/langgraph-agentic-rag/scripts/verify_all_60.py'],
    capture_output=True,
    text=True
)

elapsed = time.time() - start_time

# Display output
print(result.stdout)

if result.stderr:
    print("\nErrors:")
    print(result.stderr)

print(f"\nTotal verification time: {elapsed/60:.1f} minutes")

# Parse final results from output
if "Grounded Answers:" in result.stdout:
    for line in result.stdout.split('\n'):
        if "Grounded Answers:" in line:
            # Extract the success rate
            parts = line.split('(')
            if len(parts) > 1:
                rate = parts[1].split('%')[0]
                try:
                    success_rate = float(rate)
                    print(f"\n{'='*60}")
                    print("FINAL RESULT")
                    print(f"{'='*60}")
                    if success_rate >= 83:
                        print(f"✅ SUCCESS: Achieved {success_rate}% grounded answers!")
                        print(f"   Target: >83%")
                        print(f"   Exceeded target by: {success_rate - 83:.1f} percentage points")
                    else:
                        print(f"❌ Current: {success_rate}% grounded answers")
                        print(f"   Target: >83%")
                        print(f"   Gap: {83 - success_rate:.1f} percentage points")
                    
                    # Show improvement from baseline
                    baseline = 21.7
                    print(f"\nImprovement from baseline:")
                    print(f"   Baseline: {baseline}%")
                    print(f"   Current: {success_rate}%")
                    print(f"   Improvement: {success_rate/baseline:.1f}x ({success_rate - baseline:.1f} percentage points)")
                except:
                    pass