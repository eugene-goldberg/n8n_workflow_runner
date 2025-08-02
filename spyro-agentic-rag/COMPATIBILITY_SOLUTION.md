# Schema Compatibility Solution

## Problem
- LlamaIndex stores entities as `:__Entity__:CUSTOMER`
- Spyro RAG expects entities as `:Customer`
- Backend API couldn't find LlamaIndex-ingested entities

## Solution Implemented

### 1. Created Schema Compatibility Layer
- `src/utils/schema_compatibility.py` - Label mapping and query transformation
- `src/utils/cypher_examples_compatible.py` - Compatible query examples

### 2. Updated Agent Implementation
- `src/agents/spyro_agent_compatible.py` - New agent with dual-schema support
- Modified queries to check both label formats
- Added UnifiedSearch tool as primary interface

### 3. Query Pattern Transformation
Original: `MATCH (c:Customer) RETURN c.name`
Compatible: `MATCH (c) WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c))) RETURN c.name`

### 4. Updated API
- Modified `src/api/main.py` to use compatible agent
- No API interface changes - fully backward compatible

## Key Features
✅ Works with both Spyro RAG and LlamaIndex data
✅ No data migration required
✅ Backward compatible with existing queries
✅ Transparent to API users
✅ Supports all entity types and relationships

## Testing
```bash
# Check database schemas
./check_schemas.py

# Test API with both formats
./test_compatible_queries.sh

# Run comprehensive tests
./test_dual_schema.py
```

## Results
- API now returns entities from both schemas
- Queries like "Show me all customers" return both TechCorp (Spyro) and InnovateTech Solutions (LlamaIndex)
- Aggregations work across both data sources
- Full semantic model preserved