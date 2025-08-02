"""Multi-hop relationship discovery"""

import asyncio
import logging
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx

from .models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    PathAnalysis,
    RelationshipDiscoveryContext
)

logger = logging.getLogger(__name__)


class MultiHopRelationshipDiscoverer:
    """Find complex multi-entity relationships"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize multi-hop discoverer
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._get_default_config()
        self.graph = nx.DiGraph()
        self._path_cache: Dict[Tuple[str, str], List[List[Entity]]] = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "max_hops": 3,
            "min_path_strength": 0.5,
            "enable_llm_interpretation": True,
            "path_scoring": {
                "edge_weight_factor": 0.7,
                "path_length_penalty": 0.1,
                "loop_penalty": 0.5
            },
            "performance": {
                "max_paths_per_pair": 5,
                "cache_paths": True
            }
        }
    
    async def discover_multi_hop(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        max_hops: Optional[int] = None,
        context: Optional[RelationshipDiscoveryContext] = None
    ) -> List[Relationship]:
        """Discover multi-hop relationships between entities
        
        Args:
            entities: List of entities
            relationships: Existing direct relationships
            max_hops: Maximum number of hops to consider
            context: Optional discovery context
            
        Returns:
            List of discovered multi-hop relationships
        """
        if not entities or not relationships:
            return []
        
        max_hops = max_hops or self.config["max_hops"]
        context = context or RelationshipDiscoveryContext()
        
        # Build graph from entities and relationships
        self._build_graph(entities, relationships)
        
        # Find multi-hop paths
        multi_hop_relationships = []
        
        # Process entities in batches for efficiency
        batch_size = 100
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            batch_relationships = await self._process_entity_batch(
                batch, entities, max_hops, context
            )
            multi_hop_relationships.extend(batch_relationships)
        
        return multi_hop_relationships
    
    def _build_graph(self, entities: List[Entity], relationships: List[Relationship]):
        """Build NetworkX graph from entities and relationships"""
        self.graph.clear()
        
        # Add nodes
        for entity in entities:
            self.graph.add_node(
                entity.id,
                entity=entity,
                type=entity.type,
                name=entity.get_name()
            )
        
        # Add edges
        for rel in relationships:
            weight = self._calculate_edge_weight(rel)
            
            self.graph.add_edge(
                rel.source.id,
                rel.target.id,
                relationship=rel,
                weight=weight,
                type=rel.relationship_type.value
            )
            
            # Add reverse edge for bidirectional relationships
            if rel.direction == RelationshipDirection.BIDIRECTIONAL:
                self.graph.add_edge(
                    rel.target.id,
                    rel.source.id,
                    relationship=rel,
                    weight=weight,
                    type=rel.relationship_type.value
                )
    
    def _calculate_edge_weight(self, relationship: Relationship) -> float:
        """Calculate edge weight based on relationship properties"""
        base_weight = relationship.confidence
        
        # Adjust based on strength
        strength_multipliers = {
            RelationshipStrength.STRONG: 1.0,
            RelationshipStrength.MODERATE: 0.7,
            RelationshipStrength.WEAK: 0.4
        }
        
        weight = base_weight * strength_multipliers.get(
            relationship.strength,
            0.5
        )
        
        return weight
    
    async def _process_entity_batch(
        self,
        batch: List[Entity],
        all_entities: List[Entity],
        max_hops: int,
        context: RelationshipDiscoveryContext
    ) -> List[Relationship]:
        """Process a batch of entities to find multi-hop relationships"""
        relationships = []
        
        for source_entity in batch:
            # Find interesting targets (different type, not directly connected)
            targets = self._find_interesting_targets(source_entity, all_entities)
            
            for target_entity in targets:
                # Check cache first
                cache_key = (source_entity.id, target_entity.id)
                if self.config["performance"]["cache_paths"] and cache_key in self._path_cache:
                    paths = self._path_cache[cache_key]
                else:
                    # Find paths between source and target
                    paths = self._find_paths(
                        source_entity.id,
                        target_entity.id,
                        max_hops
                    )
                    
                    if self.config["performance"]["cache_paths"]:
                        self._path_cache[cache_key] = paths
                
                # Analyze paths and create relationships
                for path in paths:
                    if len(path) <= 2:  # Skip direct relationships
                        continue
                    
                    analysis = await self._analyze_path(path)
                    
                    if analysis.score >= self.config["min_path_strength"]:
                        rel = self._create_multi_hop_relationship(
                            source_entity,
                            target_entity,
                            path,
                            analysis
                        )
                        
                        if context.should_include_relationship(rel):
                            relationships.append(rel)
        
        return relationships
    
    def _find_interesting_targets(
        self,
        source: Entity,
        all_entities: List[Entity]
    ) -> List[Entity]:
        """Find potentially interesting target entities"""
        targets = []
        
        # Get directly connected entities
        direct_neighbors = set(self.graph.neighbors(source.id))
        
        for entity in all_entities:
            # Skip self and direct neighbors
            if entity.id == source.id or entity.id in direct_neighbors:
                continue
            
            # Prioritize different entity types
            if entity.type != source.type:
                targets.append(entity)
            # Or entities with potential business relevance
            elif self._has_business_relevance(source, entity):
                targets.append(entity)
        
        return targets[:50]  # Limit to prevent explosion
    
    def _has_business_relevance(self, entity1: Entity, entity2: Entity) -> bool:
        """Check if two entities might have business relevance"""
        # Check for shared attributes
        shared_attrs = set(entity1.attributes.keys()) & set(entity2.attributes.keys())
        
        for attr in shared_attrs:
            if attr in ["industry", "region", "product", "team"]:
                if entity1.attributes[attr] == entity2.attributes[attr]:
                    return True
        
        return False
    
    def _find_paths(
        self,
        source_id: str,
        target_id: str,
        max_hops: int
    ) -> List[List[Entity]]:
        """Find paths between two entities"""
        if source_id not in self.graph or target_id not in self.graph:
            return []
        
        paths = []
        
        try:
            # Use NetworkX to find simple paths
            nx_paths = nx.all_simple_paths(
                self.graph,
                source_id,
                target_id,
                cutoff=max_hops
            )
            
            # Convert to entity paths
            max_paths = self.config["performance"]["max_paths_per_pair"]
            for i, nx_path in enumerate(nx_paths):
                if i >= max_paths:
                    break
                
                entity_path = []
                for node_id in nx_path:
                    node_data = self.graph.nodes[node_id]
                    entity_path.append(node_data["entity"])
                
                paths.append(entity_path)
                
        except nx.NetworkXNoPath:
            pass
        
        return paths
    
    async def _analyze_path(self, path: List[Entity]) -> PathAnalysis:
        """Analyze a multi-hop path to determine significance"""
        edge_strengths = []
        
        # Calculate edge strengths
        for i in range(len(path) - 1):
            edge_data = self.graph.get_edge_data(path[i].id, path[i+1].id)
            if edge_data:
                edge_strengths.append(edge_data["weight"])
            else:
                edge_strengths.append(0.5)  # Default weight
        
        # Calculate path score
        path_score = self._calculate_path_score(edge_strengths, len(path))
        
        # Get interpretation
        interpretation = await self._interpret_path(path, edge_strengths)
        
        # Find bottlenecks (weakest links)
        bottlenecks = self._find_bottlenecks(path, edge_strengths)
        
        return PathAnalysis(
            path=path,
            score=path_score,
            interpretation=interpretation,
            edge_strengths=edge_strengths,
            bottlenecks=bottlenecks,
            actionable_insight=self._generate_insight(path, interpretation)
        )
    
    def _calculate_path_score(self, edge_strengths: List[float], path_length: int) -> float:
        """Calculate overall path score"""
        if not edge_strengths:
            return 0.0
        
        config = self.config["path_scoring"]
        
        # Average edge strength
        avg_strength = sum(edge_strengths) / len(edge_strengths)
        
        # Length penalty
        length_penalty = config["path_length_penalty"] * (path_length - 2)
        
        # Final score
        score = (avg_strength * config["edge_weight_factor"]) - length_penalty
        
        return max(0.0, min(1.0, score))
    
    async def _interpret_path(
        self,
        path: List[Entity],
        edge_strengths: List[float]
    ) -> str:
        """Interpret the meaning of a path"""
        if not self.config["enable_llm_interpretation"]:
            return self._simple_path_interpretation(path)
        
        # For now, use simple interpretation
        # TODO: Integrate with LLM for advanced interpretation
        return self._simple_path_interpretation(path)
    
    def _simple_path_interpretation(self, path: List[Entity]) -> str:
        """Simple rule-based path interpretation"""
        path_types = [entity.type for entity in path]
        
        # Common patterns
        if path_types == ["Customer", "Project", "Team"]:
            return "Customer connected to Team through Project engagement"
        elif path_types == ["Risk", "Customer", "Subscription"]:
            return "Risk impacts Customer's Subscription"
        elif path_types == ["Team", "Project", "Objective"]:
            return "Team working toward Objective through Project"
        elif "Risk" in path_types and "Customer" in path_types:
            return f"Risk cascade affecting Customer through {len(path)-2} intermediate steps"
        else:
            return f"{path[0].type} influences {path[-1].type} through {len(path)-2} intermediate connections"
    
    def _find_bottlenecks(
        self,
        path: List[Entity],
        edge_strengths: List[float]
    ) -> List[Tuple[Entity, Entity]]:
        """Find weak links in the path"""
        bottlenecks = []
        
        if not edge_strengths:
            return bottlenecks
        
        # Find edges significantly weaker than average
        avg_strength = sum(edge_strengths) / len(edge_strengths)
        threshold = avg_strength * 0.7
        
        for i, strength in enumerate(edge_strengths):
            if strength < threshold and i < len(path) - 1:
                bottlenecks.append((path[i], path[i + 1]))
        
        return bottlenecks
    
    def _generate_insight(self, path: List[Entity], interpretation: str) -> str:
        """Generate actionable business insight from path"""
        source = path[0]
        target = path[-1]
        
        insights = {
            ("Customer", "Risk"): f"Monitor {source.get_name()} - indirect risk exposure through supply chain",
            ("Team", "Customer"): f"{source.get_name()} indirectly impacts {target.get_name()} - consider direct engagement",
            ("Risk", "Objective"): f"Risk '{source.get_name()}' may affect objective '{target.get_name()}' - implement mitigation",
            ("Customer", "Team"): f"Strengthen connection between {source.get_name()} and {target.get_name()} for better collaboration"
        }
        
        key = (source.type, target.type)
        return insights.get(key, f"Consider the indirect relationship: {interpretation}")
    
    def _create_multi_hop_relationship(
        self,
        source: Entity,
        target: Entity,
        path: List[Entity],
        analysis: PathAnalysis
    ) -> Relationship:
        """Create a multi-hop relationship from analysis"""
        # Determine relationship type based on path
        rel_type = self._determine_multi_hop_type(source, target, path)
        
        # Create evidence from path
        evidence = [
            f"Connected via {len(path)-2} hop(s): {' -> '.join(e.get_name() for e in path)}",
            analysis.interpretation
        ]
        
        if analysis.bottlenecks:
            evidence.append(
                f"Weak link: {analysis.bottlenecks[0][0].get_name()} -> {analysis.bottlenecks[0][1].get_name()}"
            )
        
        return Relationship(
            source=source,
            target=target,
            relationship_type=rel_type,
            direction=RelationshipDirection.UNIDIRECTIONAL,
            strength=self._score_to_strength(analysis.score),
            confidence=analysis.score,
            evidence=evidence,
            path=path,
            metadata={
                "path_analysis": {
                    "interpretation": analysis.interpretation,
                    "actionable_insight": analysis.actionable_insight,
                    "edge_strengths": analysis.edge_strengths
                }
            }
        )
    
    def _determine_multi_hop_type(
        self,
        source: Entity,
        target: Entity,
        path: List[Entity]
    ) -> RelationshipType:
        """Determine the type of multi-hop relationship"""
        # Check for specific patterns
        path_types = [e.type for e in path]
        
        if source.type == "Customer" and target.type == "Team":
            return RelationshipType.CONNECTED_VIA
        elif source.type == "Risk" and target.type in ["Customer", "Objective"]:
            return RelationshipType.INDIRECTLY_AFFECTS
        elif source.type == "Objective" and target.type == "Customer":
            return RelationshipType.INFLUENCES_THROUGH
        elif "Risk" in path_types[1:-1]:  # Risk in the middle
            return RelationshipType.CASCADES_TO
        else:
            return RelationshipType.CONNECTED_VIA
    
    def _score_to_strength(self, score: float) -> RelationshipStrength:
        """Convert numeric score to strength enum"""
        if score >= 0.8:
            return RelationshipStrength.STRONG
        elif score >= 0.5:
            return RelationshipStrength.MODERATE
        else:
            return RelationshipStrength.WEAK
    
    def get_path_between(
        self,
        source_id: str,
        target_id: str,
        max_hops: Optional[int] = None
    ) -> Optional[List[Entity]]:
        """Get shortest path between two entities
        
        Args:
            source_id: Source entity ID
            target_id: Target entity ID
            max_hops: Maximum number of hops
            
        Returns:
            Shortest path as list of entities, or None if no path exists
        """
        max_hops = max_hops or self.config["max_hops"]
        
        try:
            path_ids = nx.shortest_path(
                self.graph,
                source_id,
                target_id,
                weight="weight"
            )
            
            if len(path_ids) > max_hops + 1:
                return None
            
            # Convert to entities
            path = []
            for node_id in path_ids:
                node_data = self.graph.nodes[node_id]
                path.append(node_data["entity"])
            
            return path
            
        except (nx.NetworkXNoPath, KeyError):
            return None
    
    def clear_cache(self):
        """Clear path cache"""
        self._path_cache.clear()