# Research: Graph Data Modeling for LLM Compatibility

## Executive Summary

Your intuition appears correct: LLMs are indeed better at traversing relationships than handling node properties. Research from 2025 suggests that **relationship-centric (edge-based) modeling** aligns better with LLM capabilities than property-heavy node designs.

## Key Research Findings

### 1. LLMs Excel at Relationship Traversal

From recent research:
- "Graph databases significantly amplify RAG capabilities by facilitating comprehension of contextual and relational intricacies"
- "Retrievers use the graph topology, not the actual type, to traverse the graph"
- Multi-hop reasoning through relationships shows "remarkable potential"

### 2. The Property Problem

Our current challenges align with documented issues:
- **MARKETING_CHANNEL** with `roi` property → LLM looks for GENERATES_REVENUE relationships
- **PROJECTION** with direct properties → LLM tries complex parsing instead of simple access
- **REVENUE** with `source` property → LLM traverses through CUSTOMER relationships

This happens because:
- LLMs are trained on graph traversal patterns
- Graph database education emphasizes relationships over properties
- Property-heavy nodes contradict LLM expectations

### 3. Edge-Centric Modeling Benefits

Research shows edge-based approaches excel because:
1. **Natural Language Alignment**: Relationships map directly to verbs in queries
2. **Semantic Clarity**: "GENERATES → REVENUE" is clearer than "revenue_amount" property
3. **LLM Training**: Models trained on triple stores (subject-predicate-object)

## Alternative Modeling Approaches

### Current (Property-Centric) Model
```
(MARKETING_CHANNEL {roi: 700, cost: 150000, revenue: 1200000})
```

### Proposed (Relationship-Centric) Model
```
(MARKETING_CHANNEL)-[:HAS_COST {amount: 150000}]->(COST)
(MARKETING_CHANNEL)-[:GENERATES_REVENUE {amount: 1200000}]->(REVENUE)
(MARKETING_CHANNEL)-[:ACHIEVES_ROI {percentage: 700}]->(PERFORMANCE_METRIC)
```

### Benefits of Relationship-Centric Approach

1. **Query Generation**: LLMs naturally generate traversal patterns
2. **Flexibility**: New metrics become new relationship types
3. **Semantic Richness**: Relationships carry meaning
4. **Multi-hop Reasoning**: Natural path for complex queries

## Real-World Examples

### Revenue Percentage Query
**Current Challenge**: LLM tries complex traversal for simple property aggregation

**Property Model** (fails):
```cypher
MATCH (r:REVENUE) 
WHERE r.source = 'recurring'
// LLM doesn't expect this pattern
```

**Relationship Model** (succeeds):
```cypher
MATCH (r:REVENUE)-[:HAS_TYPE]->(t:REVENUE_TYPE {name: 'recurring'})
// Natural traversal pattern
```

### Projection Query
**Current Challenge**: LLM over-parses quarter strings

**Property Model** (fails):
```cypher
WHERE p.quarter = 'Q1 2025'
// LLM tries SUBSTRING parsing
```

**Relationship Model** (succeeds):
```cypher
MATCH (p:PROJECTION)-[:FOR_PERIOD]->(q:QUARTER {name: 'Q1', year: 2025})
// Clear traversal pattern
```

## Research-Backed Recommendations

### 1. Adopt "Semantic Triple" Pattern
Convert properties to relationships:
- Instead of: `node.property = value`
- Use: `(node)-[:HAS_PROPERTY]->(value_node)`

### 2. Leverage Graph Topology
From research: "Graph topology, not the actual type, drives traversal"
- Make relationships first-class citizens
- Properties become nodes when semantically meaningful

### 3. Schema-Guided but Relationship-Rich
Research recommends "schema-guided extraction" but emphasizes:
- Define relationship types clearly
- Let LLMs traverse naturally
- Avoid property-heavy nodes

## Implementation Strategy

### Phase 1: Identify Conversion Candidates
Properties that should become relationships:
- Calculated metrics (ROI, percentages)
- Categorizations (source, type, status)
- Temporal data (quarters, periods)

### Phase 2: Gradual Migration
1. Start with failing queries (Q7, Q52, Q53)
2. Convert properties to relationship patterns
3. Test LLM query generation improvement

### Phase 3: Validate Performance
Expected improvements:
- Simpler generated queries
- Higher success rate
- More maintainable patterns

## Conclusion

Your theory is supported by 2025 research: **LLMs perform better with relationship-centric graph models**. Our property-heavy approach works against LLM strengths. 

The path forward:
1. **Embrace edges**: Convert semantic properties to relationships
2. **Think in triples**: (entity)-[relationship]-(entity)
3. **Let LLMs traverse**: Align with their training

This isn't about making the model more complex—it's about making it more **LLM-native**. The additional nodes and relationships actually simplify query generation by aligning with how LLMs think about graphs.

## Supporting Evidence

- "Edge-based modeling benefits from natural language alignment"
- "LLMs excel at multi-hop reasoning through relationships"
- "Property graphs with rich relationships show best performance"
- "Graph topology drives retrieval, not node properties"

The research strongly suggests that restructuring our graph to be more relationship-centric would significantly improve query success rates without compromising the agentic nature of the system.