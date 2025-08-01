"""Deterministic router for query classification and strategy selection"""

import re
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass

from app.schemas.routing import RetrievalStrategy, RouterOutput


@dataclass
class RoutingRule:
    """A single routing rule with patterns and strategy"""
    patterns: List[str]
    strategy: RetrievalStrategy
    confidence: float
    description: str


class DeterministicRouter:
    """
    Deterministic query router that uses pattern matching and entity detection
    to select the optimal retrieval strategy.
    """
    
    def __init__(self):
        # Load business entities from configuration
        self.business_entities = self._load_business_entities()
        self.routing_rules = self._compile_routing_rules()
        
    def _load_business_entities(self) -> Dict[str, Set[str]]:
        """Load known business entities for detection"""
        return {
            'customers': {
                'disney', 'ea', 'netflix', 'spotify', 'nintendo',
                'warner bros', 'universal', 'sony', 'microsoft', 'apple'
            },
            'metrics': {
                'arr', 'mrr', 'revenue', 'subscription', 'churn',
                'retention', 'ltv', 'cac', 'growth', 'usage',
                'monthly recurring revenue', 'annual recurring revenue'
            },
            'teams': {
                'platform team', 'analytics team', 'infrastructure team',
                'data team', 'engineering', 'product', 'sales', 'support'
            },
            'risks': {
                'risk', 'impact', 'concern', 'issue', 'threat',
                'vulnerability', 'exposure', 'downtime', 'outage', 'breach'
            },
            'relationships': {
                'customer success', 'account manager', 'technical lead',
                'project manager', 'stakeholder', 'executive sponsor'
            }
        }
        
    def _compile_routing_rules(self) -> List[RoutingRule]:
        """Compile routing rules in priority order"""
        return [
            # Comparative analysis - CHECK FIRST for multiple entities
            RoutingRule(
                patterns=[
                    r"compare .+ (?:and|with|to|vs\.?)",
                    r"difference(?:s)? between .+ and",
                    r"similarit(?:y|ies) (?:between|among|of)",
                    r"contrast .+ (?:with|and|versus)",
                    r"which is (?:better|worse|higher|lower)",
                    r"comparison (?:of|between)",
                ],
                strategy=RetrievalStrategy.HYBRID_PARALLEL,
                confidence=0.85,
                description="Comparative analysis queries"
            ),
            
            # Multi-hop relational queries - HIGHEST PRIORITY
            RoutingRule(
                patterns=[
                    r"relationship between .+ and .+",
                    r"how (?:does|is) .+ (?:connected|related|linked) (?:to|with)",
                    r"(?:connection|link|association) (?:between|from) .+ (?:to|and)",
                    r"show .+ relationships",
                    r"what connects .+ (?:to|and|with)",
                ],
                strategy=RetrievalStrategy.GRAPH,
                confidence=0.95,
                description="Multi-hop relationship queries"
            ),
            
            # Business impact and risk analysis - HIGH PRIORITY
            RoutingRule(
                patterns=[
                    r"(?:revenue|arr|mrr) (?:at risk|impact|loss)",
                    r"if .+ (?:churns?|leaves?|cancels?)",
                    r"impact (?:of|on) .+ (?:revenue|arr|mrr)",
                    r"what happens if .+ (?:fails?|stops?|breaks?)",
                    r"risk (?:to|of|for) .+ (?:revenue|growth|retention)",
                ],
                strategy=RetrievalStrategy.GRAPH,
                confidence=0.9,
                description="Business impact and risk queries"
            ),
            
            # Entity-specific queries with metrics
            RoutingRule(
                patterns=[
                    r"(?:disney|netflix|spotify|ea|nintendo)(?:'s)? (?:arr|mrr|revenue|subscription)",
                    r"which (?:customers?|teams?) (?:have|has|with)",
                    r"(?:top|highest|lowest) \d* (?:customers?|teams?) by",
                    r"list .+ with (?:arr|mrr|revenue) (?:over|under|between)",
                    r"show me .+ (?:metrics|kpis|performance)",
                ],
                strategy=RetrievalStrategy.GRAPH,
                confidence=0.9,
                description="Entity-specific metric queries"
            ),
            
            # Complex analytical queries - SEQUENTIAL HYBRID
            RoutingRule(
                patterns=[
                    r"analy[sz]e .+ and (?:its|their) (?:impact|effect|influence)",
                    r"(?:find|identify) .+ (?:then|and) (?:determine|calculate|assess)",
                    r"what .+ and (?:how|why|when) (?:does|did|will)",
                    r"explain .+ (?:including|with|along with) (?:its|their)",
                ],
                strategy=RetrievalStrategy.HYBRID_SEQUENTIAL,
                confidence=0.8,
                description="Complex analytical queries"
            ),
            
            # Risk and concern queries - GRAPH
            RoutingRule(
                patterns=[
                    r"(?:top|main|key) \d* (?:risks?|concerns?|issues?)",
                    r"what (?:risks?|concerns?|issues?) (?:have been|are)",
                    r"concerns? (?:raised|about|regarding)",
                ],
                strategy=RetrievalStrategy.GRAPH,
                confidence=0.85,
                description="Risk and concern analysis queries"
            ),
            
            # Conceptual and definition queries - VECTOR
            RoutingRule(
                patterns=[
                    r"what (?:is|are) (?:a|an|the)? (?!top|main|key).+\??",  # Negative lookahead for risk patterns
                    r"explain (?:the concept of|how|what|why)",
                    r"definition of",
                    r"describe (?:the process|how|what)",
                    r"best practices? (?:for|in|about)",
                    r"(?:guide|tutorial|overview) (?:to|for|about)",
                ],
                strategy=RetrievalStrategy.VECTOR,
                confidence=0.9,
                description="Conceptual and definition queries"
            ),
            
            # Conversational and no-retrieval needed
            RoutingRule(
                patterns=[
                    r"^(?:hi|hello|hey|greetings?)",
                    r"^(?:thanks?|thank you|appreciate)",
                    r"^(?:bye|goodbye|see you)",
                    r"^(?:yes|no|okay|sure|got it)",
                    r"^(?:help|commands?|usage)",
                ],
                strategy=RetrievalStrategy.NO_RETRIEVAL,
                confidence=0.95,
                description="Conversational responses"
            ),
        ]
        
    def _count_entities(self, query: str) -> Tuple[int, List[str]]:
        """Count and extract business entities from the query"""
        query_lower = query.lower()
        found_entities = []
        
        for category, entities in self.business_entities.items():
            for entity in entities:
                # Use word boundaries to avoid partial matches
                if re.search(rf'\b{re.escape(entity)}\b', query_lower):
                    found_entities.append(entity)
                    
        return len(found_entities), found_entities
        
    def _classify_query_type(self, query: str) -> str:
        """Classify the general type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['who', 'what company', 'which team']):
            return "entity_lookup"
        elif any(word in query_lower for word in ['how much', 'what percentage', 'calculate']):
            return "metric_calculation"
        elif any(word in query_lower for word in ['why', 'how does', 'explain']):
            return "conceptual"
        elif any(word in query_lower for word in ['compare', 'difference', 'versus']):
            return "comparative"
        elif any(word in query_lower for word in ['impact', 'risk', 'if', 'happens']):
            return "impact_analysis"
        else:
            return "unknown"
            
    def route(self, query: str) -> RouterOutput:
        """
        Analyze the query and determine the optimal retrieval strategy.
        
        Args:
            query: The user's natural language query
            
        Returns:
            RouterOutput with strategy, reasoning, and confidence
        """
        query_lower = query.lower()
        
        # Check routing rules in priority order
        for rule in self.routing_rules:
            for pattern in rule.patterns:
                if re.search(pattern, query_lower):
                    entity_count, entities = self._count_entities(query)
                    
                    return RouterOutput(
                        strategy=rule.strategy,
                        reasoning=f"{rule.description}. Pattern matched: '{pattern}'",
                        confidence=rule.confidence,
                        detected_entities=entities,
                        query_type=self._classify_query_type(query)
                    )
        
        # Entity-based routing (fallback)
        entity_count, entities = self._count_entities(query)
        
        if entity_count >= 2:
            # Multiple entities suggest relationships or comparison
            return RouterOutput(
                strategy=RetrievalStrategy.HYBRID_SEQUENTIAL,
                reasoning=f"Multiple entities detected ({entity_count}): {', '.join(entities[:3])}",
                confidence=0.75,
                detected_entities=entities,
                query_type=self._classify_query_type(query)
            )
        elif entity_count == 1:
            # Single entity likely needs graph lookup
            return RouterOutput(
                strategy=RetrievalStrategy.GRAPH,
                reasoning=f"Single business entity detected: {entities[0]}",
                confidence=0.7,
                detected_entities=entities,
                query_type=self._classify_query_type(query)
            )
            
        # Check for metric keywords as last resort
        metric_keywords = ['revenue', 'arr', 'mrr', 'subscription', 'customer', 'team']
        if any(keyword in query_lower for keyword in metric_keywords):
            return RouterOutput(
                strategy=RetrievalStrategy.GRAPH,
                reasoning="Business metrics mentioned without specific entities",
                confidence=0.6,
                detected_entities=[],
                query_type="metric_query"
            )
            
        # Default to vector search for unknown patterns
        return RouterOutput(
            strategy=RetrievalStrategy.VECTOR,
            reasoning="No specific patterns or entities detected, defaulting to semantic search",
            confidence=0.5,
            detected_entities=[],
            query_type=self._classify_query_type(query)
        )
        
    def explain_routing(self, query: str) -> Dict[str, any]:
        """Provide detailed explanation of routing decision for debugging"""
        result = self.route(query)
        entity_count, entities = self._count_entities(query)
        
        return {
            "query": query,
            "decision": result.dict(),
            "entity_analysis": {
                "count": entity_count,
                "entities": entities,
                "categories": {
                    cat: [e for e in entities if e in ents]
                    for cat, ents in self.business_entities.items()
                }
            },
            "all_patterns_checked": [
                {
                    "rule": rule.description,
                    "patterns": rule.patterns,
                    "would_select": rule.strategy.value
                }
                for rule in self.routing_rules
            ]
        }