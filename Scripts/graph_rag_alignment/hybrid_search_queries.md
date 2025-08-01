# Top 5 Hybrid Search Queries for Enhanced Graph RAG

These queries are specifically designed to trigger hybrid search by combining semantic understanding with graph relationship traversal.

## 1. Revenue Impact Analysis
```
How much revenue will be at risk if Disney's current SLA violations continue for another quarter, and which teams need to be allocated to prevent this?
```
**Why Hybrid**: Requires understanding SLA violation concepts (vector) + traversing Disney → Events → Success Score → Subscription → Teams relationships (graph)

## 2. Cross-Customer Risk Correlation
```
Analyze the correlation between customer success scores and project delays across Disney, EA, and Netflix, and identify which operational costs could be reduced to improve profitability while maintaining service quality.
```
**Why Hybrid**: Needs semantic understanding of correlation/profitability concepts (vector) + multi-entity relationship traversal across customers, projects, scores, and costs (graph)

## 3. Strategic Objective Achievement
```
What is preventing us from achieving our $10M ARR target, considering the current status of Enterprise customer projects, team capacity constraints, and recent performance events?
```
**Why Hybrid**: Requires understanding business concepts like "preventing achievement" (vector) + traversing Objective → Risks → Customers → Projects → Teams → Events (graph)

## 4. Customer Health Prediction
```
Based on the pattern of events affecting Disney and their declining success score, predict which other Enterprise customers might face similar issues and what preventive actions their assigned teams should take.
```
**Why Hybrid**: Needs pattern recognition and prediction concepts (vector) + traversing similar customers with comparable event patterns and team assignments (graph)

## 5. Comprehensive Business Impact
```
Show me how EA's recent security alert cascades through their subscription value, affects our Q1 revenue targets, impacts the Integration Team's capacity, and threatens our customer retention objectives.
```
**Why Hybrid**: Requires understanding cascading impacts (vector) + complex multi-hop traversal: EA → Event → Subscription → ARR → Objectives + EA → Projects → Teams (graph)

## Usage Instructions

1. Copy any of these queries exactly as written
2. Paste into the demo interface at http://srv928466.hstgr.cloud:8082/
3. Observe the tool transparency showing both vector_search and graph_search being used
4. Note the comprehensive response combining semantic insights with relationship data

## Expected Behavior

Each query should trigger:
- 🔍 **Vector Search**: For semantic concepts (risk, correlation, prevention, prediction, cascade)
- 🕸️ **Graph Search**: For entity relationships (customer → project → team, event → score → revenue)
- 🔄 **Result**: Hybrid search indicator showing both tools were used

## Key Elements That Trigger Hybrid Search

1. **Named Entities**: Disney, EA, Netflix, specific teams, objectives
2. **Relationship Words**: "affects", "impacts", "cascades", "correlation", "pattern"
3. **Business Concepts**: Revenue risk, profitability, service quality, prevention
4. **Complex Analysis**: Prediction, correlation, multi-factor impact
5. **Time Elements**: "another quarter", "recent", "current status"