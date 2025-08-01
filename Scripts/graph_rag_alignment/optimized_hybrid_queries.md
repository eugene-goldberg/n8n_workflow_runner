# Optimized Hybrid Search Queries for SpyroSolutions

Based on research into hybrid RAG patterns, here are optimized versions of the example questions that should reliably trigger hybrid search (combining vector and graph search).

## Key Principles for Hybrid Search Triggers

1. **Combine relationship traversal with impact analysis**
2. **Include specific entity names AND semantic concepts**
3. **Use multi-hop reasoning patterns**
4. **Request both factual data and analytical insights**

## Optimized Queries Based on Example Questions

### 1. Revenue Risk from SLA Violations
**Original**: "How much revenue will be at risk if EA misses its SLA next month?"

**Optimized for Hybrid Search**:
```
Analyze the relationship between EA's current SLA performance metrics and their subscription revenue of $1.2M ARR, then calculate the revenue at risk if they experience SLA violations similar to Disney's recent breaches, considering the impact on their customer success score and retention probability
```

**Why it triggers hybrid**:
- Graph: Traverses EA → SLA → Subscription → Revenue relationships
- Vector: Analyzes concepts of "risk", "impact", "retention probability"

### 2. Project Deadline Impact on Future Revenue
**Original**: "How much of the future revenue will be at risk if SCCS feature project misses its deadline by 3 months?"

**Optimized for Hybrid Search**:
```
Show me how Disney's Q1 2025 Feature Delivery project delay would cascade through their $1.5M subscription value, affect their customer success score from 78 to potentially below 70, and quantify the revenue at risk over the next 3 months based on similar patterns from EA's project delays
```

**Why it triggers hybrid**:
- Graph: Multi-hop traversal Project → Customer → Score → Subscription
- Vector: Pattern matching, risk quantification, temporal analysis

### 3. Risks to Goal Achievement
**Original**: "What are the top risks related to achieving the goal X?"

**Optimized for Hybrid Search**:
```
Map the connections between our $10M ARR growth target and the specific risks from Disney's SLA violations, EA's security alerts, and Netflix's project status, then analyze which operational factors and team capacity constraints pose the greatest threat to achieving this objective
```

**Why it triggers hybrid**:
- Graph: Objective → Risks → Customers → Events relationships
- Vector: Risk prioritization, operational analysis, constraint evaluation

### 4. Product Operational Costs
**Original**: "How much $ does it cost to run product X across all regions?"

**Optimized for Hybrid Search**:
```
Calculate the total operational cost for SpyroAnalytics by tracing its usage across Disney, Netflix, and EA subscriptions, including infrastructure costs of $35K/month, team allocations from Analytics Team at 90% capacity, and how these costs relate to the $1.8M revenue it generates
```

**Why it triggers hybrid**:
- Graph: Product → Customers → Teams → Costs relationships
- Vector: Cost calculation, capacity analysis, ROI concepts

### 5. Customer Commitments and Risks
**Original**: "What are the top-5 customer commitments and what are the current risks to achieving them?"

**Optimized for Hybrid Search**:
```
Identify the top 5 customers by ARR (Disney at $1.5M, Netflix at $1.8M, EA at $1.2M, and others), trace their project commitments through teams like Platform Team and Integration Team, then analyze how recent events (Disney's outage, EA's security alert) threaten these commitments and our Q1 retention objectives
```

**Why it triggers hybrid**:
- Graph: Customers → Projects → Teams → Events → Objectives
- Vector: Commitment analysis, threat assessment, retention impact

### 6. Customer Concerns and Actions
**Original**: "What are the top customer concerns and what is currently being done to address them?"

**Optimized for Hybrid Search**:
```
Analyze the pattern of concerns from Disney (SLA breaches causing 78 success score), EA (security alerts), and Netflix (performance issues), show which teams are assigned to address each concern, and evaluate how current projects like Disney's SSO Integration and EA's API Migration are mitigating these risks
```

**Why it triggers hybrid**:
- Graph: Customers → Events → Teams → Projects relationships
- Vector: Concern patterns, mitigation strategies, effectiveness analysis

## Query Formulation Best Practices

### 1. **Multi-Entity References**
Always include 2-3 specific entities (customers, products, teams) to trigger graph traversal

### 2. **Relationship Keywords**
Use phrases like:
- "trace the connection between"
- "show how X affects Y through Z"
- "analyze the relationship between"
- "map the impact from X to Y"

### 3. **Analytical Components**
Include analytical tasks that require semantic understanding:
- "calculate the impact"
- "analyze the pattern"
- "evaluate the risk"
- "quantify the effect"

### 4. **Specific Data Points**
Reference actual values from the graph:
- ARR/MRR values
- Success scores
- Team names
- Project names

### 5. **Multi-Hop Patterns**
Structure queries to require traversing multiple relationships:
- Entity A → affects → Entity B → impacts → Metric C

## Testing These Queries

Each optimized query should trigger:
1. **Graph search** for entity relationships and traversals
2. **Vector search** for semantic concepts and analysis
3. Result in true hybrid search with both 🕸️ and 🔍 indicators

The key is combining specific entity traversal needs with analytical/semantic requirements that can't be satisfied by graph structure alone.