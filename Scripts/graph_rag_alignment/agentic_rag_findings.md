# Agentic RAG Investigation Findings

## Executive Summary

After extensive research and testing, I've discovered several key insights about the SpyroSolutions Agentic RAG implementation:

1. **The system IS using graph tools** - but there's a display issue in the demo app
2. **Natural language queries default to vector search** - even with explicit prompts
3. **Explicit relationship queries trigger graph tools** - when phrased correctly
4. **The n8n workflow has bugs** - it doesn't properly handle all tool types

## Key Discoveries

### 1. API vs Demo App Discrepancy

**Direct API calls reveal the truth:**
- Query: "Show me the relationship between Disney and their subscription revenue"
- API Response: Uses `get_entity_relationships` ✅
- Demo App Display: Shows only `vector_search` ❌

The n8n workflow's JavaScript code is missing `get_entity_relationships` from its tool mapping.

### 2. Tool Usage Patterns

**What triggers graph tools:**
- "Show me the relationship between X and Y" → `get_entity_relationships`
- "How does X connect to Y" → `graph_search`
- Queries with 2+ entity names → Sometimes triggers graph tools

**What defaults to vector search:**
- Natural business questions (even with entities)
- "How much revenue at risk..."
- "What are the top risks..."
- "Which customers have..."

### 3. Agentic RAG Principles

Based on research, agentic RAG should:
- **Route intelligently** based on query intent
- **Combine multiple tools** when needed
- **Self-grade** retrieval quality
- **Adapt** search strategy based on results

The current implementation has the tools but isn't routing optimally.

## Technical Issues Found

### 1. n8n Workflow Bug
```javascript
// Current (incorrect)
function getPurpose(toolName) {
  const purposes = {
    'vector_search': 'Semantic search in knowledge base',
    'graph_search': 'Graph traversal for relationships',
    // Missing: get_entity_relationships!
  };
}
```

### 2. Agent Tool Selection
Despite multiple prompt iterations:
- GPT-4o-mini: Very conservative, mostly vector search
- GPT-4o: Slightly better but still defaults to vector search
- Explicit prompts: Limited improvement

### 3. System Architecture
- Tools exist: ✅ (vector_search, graph_search, get_entity_relationships, hybrid_search)
- Tools work: ✅ (when called directly)
- Intelligent routing: ❌ (defaults to vector search)

## Why Natural Queries Fail

The agent appears to be:
1. **Over-trained on safety** - Prefers vector search as "safer" option
2. **Misunderstanding intent** - Doesn't recognize business questions need graph data
3. **Ignoring prompt instructions** - Even mandatory rules are overridden

## Recommendations

### 1. Fix n8n Workflow (Immediate)
Update the Format Success Response node to include all tool types:
```javascript
'get_entity_relationships': 'Entity relationship exploration'
```

### 2. Query Preprocessing (Short-term)
Add a preprocessing layer that:
- Detects entity mentions → Routes to graph tools
- Identifies business metrics → Routes to graph tools
- Classifies intent before agent processing

### 3. Custom Tool Selection (Long-term)
Implement explicit routing logic:
```python
if any(entity in query for entity in KNOWN_ENTITIES):
    use_graph_tools()
elif any(metric in query for metric in BUSINESS_METRICS):
    use_graph_tools()
else:
    use_vector_search()
```

### 4. Agent Framework Alternative
Consider frameworks with more deterministic routing:
- LangGraph with explicit state machines
- Custom routing layer before Pydantic AI
- Rule-based preprocessing with LLM fallback

## Successful Query Patterns

These patterns DO trigger graph tools:
1. "Show me the relationship between [Entity1] and [Entity2]"
2. "How does [Entity1] connect to [Entity2]"
3. "Get [Entity]'s relationships"

These patterns DON'T (but should):
1. "How much revenue at risk if [Entity] misses SLA"
2. "What are top risks to [Metric]"
3. "Which customers have [Metric] over [Value]"

## Conclusion

The Agentic RAG system has all necessary components but suffers from:
1. **Tool routing issues** - Natural queries don't trigger appropriate tools
2. **Display bugs** - n8n workflow doesn't show actual tool usage
3. **Agent limitations** - LLM prefers vector search despite instructions

The system is closer to working than it appears - fixing the n8n display bug and adding query preprocessing would significantly improve the experience.