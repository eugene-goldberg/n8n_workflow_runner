# Natural Business Questions for Hybrid Search

These questions are formulated the way actual business users would ask them, based on the example questions provided. The system should recognize these patterns and trigger hybrid search automatically.

## Revenue Risk Questions

### 1. SLA Impact on Revenue
```
How much revenue will be at risk if Disney misses its SLA next month?
```
**Expected behavior**: Should traverse Disney → SLA → Subscription ($1.5M ARR) and calculate risk

### 2. Project Delay Financial Impact
```
How much of the future revenue will be at risk if the Q1 2025 Feature Delivery project misses its deadline by 3 months?
```
**Expected behavior**: Should connect Project → Customer → Revenue and analyze delay impact

## Goal Achievement Questions

### 3. Risks to ARR Target
```
What are the top risks related to achieving our $10M ARR target?
```
**Expected behavior**: Should identify risks across all customers and their impact on the target

### 4. Customer Retention Risks
```
What threatens our 95% customer retention goal?
```
**Expected behavior**: Should analyze customer health scores, events, and risk factors

## Cost Analysis Questions

### 5. Product Operating Costs
```
How much does it cost to run SpyroAnalytics across all customers?
```
**Expected behavior**: Should sum operational costs and allocate by customer usage

### 6. Team Cost Allocation
```
What's the total cost of the Platform Team's work on Enterprise projects?
```
**Expected behavior**: Should calculate team costs allocated to specific customer projects

## Customer Relationship Questions

### 7. Customer Commitments and Risks
```
What are our top 5 customer commitments and what risks could prevent us from meeting them?
```
**Expected behavior**: Should list customers by ARR and identify their project/SLA risks

### 8. Customer Health Analysis
```
Which Enterprise customers are at risk based on recent events?
```
**Expected behavior**: Should correlate events with success scores and subscription status

## Operational Questions

### 9. Customer Concerns
```
What are the top customer concerns and what is being done to address them?
```
**Expected behavior**: Should map concerns (events) to remediation efforts (projects/teams)

### 10. Team Capacity Impact
```
How does team capacity affect our ability to deliver customer projects on time?
```
**Expected behavior**: Should analyze team utilization vs project status

## Impact Analysis Questions

### 11. Event Cascade Effects
```
How does Disney's recent outage affect their overall relationship with us?
```
**Expected behavior**: Should trace Event → Success Score → Projects → Revenue

### 12. Cross-Customer Patterns
```
Do EA and Disney face similar risks that could impact our quarterly revenue?
```
**Expected behavior**: Should compare risk profiles and calculate combined impact

## Why These Should Trigger Hybrid Search

Each question naturally requires:
1. **Graph traversal**: To connect entities (customers, projects, teams, events)
2. **Semantic analysis**: To understand concepts (risk, impact, concerns, threats)

The system should recognize that answering these questions requires:
- Following relationships in the knowledge graph
- Understanding business concepts and calculations
- Combining factual data with analytical reasoning

## The Problem

If these natural questions don't trigger hybrid search, the issue might be:
1. The agent's prompt doesn't recognize these as requiring graph traversal
2. The routing logic favors vector search as the default
3. The system needs better pattern recognition for business questions

## Recommended Solution

The system should detect patterns like:
- "How much... if..." → Impact analysis requiring relationships
- "What risks..." → Risk assessment across entities
- "Top X customers..." → Ranking with relationship data
- "How does X affect Y" → Clear relationship traversal
- "What is being done..." → Action-entity mapping

These are exactly the types of questions business users ask, and they inherently require both semantic understanding AND relationship traversal.