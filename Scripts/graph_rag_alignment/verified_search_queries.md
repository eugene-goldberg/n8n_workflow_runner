# Verified Search Query Patterns

Based on testing, here's what actually triggers different search types:

## Graph Search Only Queries (🕸️)

These reliably trigger graph search (`get_entity_relationships` or `graph_search`):

```
Show me the relationship between Disney and EA including their subscriptions, projects, and which teams are working on them
```

```
Map the connections between EA's security alert, Disney's SLA breach, and Netflix's project status
```

```
Trace how Disney's service outage event connects to their declining success score
```

## Vector Search Only Queries (🔍)

Most queries default to vector search, even when mentioning entities:

```
How much revenue will be at risk if Disney's current SLA violations continue?
```

```
What is preventing us from achieving our $10M ARR target?
```

```
Show me EA's recent security alert impact on subscription value
```

## True Hybrid Search Queries (🔄)

These SOMETIMES trigger both vector and graph search, but it's inconsistent:

```
Analyze the correlation between customer success scores and project delays across Disney, EA, and Netflix, and identify which operational costs could be reduced
```

```
Show me how Disney's recent service outage event impacts their subscription value, project timelines, and team allocations
```

## Key Findings

1. **Graph search triggers most reliably when**:
   - Using "Show me the relationship between [Entity1] and [Entity2]"
   - Using "Map the connections between" multiple entities
   - Explicitly asking for entity relationships

2. **Vector search is the default** for:
   - Questions about impact, risk, or analysis
   - Queries with single entities
   - General business questions

3. **Hybrid search is unpredictable**:
   - The same query can trigger different search combinations
   - `metadata.search_type` may show "HYBRID" even with single search type
   - True hybrid (both searches) happens less frequently than expected

## Recommended Approach

For guaranteed graph search inclusion:
1. Start with "Show me the relationship between..."
2. Name at least 2 specific entities
3. Ask for connections, relationships, or paths

For hybrid search attempts:
1. Combine relationship request with analysis
2. Include both entity names AND business concepts
3. Be prepared for inconsistent results

## Testing Note

The system's search type selection appears to be non-deterministic. The same query may trigger different search combinations on different runs. This suggests the agent is making dynamic decisions based on factors beyond just the query text.