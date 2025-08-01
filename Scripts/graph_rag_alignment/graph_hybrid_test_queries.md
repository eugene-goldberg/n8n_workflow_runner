# Graph and Hybrid Search Test Queries

Based on the example questions, here are queries adapted for our enhanced SpyroSolutions Graph RAG model that will trigger graph or hybrid search:

## 1. Revenue Risk Analysis Queries (Hybrid Search)

### SLA-Related Revenue Risk
```
"How much revenue will be at risk if Disney misses its SLA requirements next month?"
"What is the total ARR impact if EA experiences another SLA breach similar to their recent performance issues?"
"Show me the revenue at risk from all customers who have experienced SLA violations in the last 30 days"
```

### Project Deadline Revenue Impact
```
"How much future revenue will be at risk if the Disney Q1 2025 Feature Delivery project misses its deadline by 3 months?"
"What is the revenue impact if all at-risk projects from Enterprise customers fail to deliver on time?"
"Calculate the ARR exposure from Netflix if their ML Pipeline Enhancement project is delayed"
```

## 2. Goal Achievement Risk Queries (Graph Search)

### Company Objective Risks
```
"What are the top risks threatening our Q1 2025 customer retention objective?"
"Which risks are preventing us from achieving our $10M ARR growth target?"
"Show me all threats to our Q1 NPS improvement goal and their mitigation strategies"
```

### Strategic Risk Analysis
```
"Which customer risks could impact our 95% retention rate target?"
"What events and risks threaten our company objectives for 2025?"
"How do current SLA violations relate to our customer retention goals?"
```

## 3. Operational Cost Queries (Hybrid Search)

### Product Cost Analysis
```
"How much does it cost to run SpyroAnalytics across all regions and customers?"
"What is the total operational cost for SpyroSuite including infrastructure and team allocation?"
"Show me the cost breakdown for SpyroAPI and which customers contribute to covering these costs"
```

### Cost-Revenue Analysis
```
"Which products have the highest operational costs relative to their revenue contribution?"
"What is the profit margin for each product after considering operational costs?"
"How much does it cost to serve our Enterprise customers vs Pro customers?"
```

## 4. Customer Commitment & Risk Queries (Graph Search)

### Top Customer Analysis
```
"What are the top 5 customer commitments by ARR value and what are the current risks to achieving them?"
"Show me Disney's key project commitments and the risks that could prevent delivery"
"Which Enterprise customers have the highest revenue commitments and what threatens those commitments?"
```

### Commitment Risk Mapping
```
"For each customer with over $1M ARR, show their project commitments and associated delivery risks"
"What are Netflix's contractual commitments and which team dependencies could impact them?"
"Map EA's subscription commitments to their current project status and risk factors"
```

## 5. Customer Concern Analysis (Hybrid Search)

### Current Customer Issues
```
"What are the top customer concerns from Disney and Netflix, and what projects are addressing them?"
"Which teams are working on resolving the performance issues reported by EA?"
"Show me all customer-reported concerns and their resolution status"
```

### Concern Resolution Tracking
```
"What actions are being taken to address Disney's SLA breach concerns?"
"Which customer concerns are linked to at-risk projects?"
"How are we addressing the top 3 customer concerns across all Enterprise accounts?"
```

## 6. Complex Relationship Queries (Guaranteed Graph/Hybrid)

### Multi-Entity Traversals
```
"Show me how Disney's recent service outage event impacts their subscription value, project timelines, and team allocations"
"Trace the relationship between EA's security alert, their customer success score, and the teams working on remediation"
"Map the connection between Netflix's feature success event, their ARR contribution, and future project investments"
```

### Impact Chain Analysis
```
"How do SLA breaches for Disney cascade through to affect their success score, project priorities, and our Q1 objectives?"
"Show the full impact chain from EA's API performance issues to their subscription risk and our retention goals"
"Analyze how team capacity constraints relate to project delays and ultimately impact customer satisfaction scores"
```

### Cross-Cutting Business Analysis
```
"Which customers contribute most to our ARR target while also having the highest operational costs and most at-risk projects?"
"Show me customers where declining success scores correlate with missed project deadlines and increased support events"
"Identify the relationship between team utilization rates, project success, and customer retention"
```

## Testing Instructions

1. Use these queries in the demo interface at http://srv928466.hstgr.cloud:8082/
2. Queries mentioning specific entities (Disney, EA, Netflix) should trigger graph search
3. Queries about relationships and impacts should trigger hybrid search
4. Complex multi-hop queries will definitely use graph traversal

## Expected Behaviors

- **Graph Search (🕸️)**: Triggered when query mentions 2+ specific entities or asks about relationships
- **Hybrid Search (🔄)**: Triggered for complex business questions requiring both semantic understanding and relationship traversal
- **Pure Vector Search (🔍)**: Should rarely occur with these queries as they all involve relationships

## Key Entities to Reference

- **Customers**: Disney, EA, Netflix, Spotify, Nintendo
- **Products**: SpyroSuite, SpyroAnalytics, SpyroAPI, SpyroCloud
- **Teams**: Platform Team, Analytics Team, Integration Team, Customer Success Team, DevOps Team
- **Objectives**: "ARR Growth Target", "Customer Retention", "Q1 NPS Improvement", "Q1 Churn Reduction"
- **Projects**: Reference specific project names from the data