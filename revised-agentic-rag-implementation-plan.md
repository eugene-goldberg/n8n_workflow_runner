# Revised Agentic RAG Implementation Plan

Based on expert research and our current implementation gaps, this revised plan focuses on building a true agentic system with explicit state machines, deterministic routing, and self-correction capabilities.

## Executive Summary

The expert research confirms our architectural triad (Neo4j, pgvector, Pydantic AI) is sound but reveals we're missing the explicit orchestration layer that defines true agentic systems. Our current reliance on LLM tool selection is the root cause of natural business queries defaulting to vector search.

## Core Architectural Changes

### 1. From Implicit to Explicit Routing

**Current State**: LLM autonomously chooses tools based on system prompt
**Target State**: Deterministic state machine with explicit routing logic

### 2. From Linear to Cyclical Workflows

**Current State**: Query → Tool → Response (no feedback loops)
**Target State**: Query → Route → Retrieve → Grade → Reflect → Rewrite → Response

### 3. From Simple to Advanced Hybrid Patterns

**Current State**: Basic hybrid search without sophisticated fusion
**Target State**: Sequential and parallel patterns with reranking

## Phase 1: LangGraph State Machine Implementation (Week 1)

### 1.1 Define Agent State Schema

```python
# app/agent/state.py
from typing import List, Dict, TypedDict, Annotated
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from enum import Enum

class RetrievalStrategy(str, Enum):
    VECTOR = "vector"
    GRAPH = "graph"
    HYBRID_SEQUENTIAL = "hybrid_sequential"
    HYBRID_PARALLEL = "hybrid_parallel"
    NO_RETRIEVAL = "no_retrieval"

class RouterOutput(BaseModel):
    strategy: RetrievalStrategy
    reasoning: str = Field(description="Brief explanation of routing decision")
    confidence: float = Field(ge=0.0, le=1.0)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], lambda x, y: x + y]
    strategy: RetrievalStrategy
    raw_context: List[Dict]
    ranked_context: List[Dict]
    quality_score: float
    retry_count: int
    error_log: List[str]
```

### 1.2 Implement Deterministic Router

```python
# app/agent/router.py
from typing import Dict
import re
from schemas import RouterOutput, RetrievalStrategy

class DeterministicRouter:
    def __init__(self):
        self.business_entities = self._load_business_entities()
        self.routing_rules = self._compile_routing_rules()
        
    def _compile_routing_rules(self) -> List[Dict]:
        return [
            # Multi-hop relational queries
            {
                "patterns": [
                    r"relationship between (\w+) and (\w+)",
                    r"how does (\w+) (?:affect|impact|influence) (\w+)",
                    r"(\w+)'s? (?:connection|link) (?:to|with) (\w+)"
                ],
                "strategy": RetrievalStrategy.GRAPH,
                "confidence": 0.95
            },
            # Business metrics requiring graph
            {
                "patterns": [
                    r"(?:revenue|ARR|MRR) (?:at risk|impact)",
                    r"which (?:customers?|teams?) (?:have|has)",
                    r"(?:top|highest|lowest) \d* (?:risks?|concerns?)"
                ],
                "strategy": RetrievalStrategy.GRAPH,
                "confidence": 0.9
            },
            # Comparative queries needing hybrid
            {
                "patterns": [
                    r"compare (\w+) (?:and|with|to) (\w+)",
                    r"difference between",
                    r"similarities? (?:between|among)"
                ],
                "strategy": RetrievalStrategy.HYBRID_PARALLEL,
                "confidence": 0.85
            },
            # Conceptual queries for vector
            {
                "patterns": [
                    r"what is (?:a|an|the)? (\w+)",
                    r"explain (?:how|what|why)",
                    r"best practices? for",
                    r"definition of"
                ],
                "strategy": RetrievalStrategy.VECTOR,
                "confidence": 0.9
            }
        ]
        
    def route(self, query: str) -> RouterOutput:
        query_lower = query.lower()
        
        # Check each rule in priority order
        for rule in self.routing_rules:
            for pattern in rule["patterns"]:
                if re.search(pattern, query_lower):
                    return RouterOutput(
                        strategy=rule["strategy"],
                        reasoning=f"Matched pattern: {pattern}",
                        confidence=rule["confidence"]
                    )
        
        # Entity-based routing
        entity_count = self._count_entities(query_lower)
        if entity_count >= 2:
            return RouterOutput(
                strategy=RetrievalStrategy.HYBRID_SEQUENTIAL,
                reasoning=f"Multiple entities detected: {entity_count}",
                confidence=0.8
            )
        elif entity_count == 1:
            return RouterOutput(
                strategy=RetrievalStrategy.GRAPH,
                reasoning="Single entity query",
                confidence=0.7
            )
            
        # Default to vector for unknown patterns
        return RouterOutput(
            strategy=RetrievalStrategy.VECTOR,
            reasoning="No specific patterns matched",
            confidence=0.5
        )
```

### 1.3 Build LangGraph Workflow

```python
# app/agent/workflow.py
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolExecutor
from langchain_core.messages import HumanMessage, AIMessage

class AgenticRAGWorkflow:
    def __init__(self, tools, llm):
        self.tools = tools
        self.llm = llm
        self.router = DeterministicRouter()
        self.graph = self._build_graph()
        
    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("vector_retriever", self.vector_retriever_node)
        workflow.add_node("graph_retriever", self.graph_retriever_node)
        workflow.add_node("hybrid_sequential", self.hybrid_sequential_node)
        workflow.add_node("hybrid_parallel", self.hybrid_parallel_node)
        workflow.add_node("grade_context", self.grade_context_node)
        workflow.add_node("rewrite_query", self.rewrite_query_node)
        workflow.add_node("rerank_context", self.rerank_context_node)
        workflow.add_node("generate", self.generate_node)
        workflow.add_node("handle_error", self.handle_error_node)
        
        # Entry point
        workflow.set_entry_point("router")
        
        # Routing edges
        workflow.add_conditional_edges(
            "router",
            self._route_to_retriever,
            {
                "vector": "vector_retriever",
                "graph": "graph_retriever",
                "hybrid_sequential": "hybrid_sequential",
                "hybrid_parallel": "hybrid_parallel",
                "no_retrieval": "generate"
            }
        )
        
        # Post-retrieval flow
        for retriever in ["vector_retriever", "graph_retriever", 
                         "hybrid_sequential", "hybrid_parallel"]:
            workflow.add_edge(retriever, "grade_context")
            
        # Grading edges
        workflow.add_conditional_edges(
            "grade_context",
            self._check_quality,
            {
                "good": "rerank_context",
                "poor": "rewrite_query",
                "error": "handle_error"
            }
        )
        
        # Rewrite loop
        workflow.add_edge("rewrite_query", "router")
        
        # Final generation
        workflow.add_edge("rerank_context", "generate")
        workflow.add_edge("generate", END)
        workflow.add_edge("handle_error", "generate")
        
        return workflow.compile()
```

## Phase 2: Advanced Retrieval Patterns (Week 2)

### 2.1 Sequential Hybrid Implementation

```python
# app/agent/hybrid_patterns.py
class SequentialHybridRetriever:
    def __init__(self, vector_store, graph_store, entity_extractor):
        self.vector_store = vector_store
        self.graph_store = graph_store
        self.entity_extractor = entity_extractor
        
    async def retrieve(self, query: str) -> List[Dict]:
        # Step 1: Semantic search for initial context
        vector_results = await self.vector_store.similarity_search(
            query, k=10
        )
        
        # Step 2: Extract entities from vector results
        combined_text = " ".join([r.page_content for r in vector_results])
        entities = self.entity_extractor.extract(combined_text)
        
        # Step 3: Graph traversal from extracted entities
        graph_results = []
        for entity in entities:
            # Get entity's immediate relationships
            cypher = f"""
            MATCH (e:Entity {{name: '{entity.name}'}})
            -[r]->(related)
            RETURN e, r, related
            LIMIT 20
            """
            results = await self.graph_store.query(cypher)
            graph_results.extend(results)
            
        # Step 4: Combine results with metadata
        return self._combine_results(vector_results, graph_results, query)
```

### 2.2 Parallel Hybrid with Advanced Fusion

```python
# app/agent/fusion.py
import numpy as np
from sentence_transformers import CrossEncoder

class HybridFusionReranker:
    def __init__(self, cross_encoder_model="cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.cross_encoder = CrossEncoder(cross_encoder_model)
        
    def reciprocal_rank_fusion(self, 
                              vector_results: List[Dict],
                              graph_results: List[Dict],
                              k: int = 60) -> List[Dict]:
        """RRF algorithm for combining ranked lists"""
        scores = {}
        
        # Score vector results
        for rank, result in enumerate(vector_results):
            doc_id = result.get('id', str(result))
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            
        # Score graph results
        for rank, result in enumerate(graph_results):
            doc_id = result.get('id', str(result))
            scores[doc_id] = scores.get(doc_id, 0) + 1 / (k + rank + 1)
            
        # Sort by combined score
        sorted_docs = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        # Reconstruct results
        fused_results = []
        for doc_id, score in sorted_docs:
            # Find original result
            for result in vector_results + graph_results:
                if result.get('id', str(result)) == doc_id:
                    result['rrf_score'] = score
                    fused_results.append(result)
                    break
                    
        return fused_results
        
    def cross_encoder_rerank(self,
                           results: List[Dict],
                           query: str,
                           top_k: int = 10) -> List[Dict]:
        """Rerank using cross-encoder for precision"""
        # Prepare pairs for cross-encoder
        pairs = [[query, r.get('content', str(r))] for r in results]
        
        # Get relevance scores
        scores = self.cross_encoder.predict(pairs)
        
        # Add scores to results
        for i, score in enumerate(scores):
            results[i]['relevance_score'] = float(score)
            
        # Sort by relevance
        reranked = sorted(results, 
                         key=lambda x: x['relevance_score'], 
                         reverse=True)
        
        return reranked[:top_k]
```

## Phase 3: Self-Correction and Reflection (Week 3)

### 3.1 Context Grading

```python
# app/agent/grading.py
class ContextGrader:
    def __init__(self, llm):
        self.llm = llm
        self.grading_prompt = """
        You are a relevance grader. Score the following context 
        for its relevance to the query.
        
        Query: {query}
        Context: {context}
        
        Provide a score from 0-1 and brief reasoning.
        Output format:
        {
            "score": 0.8,
            "reasoning": "Context directly addresses the query"
        }
        """
        
    async def grade(self, query: str, context: List[Dict]) -> Dict:
        # Prepare context summary
        context_text = "\n".join([
            f"- {c.get('content', str(c))[:200]}..." 
            for c in context[:5]
        ])
        
        response = await self.llm.astructured_output(
            self.grading_prompt.format(
                query=query,
                context=context_text
            ),
            output_schema=GradingOutput
        )
        
        return {
            "score": response.score,
            "reasoning": response.reasoning,
            "needs_refinement": response.score < 0.7
        }
```

### 3.2 Query Rewriting

```python
# app/agent/rewriter.py
class QueryRewriter:
    def __init__(self, llm):
        self.llm = llm
        self.rewrite_prompt = """
        The following query didn't retrieve relevant results.
        Rewrite it to be more specific and likely to find good matches.
        
        Original query: {query}
        Failed strategy: {strategy}
        Context quality: {quality_score}
        
        Provide 2-3 alternative formulations that might work better.
        """
        
    async def rewrite(self, state: AgentState) -> List[str]:
        response = await self.llm.astructured_output(
            self.rewrite_prompt.format(
                query=state["messages"][-1].content,
                strategy=state["strategy"],
                quality_score=state["quality_score"]
            ),
            output_schema=RewrittenQueries
        )
        
        return response.alternatives
```

## Phase 4: Production Optimizations (Week 4)

### 4.1 Caching Layer

```python
# app/agent/caching.py
from functools import lru_cache
import hashlib
import redis

class SemanticCache:
    def __init__(self, redis_client, embedding_model, threshold=0.85):
        self.redis = redis_client
        self.embedder = embedding_model
        self.threshold = threshold
        
    async def get_or_compute(self, query: str, compute_fn):
        # Generate query embedding
        query_embedding = await self.embedder.encode(query)
        
        # Search for similar cached queries
        similar = self._search_similar(query_embedding)
        
        if similar and similar['score'] > self.threshold:
            return similar['result']
            
        # Compute new result
        result = await compute_fn(query)
        
        # Cache with embedding
        self._cache_result(query, query_embedding, result)
        
        return result
```

### 4.2 Performance Monitoring

```python
# app/monitoring/metrics.py
from dataclasses import dataclass
from datetime import datetime
import structlog

@dataclass
class QueryMetrics:
    query: str
    strategy: str
    tools_used: List[str]
    latency_ms: float
    context_quality: float
    rewrite_count: int
    final_success: bool
    
class MetricsCollector:
    def __init__(self):
        self.logger = structlog.get_logger()
        self.metrics = []
        
    def log_query(self, state: AgentState, start_time: datetime):
        metrics = QueryMetrics(
            query=state["messages"][0].content,
            strategy=state["strategy"],
            tools_used=self._extract_tools(state),
            latency_ms=(datetime.now() - start_time).total_seconds() * 1000,
            context_quality=state.get("quality_score", 0),
            rewrite_count=state.get("retry_count", 0),
            final_success=state.get("quality_score", 0) > 0.7
        )
        
        self.metrics.append(metrics)
        self.logger.info("query_completed", **metrics.__dict__)
        
    def analyze_routing_accuracy(self) -> Dict:
        """Analyze which queries are being misrouted"""
        misrouted = [
            m for m in self.metrics 
            if m.context_quality < 0.5 and m.rewrite_count > 0
        ]
        
        return {
            "total_queries": len(self.metrics),
            "misrouted_count": len(misrouted),
            "misrouted_patterns": self._extract_patterns(misrouted),
            "avg_quality_by_strategy": self._quality_by_strategy()
        }
```

## Implementation Timeline

### Week 1: Core State Machine
- Day 1-2: Implement LangGraph workflow with all nodes
- Day 3-4: Build deterministic router with business rules
- Day 5: Integration testing with existing tools

### Week 2: Advanced Patterns
- Day 1-2: Sequential hybrid retriever
- Day 3-4: Parallel hybrid with RRF and reranking
- Day 5: Performance optimization

### Week 3: Self-Correction
- Day 1-2: Context grading system
- Day 3-4: Query rewriting logic
- Day 5: Error handling and fallbacks

### Week 4: Production Ready
- Day 1-2: Caching and optimization
- Day 3-4: Monitoring and analytics
- Day 5: Documentation and deployment

## Success Metrics

1. **Routing Accuracy**: 95% of business queries use appropriate tools
2. **Context Quality**: Average grading score > 0.8
3. **Latency**: < 200ms for routing decision
4. **Self-Correction**: 80% of failed queries succeed after rewrite
5. **Cost Efficiency**: 30% reduction in LLM calls through caching

## Conclusion

This revised plan incorporates the expert research findings to build a true agentic system. By implementing explicit state machines, deterministic routing, and self-correction mechanisms, we transform from hoping the LLM makes good choices to guaranteeing appropriate tool selection through debuggable, observable workflows.