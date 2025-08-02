"""Graph pattern recognition for relationship discovery"""

import asyncio
import logging
from collections import defaultdict, Counter
from typing import Dict, List, Optional, Set, Tuple, Any
import networkx as nx
from networkx.algorithms import community

from .models import (
    Entity,
    Relationship,
    RelationshipType,
    RelationshipDirection,
    RelationshipStrength,
    GraphPattern,
    CollaborationPattern,
    RelationshipDiscoveryContext
)

logger = logging.getLogger(__name__)


class GraphPatternRecognizer:
    """Identify patterns in entity relationship graphs"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize pattern recognizer
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or self._get_default_config()
        self._pattern_cache: Dict[str, List[GraphPattern]] = {}
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "patterns": {
                "hub_detection": {
                    "enable": True,
                    "min_connections": 5,
                    "centrality_threshold": 0.7
                },
                "community_detection": {
                    "enable": True,
                    "min_community_size": 3,
                    "algorithm": "louvain"  # louvain, girvan_newman, label_propagation
                },
                "triangle_detection": {
                    "enable": True,
                    "min_triangle_strength": 0.5
                },
                "chain_detection": {
                    "enable": True,
                    "min_chain_length": 3,
                    "max_chain_length": 10
                },
                "star_detection": {
                    "enable": True,
                    "min_spokes": 4
                }
            },
            "scoring": {
                "centrality_weight": 0.4,
                "density_weight": 0.3,
                "strength_weight": 0.3
            },
            "performance": {
                "cache_patterns": True,
                "parallel_detection": True
            }
        }
    
    async def recognize_patterns(
        self,
        entities: List[Entity],
        relationships: List[Relationship],
        context: Optional[RelationshipDiscoveryContext] = None
    ) -> List[GraphPattern]:
        """Recognize patterns in entity relationship graph
        
        Args:
            entities: List of entities
            relationships: List of relationships
            context: Optional discovery context
            
        Returns:
            List of discovered graph patterns
        """
        if not entities or not relationships:
            return []
        
        context = context or RelationshipDiscoveryContext()
        
        # Build graph
        graph = self._build_graph(entities, relationships)
        
        # Check cache
        cache_key = f"{len(entities)}_{len(relationships)}"
        if self.config["performance"]["cache_patterns"] and cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]
        
        patterns = []
        
        # Detect different pattern types
        detection_tasks = []
        
        if self.config["patterns"]["hub_detection"]["enable"]:
            detection_tasks.append(self._detect_hubs(graph, entities))
        
        if self.config["patterns"]["community_detection"]["enable"]:
            detection_tasks.append(self._detect_communities(graph, entities))
        
        if self.config["patterns"]["triangle_detection"]["enable"]:
            detection_tasks.append(self._detect_triangles(graph, entities, relationships))
        
        if self.config["patterns"]["chain_detection"]["enable"]:
            detection_tasks.append(self._detect_chains(graph, entities))
        
        if self.config["patterns"]["star_detection"]["enable"]:
            detection_tasks.append(self._detect_stars(graph, entities))
        
        # Run detection in parallel if enabled
        if self.config["performance"]["parallel_detection"] and detection_tasks:
            pattern_sets = await asyncio.gather(*detection_tasks)
            for pattern_set in pattern_sets:
                patterns.extend(pattern_set)
        else:
            for task in detection_tasks:
                task_patterns = await task
                patterns.extend(task_patterns)
        
        # Score and rank patterns
        patterns = self._score_patterns(patterns, graph)
        
        # Cache results
        if self.config["performance"]["cache_patterns"]:
            self._pattern_cache[cache_key] = patterns
        
        return patterns
    
    def _build_graph(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> nx.Graph:
        """Build NetworkX graph from entities and relationships"""
        # Use undirected graph for pattern detection
        graph = nx.Graph()
        
        # Add nodes
        for entity in entities:
            graph.add_node(
                entity.id,
                entity=entity,
                type=entity.type,
                name=entity.get_name()
            )
        
        # Add edges
        for rel in relationships:
            weight = rel.confidence
            
            # Adjust weight based on strength
            if rel.strength == RelationshipStrength.STRONG:
                weight *= 1.2
            elif rel.strength == RelationshipStrength.WEAK:
                weight *= 0.8
            
            graph.add_edge(
                rel.source.id,
                rel.target.id,
                relationship=rel,
                weight=weight,
                type=rel.relationship_type.value
            )
        
        return graph
    
    async def _detect_hubs(
        self,
        graph: nx.Graph,
        entities: List[Entity]
    ) -> List[GraphPattern]:
        """Detect hub patterns (highly connected nodes)"""
        patterns = []
        config = self.config["patterns"]["hub_detection"]
        
        # Calculate centrality measures
        degree_centrality = nx.degree_centrality(graph)
        betweenness_centrality = nx.betweenness_centrality(graph, weight='weight')
        closeness_centrality = nx.closeness_centrality(graph, distance='weight')
        
        # Combine centrality measures
        combined_centrality = {}
        for node in graph.nodes():
            combined_centrality[node] = (
                degree_centrality.get(node, 0) * 0.4 +
                betweenness_centrality.get(node, 0) * 0.4 +
                closeness_centrality.get(node, 0) * 0.2
            )
        
        # Find hubs
        for node_id, centrality in combined_centrality.items():
            degree = graph.degree(node_id)
            
            if (degree >= config["min_connections"] and 
                centrality >= config["centrality_threshold"]):
                
                # Get hub entity and connected entities
                hub_entity = graph.nodes[node_id]["entity"]
                connected_entities = [
                    graph.nodes[neighbor]["entity"]
                    for neighbor in graph.neighbors(node_id)
                ]
                
                pattern = GraphPattern(
                    pattern_type="hub",
                    entities=[hub_entity] + connected_entities,
                    centrality_scores={
                        node_id: centrality,
                        **{e.id: combined_centrality.get(e.id, 0) 
                           for e in connected_entities}
                    },
                    metadata={
                        "hub_id": node_id,
                        "degree": degree,
                        "centrality_measures": {
                            "degree": degree_centrality[node_id],
                            "betweenness": betweenness_centrality[node_id],
                            "closeness": closeness_centrality[node_id]
                        }
                    }
                )
                
                patterns.append(pattern)
        
        # Create hub relationships
        for pattern in patterns:
            hub = pattern.get_central_entity()
            if hub:
                # Create HUB_OF relationships
                for entity in pattern.entities[1:]:  # Skip hub itself
                    rel = Relationship(
                        source=hub,
                        target=entity,
                        relationship_type=RelationshipType.HUB_OF,
                        direction=RelationshipDirection.UNIDIRECTIONAL,
                        strength=RelationshipStrength.STRONG,
                        confidence=pattern.centrality_scores[hub.id],
                        evidence=[
                            f"Hub pattern detected with {pattern.metadata['degree']} connections",
                            f"Centrality score: {pattern.centrality_scores[hub.id]:.2f}"
                        ]
                    )
        
        return patterns
    
    async def _detect_communities(
        self,
        graph: nx.Graph,
        entities: List[Entity]
    ) -> List[GraphPattern]:
        """Detect community patterns"""
        patterns = []
        config = self.config["patterns"]["community_detection"]
        
        # Detect communities based on algorithm
        if config["algorithm"] == "louvain":
            communities = community.louvain_communities(graph, weight='weight')
        elif config["algorithm"] == "label_propagation":
            communities = list(nx.community.label_propagation_communities(graph))
        else:  # girvan_newman
            comp = nx.community.girvan_newman(graph)
            communities = next(comp)
        
        # Process communities
        for comm_nodes in communities:
            if len(comm_nodes) < config["min_community_size"]:
                continue
            
            # Get community entities
            comm_entities = [
                graph.nodes[node_id]["entity"]
                for node_id in comm_nodes
            ]
            
            # Calculate community metrics
            subgraph = graph.subgraph(comm_nodes)
            density = nx.density(subgraph)
            
            # Calculate centrality within community
            comm_centrality = nx.degree_centrality(subgraph)
            
            pattern = GraphPattern(
                pattern_type="community",
                entities=comm_entities,
                centrality_scores={
                    entity.id: comm_centrality.get(entity.id, 0)
                    for entity in comm_entities
                },
                metadata={
                    "size": len(comm_nodes),
                    "density": density,
                    "cohesion": self._calculate_cohesion(subgraph),
                    "entity_types": Counter(e.type for e in comm_entities)
                }
            )
            
            patterns.append(pattern)
        
        return patterns
    
    async def _detect_triangles(
        self,
        graph: nx.Graph,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> List[GraphPattern]:
        """Detect triangle patterns (collaboration indicators)"""
        patterns = []
        config = self.config["patterns"]["triangle_detection"]
        
        # Find all triangles
        triangles = [clique for clique in nx.enumerate_all_cliques(graph) 
                    if len(clique) == 3]
        
        for triangle_nodes in triangles:
            # Get triangle entities
            triangle_entities = [
                graph.nodes[node_id]["entity"]
                for node_id in triangle_nodes
            ]
            
            # Calculate triangle strength
            edge_weights = []
            for i in range(3):
                for j in range(i+1, 3):
                    edge_data = graph.get_edge_data(
                        triangle_nodes[i],
                        triangle_nodes[j]
                    )
                    if edge_data:
                        edge_weights.append(edge_data.get("weight", 1.0))
            
            avg_strength = sum(edge_weights) / len(edge_weights) if edge_weights else 0
            
            if avg_strength >= config["min_triangle_strength"]:
                # Analyze triangle for collaboration
                collab_strength = self._analyze_collaboration_strength(
                    triangle_entities,
                    relationships
                )
                
                pattern = CollaborationPattern(
                    pattern_type="triangle",
                    entities=triangle_entities,
                    collaboration_strength=collab_strength,
                    supporting_evidence=self._get_triangle_evidence(
                        triangle_entities,
                        relationships
                    ),
                    collaboration_type=self._determine_collaboration_type(
                        triangle_entities
                    ),
                    metadata={
                        "avg_edge_strength": avg_strength,
                        "triangle_type": self._classify_triangle(triangle_entities)
                    }
                )
                
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_chains(
        self,
        graph: nx.Graph,
        entities: List[Entity]
    ) -> List[GraphPattern]:
        """Detect chain patterns (sequential dependencies)"""
        patterns = []
        config = self.config["patterns"]["chain_detection"]
        
        # Find nodes with degree 2 (potential chain members)
        degree_2_nodes = [n for n in graph.nodes() if graph.degree(n) == 2]
        
        # Track visited nodes
        visited = set()
        
        for start_node in degree_2_nodes:
            if start_node in visited:
                continue
            
            # Try to build chain from this node
            chain = self._build_chain(graph, start_node, visited, config)
            
            if len(chain) >= config["min_chain_length"]:
                chain_entities = [
                    graph.nodes[node_id]["entity"]
                    for node_id in chain
                ]
                
                pattern = GraphPattern(
                    pattern_type="chain",
                    entities=chain_entities,
                    metadata={
                        "chain_length": len(chain),
                        "chain_type": self._classify_chain(chain_entities),
                        "direction": self._determine_chain_direction(
                            chain_entities,
                            graph
                        )
                    }
                )
                
                patterns.append(pattern)
        
        return patterns
    
    async def _detect_stars(
        self,
        graph: nx.Graph,
        entities: List[Entity]
    ) -> List[GraphPattern]:
        """Detect star patterns (one central node with many leaves)"""
        patterns = []
        config = self.config["patterns"]["star_detection"]
        
        for node in graph.nodes():
            neighbors = list(graph.neighbors(node))
            
            if len(neighbors) < config["min_spokes"]:
                continue
            
            # Check if neighbors are mostly leaves (degree 1)
            leaf_count = sum(1 for n in neighbors if graph.degree(n) == 1)
            
            if leaf_count >= config["min_spokes"] * 0.7:  # 70% should be leaves
                center_entity = graph.nodes[node]["entity"]
                spoke_entities = [
                    graph.nodes[n]["entity"]
                    for n in neighbors
                ]
                
                pattern = GraphPattern(
                    pattern_type="star",
                    entities=[center_entity] + spoke_entities,
                    centrality_scores={
                        center_entity.id: 1.0,
                        **{e.id: 0.1 for e in spoke_entities}
                    },
                    metadata={
                        "center_id": node,
                        "spoke_count": len(neighbors),
                        "leaf_count": leaf_count,
                        "star_type": self._classify_star(center_entity, spoke_entities)
                    }
                )
                
                patterns.append(pattern)
        
        return patterns
    
    def _calculate_cohesion(self, subgraph: nx.Graph) -> float:
        """Calculate cohesion score for a subgraph"""
        if len(subgraph) < 2:
            return 0.0
        
        # Cohesion based on edge density and average weight
        density = nx.density(subgraph)
        
        total_weight = sum(
            data.get("weight", 1.0)
            for _, _, data in subgraph.edges(data=True)
        )
        
        num_edges = subgraph.number_of_edges()
        avg_weight = total_weight / num_edges if num_edges > 0 else 0
        
        return density * avg_weight
    
    def _analyze_collaboration_strength(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> float:
        """Analyze collaboration strength in a group"""
        if len(entities) < 3:
            return 0.0
        
        # Find relationships between entities
        entity_ids = {e.id for e in entities}
        relevant_rels = [
            r for r in relationships
            if r.source.id in entity_ids and r.target.id in entity_ids
        ]
        
        if not relevant_rels:
            return 0.0
        
        # Score based on relationship types
        collab_types = {
            RelationshipType.COLLABORATES_WITH: 1.0,
            RelationshipType.WORKS_WITH: 0.9,
            RelationshipType.ASSIGNED_TO: 0.7,
            RelationshipType.BELONGS_TO: 0.6
        }
        
        total_score = 0
        for rel in relevant_rels:
            rel_score = collab_types.get(rel.relationship_type, 0.5)
            total_score += rel_score * rel.confidence
        
        # Normalize by number of possible connections
        max_connections = len(entities) * (len(entities) - 1) / 2
        return min(1.0, total_score / max_connections)
    
    def _get_triangle_evidence(
        self,
        entities: List[Entity],
        relationships: List[Relationship]
    ) -> List[str]:
        """Get evidence for triangle collaboration"""
        evidence = []
        
        # Entity types involved
        entity_types = [e.type for e in entities]
        evidence.append(f"Triangle between: {', '.join(entity_types)}")
        
        # Find relationships
        entity_ids = {e.id for e in entities}
        triangle_rels = [
            r for r in relationships
            if r.source.id in entity_ids and r.target.id in entity_ids
        ]
        
        # Relationship types
        rel_types = set(r.relationship_type.value for r in triangle_rels)
        if rel_types:
            evidence.append(f"Relationships: {', '.join(rel_types)}")
        
        return evidence
    
    def _determine_collaboration_type(
        self,
        entities: List[Entity]
    ) -> Optional[str]:
        """Determine type of collaboration"""
        entity_types = [e.type for e in entities]
        
        # Common collaboration patterns
        if all(t == "Team" for t in entity_types):
            return "inter_team_collaboration"
        elif "Customer" in entity_types and "Team" in entity_types:
            return "customer_engagement"
        elif "Project" in entity_types:
            return "project_collaboration"
        else:
            return "general_collaboration"
    
    def _classify_triangle(self, entities: List[Entity]) -> str:
        """Classify triangle type"""
        types = sorted([e.type for e in entities])
        
        # Common patterns
        if types == ["Customer", "Product", "Team"]:
            return "customer_product_team"
        elif types == ["Team", "Team", "Team"]:
            return "team_collaboration"
        elif "Risk" in types:
            return "risk_triangle"
        else:
            return "mixed_triangle"
    
    def _build_chain(
        self,
        graph: nx.Graph,
        start_node: str,
        visited: Set[str],
        config: Dict[str, Any]
    ) -> List[str]:
        """Build a chain starting from a node"""
        chain = [start_node]
        visited.add(start_node)
        
        current = start_node
        
        # Try to extend chain in both directions
        for direction in [0, 1]:
            current = start_node
            
            while len(chain) < config["max_chain_length"]:
                neighbors = [
                    n for n in graph.neighbors(current)
                    if n not in visited and graph.degree(n) <= 2
                ]
                
                if not neighbors:
                    break
                
                # Choose next node (prefer degree 2)
                next_node = sorted(
                    neighbors,
                    key=lambda n: (graph.degree(n) == 2, n),
                    reverse=True
                )[0]
                
                if direction == 0:
                    chain.insert(0, next_node)
                else:
                    chain.append(next_node)
                
                visited.add(next_node)
                current = next_node
        
        return chain
    
    def _classify_chain(self, entities: List[Entity]) -> str:
        """Classify chain type based on entities"""
        types = [e.type for e in entities]
        
        # Check for common patterns
        if all(t == types[0] for t in types):
            return f"{types[0]}_chain"
        elif types == sorted(types):
            return "hierarchical_chain"
        else:
            return "mixed_chain"
    
    def _determine_chain_direction(
        self,
        entities: List[Entity],
        graph: nx.Graph
    ) -> str:
        """Determine if chain has a direction"""
        # This would analyze the actual relationships
        # For now, return a simple classification
        return "bidirectional"
    
    def _classify_star(
        self,
        center: Entity,
        spokes: List[Entity]
    ) -> str:
        """Classify star pattern type"""
        spoke_types = [e.type for e in spokes]
        
        if all(t == spoke_types[0] for t in spoke_types):
            return f"{center.type}_to_{spoke_types[0]}_star"
        else:
            return f"{center.type}_mixed_star"
    
    def _score_patterns(
        self,
        patterns: List[GraphPattern],
        graph: nx.Graph
    ) -> List[GraphPattern]:
        """Score and rank patterns by importance"""
        weights = self.config["scoring"]
        
        for pattern in patterns:
            # Base score on pattern type
            type_scores = {
                "hub": 0.9,
                "community": 0.8,
                "triangle": 0.7,
                "star": 0.7,
                "chain": 0.6
            }
            
            base_score = type_scores.get(pattern.pattern_type, 0.5)
            
            # Centrality component
            if pattern.centrality_scores:
                avg_centrality = sum(pattern.centrality_scores.values()) / len(pattern.centrality_scores)
                centrality_score = avg_centrality * weights["centrality_weight"]
            else:
                centrality_score = 0
            
            # Density component (for communities)
            if "density" in pattern.metadata:
                density_score = pattern.metadata["density"] * weights["density_weight"]
            else:
                density_score = 0
            
            # Strength component (for collaborations)
            if isinstance(pattern, CollaborationPattern):
                strength_score = pattern.collaboration_strength * weights["strength_weight"]
            else:
                strength_score = 0
            
            # Calculate final score
            pattern.metadata["importance_score"] = (
                base_score + centrality_score + density_score + strength_score
            )
        
        # Sort by importance
        patterns.sort(
            key=lambda p: p.metadata.get("importance_score", 0),
            reverse=True
        )
        
        return patterns
    
    def clear_cache(self):
        """Clear pattern cache"""
        self._pattern_cache.clear()