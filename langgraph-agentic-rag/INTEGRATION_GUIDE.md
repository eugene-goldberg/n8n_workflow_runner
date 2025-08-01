# Router Integration Guide

This guide shows how to integrate the deterministic router with SpyroSolutions for immediate improvements.

## 1. Router Integration

### Option A: Modify System Prompt (Easiest)

Add this to `/root/spyro-agentic-rag/app/agent/prompts.py`:

```python
import sys
sys.path.append('/root/langgraph-agentic-rag')
from app.agent.router import DeterministicRouter

# Create global router instance
ROUTER = DeterministicRouter()

def get_enhanced_prompt(base_prompt: str, query: str) -> str:
    """Enhance prompt with routing decision"""
    decision = ROUTER.route(query)
    
    if decision.strategy.value == "graph":
        instruction = "\n\nMANDATORY: Use get_entity_relationships or graph_search for this query about specific business data.\n\n"
    elif decision.strategy.value == "vector":
        instruction = "\n\nMANDATORY: Use vector_search for this conceptual query.\n\n"
    elif decision.strategy.value == "hybrid_parallel":
        instruction = "\n\nMANDATORY: Use BOTH vector_search AND graph_search for this comparative query.\n\n"
    else:
        instruction = "\n\n"
    
    return instruction + base_prompt
```

### Option B: Modify Agent Class

Add routing to the existing agent in `/root/spyro-agentic-rag/app/agent/agent.py`:

```python
# Import at top
import sys
sys.path.append('/root/langgraph-agentic-rag')
from app.agent.router import DeterministicRouter
from app.monitoring.router_monitor import monitor

# In your agent class
class SpyroAgent:
    def __init__(self):
        self.router = DeterministicRouter()
        # ... existing init code ...
    
    async def process_query(self, query: str):
        # Get routing decision
        decision = self.router.route(query)
        tracking_id = monitor.log_routing_decision(query, decision)
        
        # Modify system prompt based on decision
        # ... your existing code with routing instructions ...
        
        # After getting result, log actual usage
        tools_used = [...]  # Extract from result
        monitor.log_actual_usage(tracking_id, tools_used)
```

## 2. n8n Workflow Fix

1. Open your n8n workflow in the UI
2. Find the "Format Success Response" node
3. Replace the code with the contents of `n8n_workflow_fix.js`
4. Save and test the workflow

The fix adds `get_entity_relationships` to the tool mapping so it displays correctly.

## 3. Monitoring Setup

### Enable Logging

1. Create logs directory:
```bash
mkdir -p /root/langgraph-agentic-rag/logs
```

2. Add monitoring to your agent (see Option B above)

3. View statistics:
```bash
cd /root/langgraph-agentic-rag
source venv/bin/activate
python3 monitor_cli.py
```

### What Gets Logged

- Every routing decision (query, strategy, confidence)
- Actual tools used by the agent
- Whether tools matched router expectation
- Response times and errors

### Monitoring Dashboard

The `monitor_cli.py` shows:
- Overall accuracy statistics
- Breakdown by strategy type
- Recent mismatches
- Hourly query volumes

## Quick Test

Test the router directly:

```python
from app.agent.router import DeterministicRouter

router = DeterministicRouter()

# Business query - should return GRAPH
result = router.route("How much revenue at risk if Disney churns?")
print(f"Strategy: {result.strategy.value}")
print(f"Confidence: {result.confidence}")
print(f"Entities: {result.detected_entities}")
```

## Expected Results

After integration, you should see:

1. **Business queries using graph tools**
   - "Revenue at risk" → graph_search
   - "Top customers by ARR" → get_entity_relationships

2. **Conceptual queries using vector search**
   - "What is an SLA?" → vector_search
   - "Best practices" → vector_search

3. **Monitoring showing high accuracy**
   - 80%+ tool usage matching router expectations
   - Clear patterns in mismatches for further tuning

## Troubleshooting

If tools don't match router expectations:

1. Check if system prompt modifications are being applied
2. Verify the agent is seeing the routing instructions
3. Look at monitor logs for patterns in mismatches
4. Consider making routing instructions more forceful

## Next Steps

Once basic integration is working:

1. Tune router rules based on mismatch patterns
2. Add more specific business entity detection
3. Implement full LangGraph workflow for complete control
4. Add query preprocessing for complex queries