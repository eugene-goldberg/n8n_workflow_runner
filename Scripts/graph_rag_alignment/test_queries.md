# Enhanced Graph RAG Test Queries

This document contains test queries to demonstrate the enhanced Graph RAG capabilities after implementing the semantic model alignment.

## Entity-Based Queries

### 1. Subscription and Revenue Queries
```
"What is the total ARR from all Enterprise customers?"
"Show me all customers with subscriptions worth over 1 million ARR"
"Which products contribute most to our total revenue?"
```

### 2. Customer Success Queries
```
"Which customers have a success score below 80 and what are their risk factors?"
"Show me the trend of customer success scores for our top 3 customers"
"How do recent events impact customer success scores?"
```

### 3. Project Management Queries
```
"List all at-risk projects with their completion percentage and assigned teams"
"Which teams are over 85% capacity and what projects are they working on?"
"Show me projects for Disney and their current status"
```

### 4. Team Performance Queries
```
"Which team has the highest utilization and what are they working on?"
"Show me all teams working on Enterprise customer projects"
"What is the average team capacity across all teams?"
```

### 5. Event Analysis Queries
```
"Show me all critical events in the last 30 days and their impact"
"Which customers experienced SLA breaches recently?"
"What events affected Disney's success score?"
```

## Relationship-Based Queries (Graph Search)

### 1. Customer 360 View
```
"Give me a complete view of Disney including their subscription, projects, events, and success score"
"Show me everything about Netflix - their products, teams working for them, and recent events"
```

### 2. Cross-Entity Relationships
```
"Which teams are working on projects for customers with ARR over 1 million?"
"Show me the relationship between at-risk projects and customer success scores"
"Which products are used by customers with declining success scores?"
```

### 3. Impact Analysis
```
"How do SLA breaches impact customer retention objectives?"
"Which risks threaten our Q1 2025 objectives?"
"Show me the chain of impact from events to success scores to ARR"
```

### 4. Resource Allocation
```
"Which teams are working on multiple at-risk projects?"
"Show me products with high operational costs and their customer base"
"How is team capacity distributed across Enterprise vs Pro customers?"
```

## Hybrid Search Queries

### 1. Complex Business Questions
```
"Analyze the relationship between Disney and EA including their subscriptions, projects, and teams"
"Which Enterprise customers are at risk of churn based on their success scores, recent events, and project status?"
"Show me the correlation between team utilization and project success rates"
```

### 2. Financial Analysis
```
"What is the total operational cost for products used by our top 3 revenue customers?"
"How much ARR is at risk from customers with declining success scores?"
"Which products have the best profit margin considering their operational costs and revenue?"
```

### 3. Strategic Planning
```
"Based on current team capacity and project status, which Q2 2025 roadmap items are at risk?"
"Which customers should we prioritize based on their ARR, success scores, and project engagement?"
"Show me opportunities to improve customer retention based on event patterns and success scores"
```

## Expected Search Type Indicators

- **Vector Search (🔍)**: General questions about single entities or metrics
- **Graph Search (🕸️)**: Questions about relationships between specific named entities
- **Hybrid Search (🔄)**: Complex questions requiring both semantic understanding and relationship traversal

## Testing Instructions

1. Access the demo interface at http://srv928466.hstgr.cloud:8082/
2. Try each query category to see different search types in action
3. Observe the tool transparency showing which search method was used
4. Note response times and accuracy for different query types

## Success Metrics

- Graph search triggers when querying relationships between named entities
- Vector search handles general semantic queries efficiently
- Hybrid search combines both for complex business questions
- Response times remain under 500ms for most queries
- Tool transparency clearly indicates search methods used