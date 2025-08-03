# Neo4j Investigation Report for Failed Queries

## Summary

- Total failed queries: 18
- Queries with partial/proxy data: 6
- Queries with no relevant data: 12

## Detailed Findings

### Query 7: What are the projected quarterly revenue trends for the next fiscal year?

**Status**: No Data

**Missing**: PROJECTION or FORECAST nodes with quarterly data

**Finding**: No projection/forecast nodes found in the graph

---

### Query 12: What is the average time to resolve critical customer issues by product?

**Status**: Has Partial Data

**Missing**: resolution_date or closed_date properties on EVENT nodes

**Finding**: Found 2 support events but no resolution dates/times

---

### Query 19: What is the correlation between team size and project completion rates?

**Status**: No Data

**Missing**: PROJECT nodes and project completion data

**Finding**: Found 31 teams (with size data: 15) but only 50 PROJECT nodes

---

### Query 20: How many critical milestones are at risk of being missed this quarter?

**Status**: No Data

**Missing**: MILESTONE nodes with risk/status properties

**Finding**: Found 0 ROADMAPITEM nodes but 6 MILESTONE nodes

---

### Query 25: What percentage of projects are currently over budget?

**Status**: No Data

**Missing**: budget and actual_cost properties on PROJECT nodes

**Finding**: PROJECT nodes exist but 0 have budget property

---

### Query 26: Which teams have the highest employee satisfaction scores?

**Status**: Has Partial Data

**Missing**: EMPLOYEE nodes or employee_satisfaction properties

**Finding**: Found 9 teams with satisfaction_score (avg: 4.122222222222222)

---

### Query 28: How many security incidents have been reported in the last quarter?

**Status**: No Data

**Missing**: EVENT nodes with type='security_incident'

**Finding**: Checked all events, found 1 security-related (types: ['security_incident'])

---

### Query 31: What is the average time from lead to customer conversion?

**Status**: No Data

**Missing**: LEAD nodes and CONVERTED_TO relationships

**Finding**: No LEAD entities found (count: 0)

---

### Query 32: How many customers are using deprecated features?

**Status**: No Data

**Missing**: deprecated or is_deprecated property on FEATURE nodes

**Finding**: 105 features exist, 0 marked deprecated. Props: ['is_new_feature', 'adoption_rate', 'name', 'released_timeframe', 'triplet_source_id', 'embedding', 'id', 'active_users']

---

### Query 34: Which SLAs are most frequently violated?

**Status**: Has Partial Data

**Missing**: EVENT nodes with type='sla_violation'

**Finding**: Found 16 SLA nodes but 0 violation events

---

### Query 39: What is the average revenue per employee across different departments?

**Status**: Has Partial Data

**Missing**: Direct revenue attribution to teams/departments

**Finding**: Found 15 teams with employee data (total: 70)

---

### Query 43: What is the trend in customer acquisition costs over time?

**Status**: No Data

**Missing**: COST nodes with category='acquisition' and time periods

**Finding**: Found 0 acquisition costs. Periods: []

---

### Query 44: How many high-value opportunities are in the pipeline?

**Status**: Has Partial Data

**Missing**: value or stage properties on opportunities

**Finding**: Found 24 EXPANSION_OPPORTUNITY nodes (used as proxy)

---

### Query 48: How many days of runway do we have at current burn rate?

**Status**: No Data

**Missing**: FINANCE or CASH nodes with balance data

**Finding**: Monthly burn: $8200000.0, but no cash/reserves found. Checked: []

---

### Query 51: How many critical dependencies exist in our technology stack?

**Status**: Has Partial Data

**Missing**: Clear definition of 'critical dependency'

**Finding**: Using 19 features with adoption_rate as proxy for dependencies

---

### Query 52: What percentage of revenue is recurring vs one-time?

**Status**: No Data

**Missing**: source property set to 'recurring' or 'one-time' on REVENUE nodes

**Finding**: REVENUE nodes: 44, but source values are: []

---

### Query 53: Which marketing channels have the highest ROI?

**Status**: No Data

**Missing**: MARKETING_CHANNEL nodes

**Finding**: No marketing-related labels found. Checked: []

---

### Query 58: What percentage of our codebase has technical debt?

**Status**: No Data

**Missing**: CODEBASE or TECHNICAL_DEBT nodes

**Finding**: No technical debt metrics found. Nodes with debt properties: []

---

