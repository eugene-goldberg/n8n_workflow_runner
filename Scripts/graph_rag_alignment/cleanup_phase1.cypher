// Cleanup script to remove Phase 1 entities before re-running

// Remove all the new entity types
MATCH (n:Subscription) DETACH DELETE n;
MATCH (n:Project) DETACH DELETE n;
MATCH (n:Team) DETACH DELETE n;
MATCH (n:Event) DETACH DELETE n;
MATCH (n:SLA) DETACH DELETE n;
MATCH (n:CustomerSuccessScore) DETACH DELETE n;
MATCH (n:CompanyObjective) DETACH DELETE n;
MATCH (n:OperationalCost) DETACH DELETE n;
MATCH (n:Roadmap) DETACH DELETE n;

// Verify cleanup
MATCH (n)
WHERE n:Subscription OR n:Project OR n:Team OR n:Event OR n:SLA OR 
      n:CustomerSuccessScore OR n:CompanyObjective OR n:OperationalCost OR n:Roadmap
RETURN labels(n) as Labels, count(n) as Count;