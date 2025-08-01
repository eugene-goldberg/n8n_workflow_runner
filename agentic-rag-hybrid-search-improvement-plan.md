# Agentic RAG Hybrid Search Improvement Plan

## Executive Summary

After extensive research into 2025's latest agentic RAG technologies and analysis of our current implementation, this plan addresses the critical issue: **natural business queries default to vector search despite having a rich knowledge graph of business entities**. Our solution combines deterministic routing rules with semantic understanding to ensure appropriate tool selection.

## Problem Statement

### Current State
- **Tools exist and work**: vector_search, graph_search, get_entity_relationships, hybrid_search ✅
- **Natural queries fail**: Business questions like "How much revenue at risk?" default to vector search ❌
- **Explicit queries succeed**: "Show me the relationship between X and Y" triggers graph tools ✅
- **Display bug**: n8n workflow doesn't show actual tool usage ❌

### Root Causes
1. **LLM Tool Selection Bias**: Models prefer "safer" vector search over graph tools
2. **Prompt Instructions Ignored**: Even explicit mandatory rules are overridden
3. **Intent Misclassification**: Business queries aren't recognized as needing graph data
4. **Display Issues**: n8n workflow missing tool type mappings

## Proposed Solution Architecture

### Phase 1: Immediate Fixes (1-2 days)

#### 1.1 Fix n8n Workflow Display
```javascript
// Update Format Success Response node
function getPurpose(toolName) {
  const purposes = {
    'vector_search': 'Semantic search in knowledge base',
    'graph_search': 'Graph traversal for relationships',
    'get_entity_relationships': 'Entity relationship exploration',
    'hybrid_search': 'Combined vector and graph search'
  };
  return purposes[toolName] || 'General search';
}
```

#### 1.2 Implement Query Classifier
Create a deterministic pre-classifier that routes queries before they reach the LLM agent:

```python
# app/agent/query_classifier.py
class QueryClassifier:
    def __init__(self):
        self.business_entities = {
            'customers': ['Disney', 'EA', 'Netflix', 'Spotify', 'Nintendo'],
            'metrics': ['ARR', 'MRR', 'revenue', 'subscription', 'churn'],
            'teams': ['Platform Team', 'Analytics Team', 'Infrastructure Team'],
            'risks': ['risk', 'impact', 'concern', 'issue', 'threat']
        }
        
    def classify_query(self, query: str) -> str:
        query_lower = query.lower()
        
        # Check for explicit relationship queries
        if any(phrase in query_lower for phrase in [
            'relationship between', 'how does', 'connected to', 
            'relates to', 'impact on'
        ]):
            return 'graph_required'
            
        # Check for business entities
        entity_count = sum(
            1 for entity_list in self.business_entities.values()
            for entity in entity_list
            if entity.lower() in query_lower
        )
        
        if entity_count >= 2:
            return 'graph_required'
            
        # Check for business metrics
        if any(metric in query_lower for metric in self.business_entities['metrics']):
            return 'graph_preferred'
            
        # Check for impact/risk analysis
        if any(risk in query_lower for risk in self.business_entities['risks']):
            return 'graph_preferred'
            
        return 'vector_preferred'
```

### Phase 2: Enhanced Routing System (3-5 days)

#### 2.1 Semantic Router Implementation
Implement a semantic router that combines deterministic rules with semantic understanding:

```python
# app/agent/semantic_router.py
from typing import List, Dict, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer

class SemanticRouter:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.routes = self._initialize_routes()
        
    def _initialize_routes(self) -> Dict[str, Dict]:
        return {
            'graph_search': {
                'description': 'Questions about specific business entities, relationships, and metrics',
                'examples': [
                    "What is Disney's ARR?",
                    "How much revenue at risk if Netflix churns?",
                    "Which teams work on the Analytics Platform?",
                    "Show me customers with MRR over $100k"
                ],
                'embeddings': None  # Will be computed
            },
            'vector_search': {
                'description': 'General questions about concepts, documentation, best practices',
                'examples': [
                    "What is an SLA?",
                    "Best practices for customer retention",
                    "How to calculate churn rate?",
                    "Explain subscription models"
                ],
                'embeddings': None
            }
        }
        
    def route_query(self, query: str) -> Tuple[str, float]:
        """Route query to appropriate tool with confidence score"""
        query_embedding = self.model.encode(query)
        
        scores = {}
        for route_name, route_info in self.routes.items():
            if route_info['embeddings'] is None:
                route_info['embeddings'] = self.model.encode(route_info['examples'])
            
            # Calculate similarity to route examples
            similarities = np.dot(route_info['embeddings'], query_embedding)
            scores[route_name] = float(np.max(similarities))
            
        best_route = max(scores, key=scores.get)
        confidence = scores[best_route]
        
        return best_route, confidence
```

#### 2.2 Tool Selection Middleware
Create middleware that intercepts tool selection:

```python
# app/agent/tool_selection_middleware.py
class ToolSelectionMiddleware:
    def __init__(self, classifier: QueryClassifier, router: SemanticRouter):
        self.classifier = classifier
        self.router = router
        self.threshold = 0.7
        
    async def select_tools(self, query: str) -> List[str]:
        """Determine which tools to use based on query analysis"""
        # Step 1: Deterministic classification
        classification = self.classifier.classify_query(query)
        
        # Step 2: Semantic routing
        route, confidence = self.router.route_query(query)
        
        # Step 3: Decision logic
        if classification == 'graph_required':
            return ['get_entity_relationships', 'graph_search']
        elif classification == 'graph_preferred' and confidence > self.threshold:
            return ['hybrid_search']
        elif route == 'graph_search' and confidence > self.threshold:
            return ['graph_search', 'vector_search']
        else:
            return ['vector_search']
```

### Phase 3: LangGraph Integration (5-7 days)

#### 3.1 Deterministic Workflow with LangGraph
Implement a LangGraph-based system for more predictable routing:

```python
# app/agent/langgraph_router.py
from langgraph.graph import Graph, StateGraph
from typing import TypedDict, List

class QueryState(TypedDict):
    query: str
    classification: str
    tools_to_use: List[str]
    results: Dict
    
class LangGraphRouter:
    def __init__(self):
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(QueryState)
        
        # Add nodes
        workflow.add_node("classify", self.classify_node)
        workflow.add_node("route", self.route_node)
        workflow.add_node("execute_graph", self.execute_graph_node)
        workflow.add_node("execute_vector", self.execute_vector_node)
        workflow.add_node("execute_hybrid", self.execute_hybrid_node)
        
        # Add edges
        workflow.add_edge("classify", "route")
        
        # Conditional routing based on classification
        workflow.add_conditional_edges(
            "route",
            self.determine_path,
            {
                "graph": "execute_graph",
                "vector": "execute_vector",
                "hybrid": "execute_hybrid"
            }
        )
        
        return workflow.compile()
```

### Phase 4: Query Preprocessing Pipeline (3-4 days)

#### 4.1 Business Entity Extraction
```python
# app/agent/entity_extractor.py
class BusinessEntityExtractor:
    def __init__(self, graph_connection):
        self.graph = graph_connection
        self.entities_cache = self._load_entities()
        
    def extract_entities(self, query: str) -> List[Dict]:
        """Extract business entities from query"""
        entities = []
        
        # Use NER for entity extraction
        doc = nlp(query)
        
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'MONEY', 'DATE']:
                # Check if entity exists in graph
                if self._entity_exists(ent.text):
                    entities.append({
                        'text': ent.text,
                        'type': self._get_entity_type(ent.text),
                        'label': ent.label_
                    })
                    
        return entities
```

#### 4.2 Query Enhancement
```python
# app/agent/query_enhancer.py
class QueryEnhancer:
    def enhance_for_graph(self, query: str, entities: List[Dict]) -> str:
        """Enhance query to trigger graph search"""
        if len(entities) >= 2:
            # Multiple entities - add relationship context
            return f"Show me the relationship between {entities[0]['text']} and {entities[1]['text']} in the context of: {query}"
        elif len(entities) == 1:
            # Single entity - add property context
            return f"Get {entities[0]['text']}'s properties and relationships relevant to: {query}"
        else:
            # No entities - try to infer intent
            if any(metric in query.lower() for metric in ['revenue', 'arr', 'mrr']):
                return f"Using the knowledge graph, find data about: {query}"
            return query
```

### Phase 5: Monitoring and Optimization (2-3 days)

#### 5.1 Tool Usage Analytics
```python
# app/monitoring/tool_analytics.py
class ToolUsageAnalytics:
    def __init__(self):
        self.usage_log = []
        
    def log_tool_usage(self, query: str, tools_used: List[str], 
                       results_quality: float):
        self.usage_log.append({
            'timestamp': datetime.now(),
            'query': query,
            'tools_used': tools_used,
            'results_quality': results_quality,
            'query_type': self._classify_query_type(query)
        })
        
    def analyze_patterns(self) -> Dict:
        """Analyze tool usage patterns"""
        # Identify queries that should use graph but don't
        misrouted_queries = [
            log for log in self.usage_log
            if self._should_use_graph(log['query']) 
            and 'graph_search' not in log['tools_used']
        ]
        
        return {
            'total_queries': len(self.usage_log),
            'graph_usage_rate': self._calculate_graph_usage_rate(),
            'misrouted_queries': misrouted_queries,
            'optimization_opportunities': self._identify_optimizations()
        }
```

## Implementation Timeline

### Week 1
- **Day 1-2**: Fix n8n workflow display bug and implement basic query classifier
- **Day 3-4**: Deploy semantic router and test with production queries
- **Day 5**: Monitor and collect baseline metrics

### Week 2
- **Day 1-3**: Implement LangGraph deterministic workflow
- **Day 4-5**: Build query preprocessing pipeline with entity extraction

### Week 3
- **Day 1-2**: Deploy enhanced system to production
- **Day 3-4**: Monitor performance and optimize routing rules
- **Day 5**: Create documentation and training materials

## Success Metrics

1. **Tool Selection Accuracy**
   - Target: 90% of business queries trigger appropriate graph tools
   - Baseline: ~20% (current state)

2. **Query Response Quality**
   - Measure: User satisfaction with answers to business questions
   - Target: 85% satisfaction rate

3. **System Performance**
   - Latency: < 100ms for routing decision
   - Throughput: Support 1000+ concurrent queries

4. **Cost Optimization**
   - Reduce unnecessary LLM calls by 40%
   - Optimize tool usage based on query complexity

## Risk Mitigation

1. **Fallback Mechanisms**
   - If routing fails, default to hybrid search
   - Implement circuit breakers for each component

2. **Gradual Rollout**
   - A/B test new routing system with 10% of traffic
   - Monitor closely and scale based on performance

3. **Model Updates**
   - Regular retraining of semantic router
   - Continuous improvement of routing rules

## Conclusion

This comprehensive plan addresses the core issue of natural business queries not triggering appropriate tools. By combining deterministic rules, semantic understanding, and modern routing frameworks like LangGraph, we can achieve reliable hybrid search that leverages both vector and graph capabilities effectively.

The phased approach ensures minimal disruption while progressively improving the system's ability to understand and route business queries correctly. With proper implementation and monitoring, we expect to see a significant improvement in query handling within 3 weeks.