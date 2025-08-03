# Neo4j Business Entities and Relationships Documentation

## Overview

This document provides a comprehensive catalog of all business entities (nodes) and relationships (edges) in the SpyroSolutions Neo4j database, regardless of schema type. The database contains **1,257 nodes** and uses multiple schema patterns, primarily LlamaIndex format.

## Schema Distribution

- **LlamaIndex Schema**: 943 nodes (74%) - Uses `__Entity__` and `__Node__` labels
- **Other/Standalone**: 309 nodes (25%) - Document, POC, FeatureRequest, etc.
- **SpyroRAG Schema**: 5 nodes (<1%) - Original format using plain labels

## Core Business Entities

### 1. Customer Entities

#### CUSTOMER (46 nodes)
Represents client organizations using SpyroSolutions products.

**Key Properties:**
- `name`: Company name (e.g., "TechCorp", "FinanceHub")
- `subscription_value`: Annual subscription amount (e.g., "$2M/year")
- `size`: Company size category (Enterprise, SMB)
- `industry`: Business sector
- `contract_length`: Duration in months
- `usage_growth`: Percentage growth in usage
- `subscription_start_date`: When they became a customer

**Example Customers:**
- TechCorp (Enterprise, $8M/year)
- FinanceHub (Enterprise, $6M/year)
- GlobalRetail (Enterprise, $5M/year)
- CloudFirst (Mid-Market, $3M/year)

#### CUSTOMER_SUCCESS_SCORE (15 nodes)
Tracks customer health metrics.

**Properties:**
- `score`: Numeric health score (0-100)
- `trend`: Direction of score change
- `factors`: Contributing factors to the score

### 2. Product Entities

#### PRODUCT (37 nodes)
SpyroSolutions product offerings.

**Key Properties:**
- `name`: Product name
- `operational_cost`: Cost to run the product
- `satisfaction_score`: Customer satisfaction rating
- `nps_score`: Net Promoter Score

**Core Products:**
- SpyroCloud (Cloud infrastructure platform)
- SpyroAI (AI/ML capabilities)
- SpyroSecure (Security solutions)

#### FEATURE (102 nodes)
Product capabilities and functionalities.

**Properties:**
- `name`: Feature name
- `adoption_rate`: Percentage of customers using it
- `launch_date`: When feature was released
- `status`: Current status (delivered, in_progress, planned)
- `delivery_status`: For promised features

**Notable Features:**
- Multi-region deployment
- AI-powered analytics
- Real-time dashboards
- Enhanced API rate limits

### 3. Financial Entities

#### REVENUE (42 nodes)
Revenue tracking across different dimensions.

**Properties:**
- `amount`: Revenue value
- `type`: Revenue category
- `period`: Time period

#### COST (65 nodes)
Operational and infrastructure costs.

**Properties:**
- `amount`: Cost value
- `type`: Cost category (operational, infrastructure)
- `region`: Geographic region
- `period`: Time period (annual, monthly)

#### SUBSCRIPTION (19 nodes)
Customer subscription details.

**Properties:**
- `value`: Subscription amount
- `term`: Contract term
- `renewal_date`: Next renewal date

#### ARR (Annual Recurring Revenue)
Tracks annual recurring revenue metrics.

### 4. Organizational Entities

#### TEAM (31 nodes)
Internal teams at SpyroSolutions.

**Key Properties:**
- `name`: Team name
- `size`: Number of team members
- `focus_area`: Primary responsibility
- `operational_cost`: Team's operational cost
- `attrition_rate`: Employee turnover percentage
- `satisfaction_score`: Team satisfaction metric

**Core Teams:**
- Cloud Platform Team
- AI Research Team
- Security Team
- Customer Success Team
- DevOps Team

#### PERSON (40 nodes)
Individual team members and stakeholders.

**Properties:**
- `name`: Person's name
- `role`: Job title/position
- `team`: Associated team

### 5. Project & Development Entities

#### PROJECT (50 nodes)
Active initiatives and development efforts.

**Properties:**
- `name`: Project name
- `status`: Current status
- `priority`: Project priority
- `deadline`: Target completion date

**Example Projects:**
- Cloud Migration
- AI Enhancement
- Security Audit
- Win-back campaigns for lost customers

#### ROADMAP_ITEM (30 nodes)
Planned product enhancements.

**Properties:**
- `name`: Feature/capability name
- `quarter`: Target delivery quarter
- `status`: Planning status

### 6. Risk & Compliance Entities

#### RISK (76 nodes)
Business and operational risks.

**Properties:**
- `name`: Risk description
- `severity`: Impact level (Low, Medium, High, Critical)
- `type`: Risk category (operational, financial, technical)
- `probability`: Likelihood of occurrence
- `mitigation_status`: Current mitigation efforts

**Risk Categories:**
- Customer churn risks
- Technical/operational risks
- Market/competitive risks
- Compliance risks

#### OBJECTIVE (51 nodes)
Business goals and OKRs.

**Properties:**
- `name`: Objective description
- `target`: Measurable target
- `status`: Achievement status
- `quarter`: Target quarter

**Key Objectives:**
- Market Expansion
- Customer Retention
- Product Innovation
- Revenue Growth

### 7. Customer Experience Entities

#### CONCERN (Multiple nodes)
Customer issues and concerns.

**Properties:**
- `type`: Concern category
- `description`: Detailed description
- `priority`: Urgency level
- `status`: Resolution status
- `created_date`: When reported

#### SLA (Service Level Agreement)
Customer service commitments.

**Properties:**
- `type`: SLA tier
- `uptime_target`: Availability commitment
- `response_time_target`: Performance commitment
- `penalty_percentage`: Penalty for breach

#### SupportTicket (25 nodes)
Customer support requests.

**Properties:**
- `id`: Ticket identifier
- `type`: Issue type
- `priority`: Urgency level
- `status`: Resolution status
- `customer`: Associated customer

### 8. Operational Entities

#### EVENT (22 nodes)
System events and incidents.

**Properties:**
- `type`: Event category
- `description`: Event details
- `severity`: Impact level
- `date`: When occurred
- `impact`: Business impact

#### EXPANSION_OPPORTUNITY (24 nodes)
Upsell and growth opportunities.

**Properties:**
- `value`: Potential revenue
- `product`: Target product
- `probability`: Success likelihood
- `expected_close_date`: Target date

#### POC (Proof of Concept)
Trial implementations for prospects.

**Properties:**
- `company`: Prospect name
- `product`: Product being evaluated
- `stage`: Current stage
- `potential_value`: Deal size

## Key Relationships

### Customer Relationships
- `SUBSCRIBES_TO`: Customer → Subscription (19 relationships)
- `USES`: Customer → Product (132 relationships)
- `HAS_SUCCESS_SCORE`: Customer → CustomerSuccessScore
- `HAS_CONCERN`: Customer → Concern
- `HAS_SLA`: Customer → SLA
- `HAS_EXPANSION_OPPORTUNITY`: Customer → ExpansionOpportunity
- `WAITING_FOR`: Customer → Feature (for promised features)
- `PROMISED_FEATURE`: Customer → Feature

### Product Relationships
- `HAS_FEATURE`: Product → Feature (97 relationships)
- `HAS_COST`: Product → Cost
- `GENERATES`: Various → Revenue (42 relationships)
- `SUPPORTED_BY`: Product → Team

### Team Relationships
- `WORKS_ON`: Team → Project
- `SUPPORTS`: Team → Product/Customer
- `HAS_MEMBER`: Team → Person
- `RESPONSIBLE_FOR`: Team → RoadmapItem
- `ADDRESSING`: Team → Concern

### Risk & Objective Relationships
- `AFFECTS`: Risk → Objective (31 relationships)
- `HAS_OBJECTIVE`: Various → Objective (50 relationships)
- `HAS_RISK`: Customer/Project → Risk

### Development Relationships
- `IMPLEMENTS`: RoadmapItem → Feature
- `DEPENDS_ON`: Project → Project (dependencies)
- `ON_ROADMAP`: Feature → RoadmapItem

### Financial Relationships
- `GENERATES_REVENUE`: Various → Revenue
- `HAS_OPERATIONAL_COST`: Team/Product → Cost

## Data Completeness Issues

### Missing Data for Business Questions:
1. **Marketing/Campaign Data**: No dedicated campaign entities or conversion metrics
2. **Upsell Campaign Data**: Only 2 mentions found (as revenue and project)
3. **Proactive vs Reactive Tickets**: No categorization in support tickets
4. **Feature Request Patterns**: Limited feature request entities (5 nodes)
5. **Competitive Analysis**: Few competitor entities or comparisons

### Schema Inconsistencies:
1. Multiple schema patterns (LlamaIndex vs SpyroRAG vs standalone)
2. Some entities have both schema versions (e.g., COMMITMENT vs Commitment)
3. Relationship naming inconsistencies (HAS_ prefix vs direct names)

## Recommendations

1. **Schema Standardization**: Migrate all entities to a single schema format
2. **Add Missing Entities**:
   - Marketing campaigns with conversion metrics
   - Competitive intelligence data
   - Detailed support categorization
   - Customer journey stages
3. **Enhance Relationships**:
   - Link campaigns to revenue
   - Connect features to customer value
   - Track team impact on customer success
4. **Data Enrichment**:
   - Add more operational metrics
   - Include time-series data for trends
   - Capture customer feedback systematically

## Query Optimization Tips

When querying this database:
1. Always check for both schema formats (e.g., `Customer` and `['__Entity__', '__Node__', 'CUSTOMER']`)
2. Use flexible label matching: `WHERE 'CUSTOMER' IN labels(n) OR ('__Entity__' IN labels(n) AND 'CUSTOMER' IN labels(n))`
3. Be aware that some properties may be null or missing
4. Consider using `OPTIONAL MATCH` for relationships that may not exist