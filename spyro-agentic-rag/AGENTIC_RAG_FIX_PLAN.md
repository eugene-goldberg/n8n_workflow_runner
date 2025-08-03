# Agentic RAG Fix Plan: Empowering Autonomous Tool Selection

## Philosophy
True Agentic RAG gives the agent freedom to choose its tools and approach. Our goal is NOT to handle queries for the agent, but to provide comprehensive context enabling it to make informed decisions autonomously.

## Current State
- Success Rate: 16.7% (2/12 queries tested)
- Root Cause: Agent lacks accurate knowledge of the data model
- Result: Agent generates syntactically correct but semantically wrong Cypher queries

## Fix Strategy: Comprehensive Context Enhancement

### 1. Document the Complete Data Model
**Goal**: Give agent full visibility into what actually exists
- Extract all entity types with exact label names (e.g., `CUSTOMER`, `RISK`, `ISSUE`)
- Document all properties on each entity type
- Map all relationships with correct names
- Note data patterns (e.g., subscriptions are separate nodes, not customer properties)

### 2. Enhance System Prompt
**Goal**: Guide agent's reasoning without prescribing solutions
- Explain the LlamaIndex labeling convention (`:__Entity__:TYPE`)
- Describe data model philosophy (disconnected entities, separate nodes for attributes)
- Encourage exploration when primary paths fail
- Emphasize calculation over retrieval for derived metrics

### 3. Provide Rich Query Examples
**Goal**: Show possibilities without limiting creativity
- Examples demonstrating various entity types and their actual properties
- Patterns for traversing relationships
- Calculation examples (aggregations, derived metrics)
- Examples with OPTIONAL MATCH for sparse data
- Modern Cypher syntax (IS NOT NULL, not EXISTS)

### 4. Schema Information Enhancement
**Goal**: Make data structure discoverable
- Complete entity-relationship diagram in text form
- Property data types and value patterns
- Relationship cardinalities
- Data coverage notes (which entities have which properties)

### 5. Context Injection Points
- System prompt in agent configuration
- Cypher examples for Text2CypherRetriever
- Tool descriptions that reflect actual capabilities
- Schema information available to the agent

## Implementation Approach

### Phase 1: Discovery
1. Extract complete schema from Neo4j
2. Document all entities, properties, and relationships
3. Identify data patterns and coverage

### Phase 2: Context Creation
1. Update system prompt with discovered knowledge
2. Create comprehensive, accurate cypher examples
3. Enhance tool descriptions
4. Build schema reference

### Phase 3: Integration
1. Update cypher_examples_enhanced_v2.py
2. Modify agent system prompt
3. Ensure all context is accessible to agent

### Phase 4: Validation
1. Test with previously failed queries
2. Measure improvement in success rate
3. Iterate based on results

## Success Criteria
- Agent autonomously discovers correct property names
- Agent adapts to actual relationship patterns
- Agent calculates derived metrics when needed
- Agent explores alternative paths for sparse data
- Success rate improves from 16.7% to >83%

## Key Principle
We are not fixing queries; we are fixing the agent's understanding. With complete and accurate context, the agent should autonomously generate correct strategies and queries.