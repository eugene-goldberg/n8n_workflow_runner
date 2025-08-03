# Failed Queries: Neo4j Data Availability Investigation Report

## Executive Summary

Investigation of 18 failed queries reveals that **12 queries (67%) have no relevant data** in Neo4j, while **6 queries (33%) have partial or proxy data** that could potentially be used with better query construction or data enrichment.

## Detailed Investigation Results

### 1. Queries with NO DATA in Neo4j (12/18)

These queries failed because the required entities, relationships, or properties do not exist in the database:

#### Q7: What are the projected quarterly revenue trends for the next fiscal year?
- **Missing**: PROJECTION or FORECAST nodes with quarterly data
- **Finding**: No projection/forecast nodes found in the graph
- **Solution Needed**: Add PROJECTION nodes with quarterly breakdowns

#### Q19: What is the correlation between team size and project completion rates?
- **Missing**: PROJECT nodes with completion data
- **Finding**: Found 31 teams (15 with size data) but only PROJECT nodes exist without completion metrics
- **Solution Needed**: Add project_completion_rate property to PROJECT nodes or create PROJECT_COMPLETION events

#### Q25: What percentage of projects are currently over budget?
- **Missing**: budget and actual_cost properties on PROJECT nodes
- **Finding**: PROJECT nodes exist but 0 have budget property
- **Solution Needed**: Add budget and actual_cost properties to PROJECT nodes

#### Q28: How many security incidents have been reported in the last quarter?
- **Missing**: EVENT nodes with type='security_incident'
- **Finding**: Found 1 security-related event but no date filtering capability
- **Solution Needed**: Add more security incident events with proper timestamps

#### Q31: What is the average time from lead to customer conversion?
- **Missing**: LEAD nodes and CONVERTED_TO relationships
- **Finding**: No LEAD entities found (count: 0)
- **Solution Needed**: Create LEAD nodes and track conversion relationships

#### Q32: How many customers are using deprecated features?
- **Missing**: deprecated or is_deprecated property on FEATURE nodes
- **Finding**: 105 features exist, 0 marked deprecated
- **Solution Needed**: Add deprecated flag to FEATURE nodes

#### Q43: What is the trend in customer acquisition costs over time?
- **Missing**: COST nodes with category='acquisition' and time periods
- **Finding**: Found 0 acquisition costs with time data
- **Solution Needed**: Create acquisition cost nodes with period properties

#### Q48: How many days of runway do we have at current burn rate?
- **Missing**: FINANCE or CASH nodes with balance data
- **Finding**: Monthly burn calculated ($8.2M) but no cash/reserves found
- **Solution Needed**: Add CASH or FINANCE nodes with current_balance

#### Q52: What percentage of revenue is recurring vs one-time?
- **Missing**: source property set to 'recurring' or 'one-time' on REVENUE nodes
- **Finding**: 44 REVENUE nodes exist but source property is not populated
- **Solution Needed**: Update REVENUE nodes with source='recurring' or 'one-time'

#### Q53: Which marketing channels have the highest ROI?
- **Missing**: MARKETING_CHANNEL nodes
- **Finding**: No marketing-related entities in the graph
- **Solution Needed**: Create MARKETING_CHANNEL nodes with cost/revenue relationships

#### Q58: What percentage of our codebase has technical debt?
- **Missing**: CODEBASE or TECHNICAL_DEBT nodes
- **Finding**: No technical debt metrics found
- **Solution Needed**: Create CODEBASE nodes with technical_debt_percentage

#### Q20: How many critical milestones are at risk of being missed this quarter?
- **Missing**: MILESTONE nodes with risk/status properties
- **Finding**: Found 6 MILESTONE nodes but no ROADMAPITEM nodes or risk indicators
- **Solution Needed**: Add status and at_risk properties to MILESTONE nodes

### 2. Queries with PARTIAL/PROXY DATA (6/18)

These queries have some relevant data but need better properties or relationships:

#### Q12: What is the average time to resolve critical customer issues by product?
- **Has**: 2 support escalation events with timestamps
- **Missing**: resolution_date or closed_date properties
- **Solution**: Add resolution_date to EVENT nodes

#### Q26: Which teams have the highest employee satisfaction scores?
- **Has**: 9 teams with satisfaction_score property (avg: 4.12)
- **Missing**: More teams need satisfaction scores
- **Solution**: Query can work with existing data

#### Q34: Which SLAs are most frequently violated?
- **Has**: 16 SLA nodes exist
- **Missing**: EVENT nodes with type='sla_violation'
- **Solution**: Create SLA violation events linked to SLA nodes

#### Q39: What is the average revenue per employee across different departments?
- **Has**: 15 teams with employee count (total: 70 employees)
- **Missing**: Direct revenue attribution to teams
- **Solution**: Create GENERATES_REVENUE relationships from teams

#### Q44: How many high-value opportunities are in the pipeline?
- **Has**: 24 EXPANSION_OPPORTUNITY nodes
- **Missing**: value or pipeline_stage properties
- **Solution**: Add value property to opportunities

#### Q51: How many critical dependencies exist in our technology stack?
- **Has**: 19 features with adoption_rate (used as proxy)
- **Missing**: Clear definition of what constitutes a dependency
- **Solution**: Query works but needs clearer business logic

## Recommendations

### Immediate Actions (Quick Wins)
1. **Update existing REVENUE nodes** with source='recurring' or 'one-time' (fixes Q52)
2. **Add deprecated flag** to some FEATURE nodes (fixes Q32)
3. **Add resolution_date** to EVENT nodes where type='support_escalation' (fixes Q12)
4. **Add value property** to EXPANSION_OPPORTUNITY nodes (improves Q44)

### Medium-term Data Additions
1. **Create LEAD nodes** and conversion tracking (fixes Q31)
2. **Create MARKETING_CHANNEL nodes** with ROI data (fixes Q53)
3. **Add budget properties** to PROJECT nodes (fixes Q25)
4. **Create CASH/FINANCE nodes** for runway calculation (fixes Q48)

### Long-term Enhancements
1. **Add projection/forecast nodes** for revenue trends (fixes Q7)
2. **Create technical debt tracking** entities (fixes Q58)
3. **Enhance PROJECT nodes** with completion metrics (fixes Q19)
4. **Build time-series cost tracking** for trends (fixes Q43)

## Conclusion

The investigation reveals that most failed queries (67%) lack the necessary data in Neo4j. However, with targeted data additions and property enhancements, all 18 queries could be made functional. The recommendations above provide a roadmap for achieving >83% query success rate.