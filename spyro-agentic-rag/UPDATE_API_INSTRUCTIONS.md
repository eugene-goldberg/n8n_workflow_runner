# Instructions to Update API to Use Enhanced Agent v3

## Quick Steps

1. **Update the import in `/src/api/main.py`**:
   ```python
   # Line 15 - Change from:
   from ..agents.spyro_agent_enhanced_fixed import SpyroAgentEnhanced as SpyroAgent, create_agent
   
   # To:
   from ..agents.spyro_agent_enhanced_v3 import SpyroAgentEnhanced as SpyroAgent, create_agent
   ```

2. **Restart the API service**:
   ```bash
   # Stop the current service
   pkill -f "uvicorn.*main:app"
   
   # Start with the new agent
   cd /Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag
   python -m uvicorn src.api.main:app --reload --port 8000
   ```

3. **Verify the agent is working**:
   ```bash
   # Test with a query
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -H "X-API-Key: test-api-key-123" \
     -d '{"question": "What percentage of our ARR is dependent on customers with success scores below 70?"}'
   ```

4. **Monitor the Cypher queries**:
   ```bash
   # Watch the query log in real-time
   tail -f cypher_queries.log
   ```

## Important Notes

- The enhanced agent v3 automatically uses the correct files:
  - `cypher_examples_enhanced_v3.py` (correct examples)
  - `neo4j_data_model_context.py` (schema knowledge)
  - `example_formatter.py` (proper formatting)

- All Cypher queries will be logged to `cypher_queries.log`

- The agent now has comprehensive knowledge of:
  - Correct property names (e.g., `impact_amount` not `potential_impact`)
  - Correct relationships (e.g., `HAS_SUCCESS_SCORE`, `SUBSCRIBES_TO`)
  - LlamaIndex label format (e.g., `'__Entity__' IN labels(n) AND 'CUSTOMER' IN labels(n)`)
  - Data patterns (e.g., subscription values as strings like "$8M")

## Testing the Updated API

Run these test queries to verify the enhanced agent is working:

```bash
# Test 1: ARR percentage
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"question": "What percentage of our ARR is dependent on customers with success scores below 70?"}'

# Test 2: Active risks
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"question": "How many active risks are unmitigated, and what is their potential financial impact?"}'

# Test 3: Customer retention
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-api-key-123" \
  -d '{"question": "What is the customer retention rate across different product lines?"}'
```

Check `cypher_queries.log` after each query to see the generated Cypher queries.