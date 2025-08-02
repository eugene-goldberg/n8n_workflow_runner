# LlamaIndex Schema Transition Guide

## Overview

We've transitioned from dual-schema support to using **only LlamaIndex schema** for all knowledge graph operations. This simplifies the system and eliminates ambiguity.

## What Changed

### Old Approach (Dual Schema)
- Supported both `:Customer` (Spyro RAG) and `:__Entity__:CUSTOMER` (LlamaIndex)
- Complex queries checking both formats
- Potential confusion about data sources

### New Approach (LlamaIndex Only)
- All entities use LlamaIndex format: `:__Entity__:TYPE`
- Simplified queries
- Consistent data model
- Clear integration with LlamaIndex document ingestion

## Schema Format

All entities now follow this pattern:
```
:__Entity__:CUSTOMER
:__Entity__:PRODUCT
:__Entity__:TEAM
:__Entity__:RISK
```

## Migration

If you have existing data in the old Spyro RAG format, run:
```bash
./migrate_to_llamaindex.py
```

This will:
1. Convert all entities from old format to LlamaIndex format
2. Preserve all properties and relationships
3. Remove old labels

## Updated Components

### 1. Agent (`spyro_agent_llamaindex.py`)
- Uses only LlamaIndex schema
- Simplified queries without dual-format checking
- Clear schema expectations

### 2. Cypher Examples (`cypher_examples_llamaindex.py`)
- All examples use `:__Entity__:TYPE` format
- No compatibility patterns needed

### 3. Schema Definition (`llamaindex_schema.py`)
- Complete schema in LlamaIndex format
- Matches what LlamaIndex creates during ingestion

### 4. API
- Updated to use LlamaIndex-only agent
- Simpler, more consistent responses

## Benefits

1. **Simplicity**: No need to check multiple label formats
2. **Performance**: Queries run faster without dual checks
3. **Clarity**: Clear which schema is being used
4. **Consistency**: Aligns with LlamaIndex document ingestion
5. **Maintainability**: Easier to understand and modify

## Testing

Test the new schema with:
```bash
# Check current schema status
./check_current_schema.py

# Run test queries
./test_llamaindex_queries.sh
```

## Example Queries

### Old (Dual Schema)
```cypher
MATCH (c) 
WHERE ('Customer' IN labels(c) OR ('__Entity__' IN labels(c) AND 'CUSTOMER' IN labels(c)))
RETURN c.name
```

### New (LlamaIndex Only)
```cypher
MATCH (c:__Entity__:CUSTOMER)
RETURN c.name
```

## Important Notes

1. All new data ingested via LlamaIndex will automatically use this format
2. The migration is one-way - once migrated, data uses only LlamaIndex format
3. All queries must be updated to use the new format
4. The system no longer recognizes old format labels like `:Customer`