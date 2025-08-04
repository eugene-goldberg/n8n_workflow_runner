"""Enhanced Cypher queries for complex business questions"""

ENHANCED_CYPHER_QUERIES = {
    # Revenue and ARR Percentage Calculations
    "arr_percentage_by_score": """
        // Calculate percentage of ARR from customers with specific success scores
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score < $score_threshold
        WITH c, css.score as score
        MATCH (c)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH sum(s.amount * 12) as at_risk_arr
        MATCH (c2:__Entity__:CUSTOMER)-[:PAYS]->(s2:__Entity__:SUBSCRIPTION)
        WITH at_risk_arr, sum(s2.amount * 12) as total_arr
        RETURN 
            at_risk_arr as arr_at_risk,
            total_arr as total_arr,
            round(at_risk_arr * 100.0 / total_arr, 2) as percentage_at_risk
    """,
    
    "top_revenue_customers": """
        // Find customers that generate X% of revenue with risk profiles
        MATCH (c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH c, sum(s.amount * 12) as customer_arr
        ORDER BY customer_arr DESC
        WITH collect({customer: c, arr: customer_arr}) as all_customers, sum(customer_arr) as total_arr
        WITH all_customers, total_arr, total_arr * $target_percentage / 100.0 as target_revenue
        UNWIND range(0, size(all_customers)-1) as i
        WITH all_customers[0..i+1] as top_customers, 
             all_customers[i] as current,
             total_arr,
             target_revenue
        WITH top_customers, total_arr, 
             reduce(s = 0, cust IN top_customers | s + cust.arr) as cumulative_arr
        WHERE cumulative_arr >= target_revenue
        UNWIND top_customers as tc
        WITH tc.customer as customer, tc.arr as arr, total_arr
        MATCH (customer)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        OPTIONAL MATCH (customer)-[:EXPERIENCED]->(e:__Entity__:EVENT)
        WHERE e.impact = 'negative' AND e.timestamp > datetime() - duration({days: 90})
        WITH customer, arr, css.score as success_score, 
             count(distinct e) as negative_events, total_arr
        RETURN 
            customer.name as customer_name,
            arr as annual_revenue,
            round(arr * 100.0 / total_arr, 2) as revenue_percentage,
            success_score,
            negative_events,
            CASE 
                WHEN success_score < 60 OR negative_events > 2 THEN 'High Risk'
                WHEN success_score < 70 OR negative_events > 0 THEN 'Medium Risk'
                ELSE 'Low Risk'
            END as risk_profile
        ORDER BY annual_revenue DESC
    """,
    
    "customers_with_negative_events_percentage": """
        // Calculate percentage of customers with negative events
        MATCH (c:__Entity__:CUSTOMER)
        WITH count(distinct c) as total_customers
        MATCH (c2:__Entity__:CUSTOMER)-[:EXPERIENCED]->(e:__Entity__:EVENT)
        WHERE e.impact = 'negative' AND e.timestamp > datetime() - duration({days: $days})
        WITH count(distinct c2) as customers_with_events, total_customers
        RETURN 
            customers_with_events,
            total_customers,
            round(customers_with_events * 100.0 / total_customers, 2) as percentage_with_events
    """,
    
    "operational_cost_impact": """
        // Analyze operational costs impact on top customers' profitability
        MATCH (c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH c, sum(s.amount * 12) as customer_arr
        ORDER BY customer_arr DESC
        LIMIT 10
        MATCH (c)-[:USES]->(p:__Entity__:PRODUCT)
        OPTIONAL MATCH (p)<-[:SUPPORTS]-(t:__Entity__:TEAM)
        OPTIONAL MATCH (t)-[:HAS_COST]->(cost:__Entity__:OPERATIONAL_COST)
        WITH c, customer_arr, p, 
             sum(coalesce(cost.amount, 0)) as operational_costs
        RETURN 
            c.name as customer_name,
            customer_arr as annual_revenue,
            sum(operational_costs) as total_operational_costs,
            customer_arr - sum(operational_costs) as gross_profit,
            round((customer_arr - sum(operational_costs)) * 100.0 / customer_arr, 2) as profit_margin
        ORDER BY annual_revenue DESC
    """,
    
    "team_cost_to_revenue_ratio": """
        // Calculate operational costs vs revenue supported for each team
        MATCH (t:__Entity__:TEAM)
        OPTIONAL MATCH (t)-[:HAS_COST]->(cost:__Entity__:OPERATIONAL_COST)
        WITH t, sum(coalesce(cost.amount, 0)) as team_costs
        OPTIONAL MATCH (t)-[:SUPPORTS]->(p:__Entity__:PRODUCT)<-[:USES]-(c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH t, team_costs, sum(coalesce(s.amount * 12, 0)) as supported_revenue
        WHERE team_costs > 0 OR supported_revenue > 0
        RETURN 
            t.name as team_name,
            team_costs as operational_costs,
            supported_revenue as revenue_supported,
            CASE 
                WHEN supported_revenue > 0 
                THEN round(team_costs * 100.0 / supported_revenue, 2) 
                ELSE null 
            END as cost_to_revenue_percentage
        ORDER BY cost_to_revenue_percentage DESC NULLS LAST
    """,
    
    "customer_churn_risk_analysis": """
        // Identify customers at highest risk of churn
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score < 70
        OPTIONAL MATCH (c)-[:EXPERIENCED]->(e:__Entity__:EVENT)
        WHERE e.impact = 'negative' AND e.timestamp > datetime() - duration({days: 90})
        WITH c, css, count(distinct e) as recent_negative_events
        OPTIONAL MATCH (c)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
        WHERE com.status IN ['at_risk', 'delayed']
        WITH c, css, recent_negative_events, count(distinct com) as at_risk_commitments
        OPTIONAL MATCH (c)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH c, css, recent_negative_events, at_risk_commitments, 
             sum(s.amount * 12) as arr
        WHERE css.score < 60 OR recent_negative_events > 2 OR at_risk_commitments > 0
        RETURN 
            c.name as customer_name,
            css.score as success_score,
            css.trend as score_trend,
            recent_negative_events,
            at_risk_commitments,
            arr as annual_revenue,
            CASE
                WHEN css.score < 50 AND recent_negative_events > 1 THEN 'Critical'
                WHEN css.score < 60 OR recent_negative_events > 2 THEN 'High'
                WHEN css.score < 70 OR at_risk_commitments > 0 THEN 'Medium'
                ELSE 'Low'
            END as churn_risk_level
        ORDER BY 
            CASE churn_risk_level
                WHEN 'Critical' THEN 1
                WHEN 'High' THEN 2
                WHEN 'Medium' THEN 3
                ELSE 4
            END,
            arr DESC
    """,
    
    "projected_revenue_impact_roadmap": """
        // Calculate revenue impact of missing roadmap deadlines
        MATCH (ri:__Entity__:ROADMAP_ITEM)
        WHERE ri.status IN ['behind_schedule', 'at_risk']
        OPTIONAL MATCH (ri)<-[:DEPENDS_ON]-(com:__Entity__:COMMITMENT)<-[:HAS_COMMITMENT]-(c:__Entity__:CUSTOMER)
        OPTIONAL MATCH (c)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH ri, 
             count(distinct com) as dependent_commitments,
             count(distinct c) as affected_customers,
             sum(coalesce(s.amount * 12, 0)) as revenue_at_risk
        RETURN 
            sum(revenue_at_risk) as total_revenue_at_risk,
            sum(dependent_commitments) as total_commitments_affected,
            sum(affected_customers) as total_customers_affected,
            collect(distinct ri.name) as delayed_items
    """,
    
    "top_customer_commitments_and_risks": """
        // Get top customer commitments and their risks
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
        WHERE com.priority IN ['high', 'critical']
        OPTIONAL MATCH (com)-[:DEPENDS_ON]->(ri:__Entity__:ROADMAP_ITEM)
        OPTIONAL MATCH (com)-[:AT_RISK_FROM]->(r:__Entity__:RISK)
        WITH c, com, 
             collect(distinct ri.name + ' (' + ri.status + ')') as dependencies,
             collect(distinct r.description) as risks
        RETURN 
            c.name as customer_name,
            com.name as commitment,
            com.status as commitment_status,
            com.priority as priority,
            dependencies,
            risks,
            CASE 
                WHEN com.status IN ['at_risk', 'delayed'] THEN 'High Risk'
                WHEN size(risks) > 0 THEN 'Medium Risk'
                ELSE 'Low Risk'
            END as risk_level
        ORDER BY 
            CASE com.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                ELSE 3
            END,
            CASE risk_level
                WHEN 'High Risk' THEN 1
                WHEN 'Medium Risk' THEN 2
                ELSE 3
            END
        LIMIT 20
    """,
    
    "features_promised_to_customers": """
        // Show features promised to customers and delivery status
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com:__Entity__:COMMITMENT)
        WHERE com.type = 'feature'
        OPTIONAL MATCH (com)-[:DEPENDS_ON]->(f:__Entity__:FEATURE)
        OPTIONAL MATCH (f)-[:PART_OF_ROADMAP]->(ri:__Entity__:ROADMAP_ITEM)
        WITH c, com, f, ri
        RETURN 
            c.name as customer_name,
            com.name as commitment_description,
            f.name as feature_name,
            ri.status as roadmap_status,
            ri.target_date as target_delivery,
            com.promise_date as promised_date,
            CASE
                WHEN ri.status = 'completed' THEN 'Delivered'
                WHEN ri.status = 'in_progress' THEN 'In Development'
                WHEN ri.status = 'behind_schedule' THEN 'Delayed'
                WHEN ri.status = 'at_risk' THEN 'At Risk'
                ELSE 'Planned'
            END as delivery_status,
            CASE
                WHEN ri.target_date > com.promise_date THEN 'Will Miss Deadline'
                ELSE 'On Track'
            END as deadline_risk
        ORDER BY 
            CASE delivery_status
                WHEN 'Delayed' THEN 1
                WHEN 'At Risk' THEN 2
                WHEN 'In Development' THEN 3
                WHEN 'Planned' THEN 4
                ELSE 5
            END
    """,
    
    "customers_waiting_for_features": """
        // Count customers waiting for roadmap features
        MATCH (ri:__Entity__:ROADMAP_ITEM)
        WHERE ri.status IN ['planned', 'in_progress', 'behind_schedule']
        OPTIONAL MATCH (ri)<-[:DEPENDS_ON]-(com:__Entity__:COMMITMENT)<-[:HAS_COMMITMENT]-(c:__Entity__:CUSTOMER)
        WITH count(distinct c) as waiting_customers, 
             collect(distinct c.name) as customer_names,
             collect(distinct ri.name) as feature_names
        RETURN 
            waiting_customers as customers_waiting,
            customer_names[0..10] as sample_customers,
            feature_names[0..10] as sample_features
    """,
    
    "unmet_sla_commitments": """
        // Find customers with unmet SLA commitments
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SLA]->(sla:__Entity__:SLA)
        WHERE sla.performance < sla.target
        AND sla.last_measured > datetime() - duration({days: 90})
        RETURN 
            c.name as customer_name,
            sla.metric as sla_metric,
            sla.target as sla_target,
            sla.performance as actual_performance,
            round((sla.target - sla.performance) * 100.0 / sla.target, 2) as miss_percentage,
            sla.penalty_percentage as penalty_rate,
            CASE
                WHEN sla.performance < sla.target * 0.9 THEN 'Critical'
                WHEN sla.performance < sla.target * 0.95 THEN 'Warning'
                ELSE 'Minor'
            END as severity
        ORDER BY miss_percentage DESC
    """,
    
    "product_satisfaction_scores": """
        // Get products with highest customer satisfaction
        MATCH (p:__Entity__:PRODUCT)
        OPTIONAL MATCH (p)-[:HAS_SUCCESS_SCORE]->(pss:__Entity__:PRODUCT_SUCCESS_SCORE)
        OPTIONAL MATCH (p)<-[:USES]-(c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WITH p, pss, avg(css.score) as avg_customer_score, count(distinct c) as customer_count
        RETURN 
            p.name as product_name,
            coalesce(pss.score, pss.satisfaction_rating * 20, avg_customer_score) as satisfaction_score,
            pss.nps_score as nps_score,
            customer_count as active_customers,
            avg_customer_score as avg_customer_success_score
        ORDER BY satisfaction_score DESC NULLS LAST
    """,
    
    "customers_per_product_with_value": """
        // Count customers per product with average subscription value
        MATCH (p:__Entity__:PRODUCT)<-[:USES]-(c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH p, count(distinct c) as customer_count, 
             avg(s.amount) as avg_monthly_value,
             sum(s.amount * 12) as total_annual_value
        RETURN 
            p.name as product_name,
            customer_count,
            round(avg_monthly_value, 2) as avg_monthly_subscription,
            round(avg_monthly_value * 12, 2) as avg_annual_subscription,
            total_annual_value as total_product_revenue
        ORDER BY total_annual_value DESC
    """,
    
    "products_with_operational_issues": """
        // Find products with most operational issues affecting customers
        MATCH (p:__Entity__:PRODUCT)<-[:USES]-(c:__Entity__:CUSTOMER)-[:EXPERIENCED]->(e:__Entity__:EVENT)
        WHERE e.impact = 'negative' 
        AND e.type IN ['service_outage', 'performance_issue', 'bug', 'downtime']
        AND e.timestamp > datetime() - duration({days: 90})
        WITH p, count(distinct e) as issue_count, 
             count(distinct c) as affected_customers,
             collect(distinct e.type) as issue_types
        OPTIONAL MATCH (p)<-[:USES]-(all_c:__Entity__:CUSTOMER)
        WITH p, issue_count, affected_customers, issue_types, 
             count(distinct all_c) as total_customers
        RETURN 
            p.name as product_name,
            issue_count as operational_issues,
            affected_customers,
            total_customers,
            round(affected_customers * 100.0 / total_customers, 2) as impact_percentage,
            issue_types
        ORDER BY impact_percentage DESC
    """,
    
    "feature_adoption_rates": """
        // Calculate adoption rates for recently released features
        MATCH (f:__Entity__:FEATURE)
        WHERE f.release_date > datetime() - duration({days: 180})
        OPTIONAL MATCH (f)<-[:USES]-(c:__Entity__:CUSTOMER)
        WITH f, count(distinct c) as adopters
        MATCH (all_c:__Entity__:CUSTOMER)
        WITH f, adopters, count(distinct all_c) as total_customers
        RETURN 
            f.name as feature_name,
            f.release_date as release_date,
            adopters as customers_using,
            total_customers as total_customers,
            round(adopters * 100.0 / total_customers, 2) as adoption_rate_percentage,
            duration.between(f.release_date, datetime()).months as months_since_release
        ORDER BY adoption_rate_percentage DESC
    """,
    
    "critical_roadmap_items_for_retention": """
        // Identify roadmap items critical for customer retention
        MATCH (ri:__Entity__:ROADMAP_ITEM)<-[:DEPENDS_ON]-(com:__Entity__:COMMITMENT)<-[:HAS_COMMITMENT]-(c:__Entity__:CUSTOMER)
        WHERE com.priority IN ['high', 'critical']
        WITH ri, count(distinct c) as dependent_customers, collect(distinct c.name) as customer_names
        MATCH (c2:__Entity__:CUSTOMER)-[:HAS_COMMITMENT]->(com2:__Entity__:COMMITMENT)-[:DEPENDS_ON]->(ri)
        MATCH (c2)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH ri, dependent_customers, customer_names, sum(s.amount * 12) as revenue_dependent
        RETURN 
            ri.name as roadmap_item,
            ri.status as current_status,
            ri.target_date as target_date,
            dependent_customers,
            customer_names[0..5] as top_dependent_customers,
            revenue_dependent as revenue_at_stake,
            CASE
                WHEN ri.status IN ['behind_schedule', 'at_risk'] THEN 'High Risk'
                WHEN dependent_customers > 5 THEN 'Critical'
                WHEN revenue_dependent > 1000000 THEN 'High Priority'
                ELSE 'Normal'
            END as retention_impact
        ORDER BY revenue_dependent DESC
    """,
    
    "roadmap_behind_schedule_percentage": """
        // Calculate percentage of roadmap items behind schedule
        MATCH (ri:__Entity__:ROADMAP_ITEM)
        WITH count(ri) as total_items,
             count(CASE WHEN ri.status = 'behind_schedule' THEN 1 END) as behind_schedule,
             count(CASE WHEN ri.status = 'at_risk' THEN 1 END) as at_risk,
             count(CASE WHEN ri.status = 'completed' THEN 1 END) as completed,
             count(CASE WHEN ri.status = 'in_progress' THEN 1 END) as in_progress
        RETURN 
            total_items,
            behind_schedule,
            at_risk,
            completed,
            in_progress,
            round(behind_schedule * 100.0 / total_items, 2) as behind_schedule_percentage,
            round((behind_schedule + at_risk) * 100.0 / total_items, 2) as total_at_risk_percentage
    """,
    
    "projects_blocked_by_constraints": """
        // Find projects blocked by operational constraints
        MATCH (p:__Entity__:PROJECT)
        WHERE p.status IN ['blocked', 'on_hold']
        OR exists(p.blocked_by)
        OPTIONAL MATCH (p)-[:BLOCKED_BY]->(constraint)
        RETURN 
            count(distinct p) as blocked_projects,
            collect(distinct p.name) as project_names,
            collect(distinct constraint.description) as blocking_constraints
    """,
    
    "revenue_per_team_member": """
        // Calculate revenue per team member for each department
        MATCH (t:__Entity__:TEAM)
        WHERE exists(t.member_count) AND t.member_count > 0
        OPTIONAL MATCH (t)-[:SUPPORTS]->(p:__Entity__:PRODUCT)<-[:USES]-(c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH t, sum(coalesce(s.amount * 12, 0)) as team_revenue
        RETURN 
            t.name as team_name,
            t.member_count as team_size,
            team_revenue,
            round(team_revenue / t.member_count, 2) as revenue_per_member
        ORDER BY revenue_per_member DESC
    """,
    
    "company_objectives_risk_count": """
        // Count risks associated with each company objective
        MATCH (o:__Entity__:OBJECTIVE)
        OPTIONAL MATCH (o)-[:AT_RISK_FROM]->(r:__Entity__:RISK)
        WITH o, count(distinct r) as risk_count, 
             collect(distinct r.severity) as risk_severities
        WHERE risk_count > 0
        RETURN 
            o.name as objective,
            o.priority as priority,
            risk_count,
            risk_severities,
            CASE
                WHEN 'critical' IN risk_severities THEN 'Critical Risk'
                WHEN 'high' IN risk_severities THEN 'High Risk'
                WHEN risk_count > 3 THEN 'Multiple Risks'
                WHEN risk_count > 0 THEN 'Some Risk'
                ELSE 'Low Risk'
            END as overall_risk_level
        ORDER BY risk_count DESC
    """,
    
    "high_severity_risks_without_mitigation": """
        // Count high-severity risks without mitigation
        MATCH (r:__Entity__:RISK)
        WHERE r.severity IN ['high', 'critical']
        AND NOT (r)-[:MITIGATED_BY]->()
        RETURN 
            count(r) as unmitigated_risks,
            collect(distinct r.description)[0..10] as sample_risks,
            collect(distinct r.severity) as severity_breakdown
    """,
    
    "cross_objective_risks": """
        // Find risks affecting multiple objectives or customers
        MATCH (r:__Entity__:RISK)
        OPTIONAL MATCH (r)<-[:AT_RISK_FROM]-(o:__Entity__:OBJECTIVE)
        OPTIONAL MATCH (r)<-[:FACES]-(c:__Entity__:CUSTOMER)
        WITH r, count(distinct o) as objectives_affected, count(distinct c) as customers_affected
        WHERE objectives_affected > 1 OR customers_affected > 1
        RETURN 
            r.description as risk_description,
            r.severity as severity,
            objectives_affected,
            customers_affected,
            objectives_affected + customers_affected as total_impact_scope
        ORDER BY total_impact_scope DESC
    """,
    
    "project_delivery_success_rate": """
        // Calculate project success rate by team and product
        MATCH (p:__Entity__:PROJECT)
        OPTIONAL MATCH (p)<-[:WORKS_ON]-(t:__Entity__:TEAM)
        OPTIONAL MATCH (p)-[:DELIVERS]->(prod:__Entity__:PRODUCT)
        WITH t.name as team_name, prod.name as product_name,
             count(p) as total_projects,
             count(CASE WHEN p.status = 'completed' THEN 1 END) as completed,
             count(CASE WHEN p.status = 'on_schedule' THEN 1 END) as on_schedule,
             count(CASE WHEN p.status IN ['behind_schedule', 'at_risk'] THEN 1 END) as delayed
        RETURN 
            coalesce(team_name, 'Unassigned') as team,
            coalesce(product_name, 'General') as product_area,
            total_projects,
            completed,
            on_schedule,
            delayed,
            CASE 
                WHEN total_projects > 0 
                THEN round((completed + on_schedule) * 100.0 / total_projects, 2)
                ELSE 0
            END as success_rate_percentage
        ORDER BY success_rate_percentage DESC
    """,
    
    "high_growth_customer_segments": """
        // Identify customer segments with highest growth potential
        MATCH (c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH c, sum(s.amount * 12) as current_arr
        OPTIONAL MATCH (c)-[:HAD_REVENUE]->(hr:__Entity__:HISTORICAL_REVENUE)
        WHERE hr.year = date().year - 1
        WITH c, current_arr, coalesce(hr.amount, current_arr * 0.8) as previous_arr,
             CASE 
                WHEN c.industry IS NOT NULL THEN c.industry
                WHEN c.segment IS NOT NULL THEN c.segment
                WHEN c.size = 'Enterprise' THEN 'Enterprise'
                WHEN current_arr > 1000000 THEN 'Large'
                WHEN current_arr > 100000 THEN 'Mid-Market'
                ELSE 'SMB'
             END as segment
        WITH segment, 
             sum(current_arr) as total_current_arr,
             sum(previous_arr) as total_previous_arr,
             count(c) as customer_count
        RETURN 
            segment,
            customer_count,
            total_current_arr,
            round((total_current_arr - total_previous_arr) * 100.0 / total_previous_arr, 2) as growth_rate,
            round(total_current_arr / customer_count, 2) as avg_customer_value
        ORDER BY growth_rate DESC
    """,
    
    "profitability_to_cost_ratio": """
        // Calculate profitability-to-cost ratio for scaling decisions
        MATCH (p:__Entity__:PRODUCT)
        OPTIONAL MATCH (p)<-[:USES]-(c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WITH p, sum(coalesce(s.amount * 12, 0)) as product_revenue
        OPTIONAL MATCH (p)<-[:SUPPORTS]-(t:__Entity__:TEAM)-[:HAS_COST]->(cost:__Entity__:OPERATIONAL_COST)
        WITH p, product_revenue, sum(coalesce(cost.amount, 0)) as product_costs
        WHERE product_revenue > 0 AND product_costs > 0
        RETURN 
            p.name as product_name,
            product_revenue,
            product_costs,
            product_revenue - product_costs as gross_profit,
            round((product_revenue - product_costs) / product_costs, 2) as profitability_ratio,
            round((product_revenue - product_costs) * 100.0 / product_revenue, 2) as profit_margin_percentage
        ORDER BY profitability_ratio DESC
    """,
    
    "regional_expansion_metrics": """
        // Analyze regions for expansion potential
        MATCH (c:__Entity__:CUSTOMER)-[:PAYS]->(s:__Entity__:SUBSCRIPTION)
        WHERE c.region IS NOT NULL
        WITH c.region as region, 
             count(distinct c) as customer_count,
             sum(s.amount * 12) as regional_arr,
             avg(s.amount) as avg_deal_size
        OPTIONAL MATCH (c2:__Entity__:CUSTOMER)
        WHERE c2.region = region
        AND (c2)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score > 80
        WITH region, customer_count, regional_arr, avg_deal_size,
             count(distinct c2) as satisfied_customers
        RETURN 
            region,
            customer_count,
            regional_arr,
            round(avg_deal_size, 2) as avg_monthly_deal_size,
            round(satisfied_customers * 100.0 / customer_count, 2) as satisfaction_rate,
            round(regional_arr / customer_count, 2) as revenue_per_customer,
            CASE
                WHEN customer_count < 10 AND satisfaction_rate > 70 THEN 'High Growth Potential'
                WHEN regional_arr < 1000000 AND avg_deal_size > 10000 THEN 'Premium Market Opportunity'
                WHEN satisfaction_rate > 80 THEN 'Expand Existing Base'
                ELSE 'Improve Before Expanding'
            END as expansion_recommendation
        ORDER BY regional_arr DESC
    """,
    
    "features_to_improve_success_scores": """
        // Identify features that correlate with higher customer success
        MATCH (c:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE css.score > 80
        MATCH (c)-[:USES]->(f:__Entity__:FEATURE)
        WITH f, count(distinct c) as high_score_users, avg(css.score) as avg_score_with_feature
        MATCH (c2:__Entity__:CUSTOMER)-[:HAS_SUCCESS_SCORE]->(css2:__Entity__:CUSTOMER_SUCCESS_SCORE)
        WHERE NOT (c2)-[:USES]->(f)
        WITH f, high_score_users, avg_score_with_feature, avg(css2.score) as avg_score_without_feature
        WHERE avg_score_with_feature > avg_score_without_feature + 5
        RETURN 
            f.name as feature_name,
            high_score_users as customers_using,
            round(avg_score_with_feature, 2) as avg_success_with_feature,
            round(avg_score_without_feature, 2) as avg_success_without_feature,
            round(avg_score_with_feature - avg_score_without_feature, 2) as score_improvement
        ORDER BY score_improvement DESC
    """,
    
    "critical_growth_objectives": """
        // Find objectives most critical for growth targets
        MATCH (o:__Entity__:OBJECTIVE)
        WHERE o.type IN ['REVENUE', 'GROWTH', 'PROFITABILITY']
        OR o.name =~ '.*growth.*|.*revenue.*|.*expansion.*'
        OPTIONAL MATCH (o)-[:ENABLES]->(outcome)
        OPTIONAL MATCH (o)-[:AT_RISK_FROM]->(r:__Entity__:RISK)
        WITH o, collect(distinct outcome.description) as enabled_outcomes,
             count(distinct r) as risk_count,
             max(CASE WHEN r.severity = 'critical' THEN 3 
                      WHEN r.severity = 'high' THEN 2 
                      WHEN r.severity = 'medium' THEN 1 
                      ELSE 0 END) as max_risk_severity
        RETURN 
            o.name as objective,
            o.type as objective_type,
            o.target_value as target,
            o.current_value as current_progress,
            enabled_outcomes,
            risk_count,
            CASE max_risk_severity
                WHEN 3 THEN 'Critical Risk'
                WHEN 2 THEN 'High Risk'
                WHEN 1 THEN 'Medium Risk'
                ELSE 'Low Risk'
            END as risk_level,
            CASE
                WHEN o.priority = 'critical' AND risk_count = 0 THEN 'Accelerate'
                WHEN o.priority = 'critical' AND risk_count > 0 THEN 'Protect & Prioritize'
                WHEN o.priority = 'high' THEN 'Important'
                ELSE 'Supporting'
            END as growth_criticality
        ORDER BY 
            CASE o.priority
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                ELSE 3
            END,
            max_risk_severity DESC
    """
}