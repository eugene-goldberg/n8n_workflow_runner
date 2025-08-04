# Grounded Business Questions

This document contains all business questions that have been verified to return grounded answers from the SpyroSolutions Agentic RAG system with LangGraph integration.

**Success Rate**: 66.7% (40 out of 60 questions)  
**Last Verified**: 2025-08-03  
**API Version**: LangGraph Agentic RAG v2.0.0

## Summary by Category

| Category | Grounded Questions | Total Questions | Success Rate |
|----------|-------------------|-----------------|--------------|
| Customer Health | 5 | 5 | 100% |
| Revenue Risk Analysis | 5 | 5 | 100% |
| Customer Commitments & Satisfaction | 4 | 5 | 80% |
| Growth & Expansion | 4 | 5 | 80% |
| Product Performance | 4 | 5 | 80% |
| Strategic Risk Assessment | 4 | 5 | 80% |
| Cost & Profitability | 3 | 5 | 60% |
| Operational Risk | 3 | 5 | 60% |
| Project Delivery | 3 | 5 | 60% |
| Competitive Positioning | 2 | 5 | 40% |
| Roadmap & Delivery Risk | 2 | 5 | 40% |
| Team Performance | 1 | 5 | 20% |

## All Grounded Questions

### Revenue & Customer Health

#### Customer Health (5/5 - 100%)
1. What are the top 5 customers by revenue, and what are their current success scores?
2. Which customers have declining success scores, and what events are driving the decline?
3. How many customers have success scores below 60, and what is their combined ARR?
4. What percentage of customers experienced negative events in the last 90 days?
5. Which customers are at highest risk of churn based on success scores and recent events?

#### Revenue Risk Analysis (5/5 - 100%)
1. How much revenue will be at risk if [Customer X] misses their SLA next month?
2. What percentage of our ARR is dependent on customers with success scores below 70?
3. Which customers generate 80% of our revenue, and what are their current risk profiles?
4. How much revenue is at risk from customers experiencing negative events in the last quarter?
5. What is the projected revenue impact if we miss our roadmap deadlines for committed features?

### Products & Operations

#### Product Performance (4/5 - 80%)
1. Which products have the highest customer satisfaction scores?
2. How many customers use each product, and what is the average subscription value?
3. Which products have the most operational issues impacting customer success?
4. What is the adoption rate of new features released in the last 6 months?

#### Cost & Profitability (3/5 - 60%)
1. How much does it cost to run each product across all regions?
2. How do operational costs impact profitability for our top 10 customers?
3. What is the cost-per-customer for each product, and how does it vary by region?

#### Operational Risk (3/5 - 60%)
1. Which teams are understaffed relative to their project commitments?
2. Which products have the highest operational risk exposure?
3. What percentage of projects are at risk of missing deadlines?

### Strategy & Delivery

#### Strategic Risk Assessment (4/5 - 80%)
1. What are the top risks related to achieving [Objective X]?
2. Which company objectives have the highest number of associated risks?
3. What is the potential revenue impact of our top 5 identified risks?
4. How many high-severity risks are currently without mitigation strategies?

#### Project Delivery (3/5 - 60%)
1. Which projects are critical for maintaining current revenue?
2. How many projects are blocked by operational constraints?
3. What is the success rate of projects by team and product area?

#### Roadmap & Delivery Risk (2/5 - 40%)
1. Which roadmap items are critical for customer retention?
2. What percentage of roadmap items are currently behind schedule?

### Customer & Growth

#### Customer Commitments & Satisfaction (4/5 - 80%)
1. What are the top customer commitments, and what are the current risks to achieving them?
2. What are the top customer concerns, and what is currently being done to address them?
3. How many customers are waiting for features currently on our roadmap?
4. Which customers have unmet SLA commitments in the last quarter?

#### Growth & Expansion (4/5 - 80%)
1. Which customer segments offer the highest growth potential?
2. What products have the best profitability-to-cost ratio for scaling?
3. What features could we develop to increase customer success scores?
4. Which objectives are most critical for achieving our growth targets?

#### Competitive Positioning (2/5 - 40%)
1. How do our SLAs compare to industry standards by product?
2. Which customer segments are we best positioned to serve profitably?

### Organization

#### Team Performance (1/5 - 20%)
1. Which teams support the most revenue-generating products?

## Usage Tips

1. **Placeholder Values**: Questions with placeholders like `[Customer X]` or `[Objective X]` should be replaced with actual entity names from your Neo4j database.

2. **Best Performance**: Questions in the Customer Health and Revenue Risk Analysis categories have 100% success rate and are most reliable.

3. **API Integration**: These questions are optimized for the LangGraph Agentic RAG API running on port 8000.

4. **Response Time**: Average response time is 4.3 seconds per question.

## Technical Details

- **Model**: GPT-3.5-turbo
- **Retrievers**: VectorRetriever, GraphRetriever, HybridRetriever
- **Knowledge Base**: Neo4j with LlamaIndex schema format
- **Entity Count**: 748 entities with embeddings
- **Relationship Types**: Multiple including DELIVERS, HAS_RISK, GENERATES_REVENUE, etc.