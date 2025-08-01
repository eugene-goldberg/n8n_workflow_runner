# Natural Business Query Test Results

## Summary of Search Tool Usage

| Query | Search Type Used | Expected Behavior |
|-------|-----------------|-------------------|
| 1. How much revenue will be at risk if Disney misses its SLA next month? | 🔍 vector_search only | ❌ Should use hybrid |
| 2. How much of the future revenue will be at risk if the Q1 2025 Feature Delivery project misses its deadline by 3 months? | 🔍 vector_search only | ❌ Should use hybrid |
| 3. What are the top risks related to achieving our $10M ARR target? | 🔍 vector_search only | ❌ Should use hybrid |
| 4. How much does it cost to run SpyroAnalytics across all customers? | 🔍 vector_search only | ❌ Should use hybrid |
| 5. What are our top 5 customer commitments and what risks could prevent us from meeting them? | 🔍 vector_search only | ❌ Should use hybrid |
| 6. Which Enterprise customers are at risk based on recent events? | 🔍 vector_search only | ❌ Should use hybrid |
| 7. What are the top customer concerns and what is being done to address them? | 🔍 vector_search only | ❌ Should use hybrid |
| 8. How does Disney's recent outage affect their overall relationship with us? | 🔄 vector_search + get_entity_relationships | ✅ Hybrid achieved! |
| 9. Do EA and Disney face similar risks that could impact our quarterly revenue? | 🕸️ graph_search only | ⚠️ Graph only |
| 10. How does team capacity affect our ability to deliver customer projects on time? | 🔍 vector_search only | ❌ Should use hybrid |

## Key Findings

### What Triggers Hybrid Search:
- **Query 8** successfully triggered hybrid search with the pattern "How does [Entity]'s [Event] affect their overall relationship with us?"
- This query explicitly asks about relationships and effects, which seems to be recognized by the system

### What Triggers Graph Search Only:
- **Query 9** triggered graph search when comparing two specific entities (EA and Disney)
- Pattern: "Do [Entity1] and [Entity2] face similar..."

### What Defaults to Vector Search:
- **7 out of 10** natural business questions defaulted to vector search only
- Even questions that clearly require relationship traversal (like revenue impact from SLA violations) are not triggering graph search

## The Problem

The current system is not recognizing that these natural business questions require relationship traversal:

1. **Revenue calculations** require: Customer → Subscription → ARR
2. **Risk assessments** require: Risk → Customer → Impact
3. **Cost analysis** requires: Product → Customer → Operational Cost
4. **Team impact** requires: Team → Project → Customer

## Patterns That Should Trigger Hybrid

Based on the example questions, these patterns should automatically trigger hybrid search:

1. **Impact Questions**: "How much... if X happens"
   - Requires traversing from event/condition to financial impact

2. **Risk Questions**: "What risks... prevent/threaten X"
   - Requires connecting risks to objectives through entities

3. **Cost Questions**: "How much does it cost..."
   - Requires aggregating costs across relationships

4. **Ranking Questions**: "Top N... and what..."
   - Requires both retrieval and relationship analysis

5. **Action Questions**: "What is being done..."
   - Requires mapping problems to solutions through entities

## Recommendations

1. The system needs better pattern recognition for business questions
2. Questions mentioning specific entities (Disney, EA, SpyroAnalytics) should trigger graph search
3. Questions about impacts, risks, costs, and relationships should default to hybrid
4. The agent prompt may need updating to recognize these patterns

The current behavior shows that only very explicit relationship questions trigger hybrid search, while natural business questions that implicitly require relationship traversal are missing this capability.