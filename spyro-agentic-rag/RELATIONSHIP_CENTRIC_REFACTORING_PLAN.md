# Relationship-Centric Graph Model Refactoring Plan

## Executive Summary
Transform our property-centric graph model to a relationship-centric model that aligns with LLM strengths in graph traversal, targeting >85% query success rate.

## Phase 1: High-Impact Entity Refactoring (Immediate)

### Target Entities
Focus on the 3 patterns causing most failures:

1. **MARKETING_CHANNEL** (Q53)
   - Current: Properties for roi, cost, revenue
   - Issue: LLM looks for non-existent relationships
   
2. **PROJECTION** (Q7)
   - Current: Properties for quarter, revenue
   - Issue: LLM over-parses temporal data
   
3. **REVENUE** (Q52)
   - Current: Property for source type
   - Issue: LLM traverses through customers unnecessarily

### Refactoring Approach

#### 1. MARKETING_CHANNEL Transformation
```cypher
// Current structure
(m:MARKETING_CHANNEL {
    name: 'Email Campaigns',
    roi: 700,
    total_cost: 150000,
    attributed_revenue: 1200000,
    period: 'YTD 2024'
})

// New structure
(m:MARKETING_CHANNEL {name: 'Email Campaigns'})
(m)-[:HAS_COST {period: 'YTD 2024'}]->(c:COST {amount: 150000})
(m)-[:GENERATES]->(r:REVENUE {amount: 1200000})
(m)-[:ACHIEVES]->(p:PERFORMANCE_METRIC {type: 'ROI', value: 700})
```

#### 2. PROJECTION Transformation
```cypher
// Current structure
(p:PROJECTION {
    quarter: 'Q1 2025',
    projected_revenue: 22500000,
    confidence: 0.85
})

// New structure
(p:PROJECTION {name: 'Q1 2025 Revenue Projection'})
(p)-[:FOR_PERIOD]->(q:QUARTER {name: 'Q1', year: 2025})
(p)-[:PROJECTS]->(m:METRIC {type: 'revenue', value: 22500000, confidence: 0.85})
```

#### 3. REVENUE Transformation
```cypher
// Current structure
(r:REVENUE {
    amount: 8000000,
    source: 'recurring'
})

// New structure
(r:REVENUE {amount: 8000000})
(r)-[:HAS_TYPE]->(t:REVENUE_TYPE {name: 'recurring'})
```

## Phase 2: Implementation Steps

### Step 1: Create New Schema
1. Define new node types: PERFORMANCE_METRIC, QUARTER, REVENUE_TYPE
2. Define relationship types: HAS_COST, GENERATES, ACHIEVES, FOR_PERIOD, PROJECTS, HAS_TYPE
3. Ensure all new nodes have __Entity__ label for LlamaIndex compatibility

### Step 2: Data Migration
1. Create new nodes and relationships alongside existing structure
2. Verify data integrity
3. Update agent context
4. Test queries
5. Remove old properties once validated

### Step 3: Context Updates
1. Update neo4j_data_model_context_complete.py
2. Add relationship patterns to query hints
3. Update system prompt to emphasize traversal

## Phase 3: Validation Metrics

### Success Criteria
1. Q53 (Marketing ROI) returns specific percentages
2. Q7 (Projections) returns quarterly data without parsing
3. Q52 (Revenue split) calculates percentages correctly

### Expected Improvements
- Query simplicity: Complex parsing eliminated
- Success rate: 71.7% → 85%+ (12+ additional queries fixed)
- Query speed: Faster due to natural traversal patterns

## Phase 4: Extended Refactoring (If Successful)

### Additional Candidates
1. TEAM monthly_cost → (TEAM)-[:HAS_COST]->(COST)
2. FEATURE adoption_rate → (FEATURE)-[:HAS_ADOPTION]->(METRIC)
3. RISK impact_amount → (RISK)-[:HAS_IMPACT]->(FINANCIAL_IMPACT)

## Implementation Timeline
- Phase 1: Immediate (today)
- Phase 2: Test and validate
- Phase 3: Measure improvements
- Phase 4: Based on results

## Risk Mitigation
1. Keep original structure during migration
2. Test incrementally
3. Rollback plan: Revert relationships to properties
4. Monitor query performance

## Expected Outcome
By aligning our model with LLM strengths in relationship traversal, we expect:
- Natural query generation
- Higher success rates
- Maintained autonomy
- Better maintainability