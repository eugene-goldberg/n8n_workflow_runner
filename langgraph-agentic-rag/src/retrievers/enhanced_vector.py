"""Enhanced vector retriever that handles entity-only embeddings."""

import logging
from typing import List, Dict, Any, Optional
from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings

from config.settings import settings
from src.state.types import RetrievalResult
from .base import BaseRetriever

logger = logging.getLogger(__name__)


class EnhancedVectorRetriever(BaseRetriever):
    """Enhanced vector retriever that can search entities by type and relationships."""
    
    def __init__(self):
        """Initialize the enhanced vector retriever."""
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai.api_key
        )
        self.driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
        logger.info("Initialized enhanced vector retriever")
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve entities using vector similarity and enriched context.
        
        Strategy:
        1. Embed the query
        2. Find similar entities by name embedding
        3. Enrich results with entity relationships and properties
        
        Args:
            query: The search query
            k: Number of results to return
            filters: Optional filters (e.g., entity type)
            
        Returns:
            List of enriched retrieval results
        """
        try:
            # Generate embedding for the query
            query_embedding = self.embeddings.embed_query(query)
            
            # Build the Cypher query for vector search with enrichment
            cypher_query = """
            // Vector similarity search on entity index
            CALL db.index.vector.queryNodes('entity', $k, $embedding)
            YIELD node, score
            
            // Filter by entity type if specified
            WHERE $entity_type IS NULL OR $entity_type IN labels(node)
            
            // Enrich with relationships (limited to avoid too much data)
            OPTIONAL MATCH (node)-[r]-(related)
            WITH node, score, 
                 collect(DISTINCT {
                    type: type(r), 
                    related_entity: labels(related)[0], 
                    related_name: related.name
                 })[..5] as relationships
            
            // Get entity properties and context
            RETURN 
                labels(node) as labels,
                node.name as name,
                properties(node) as properties,
                relationships,
                score
            ORDER BY score DESC
            LIMIT $k
            """
            
            # Extract entity type filter if provided
            entity_type = filters.get('entity_type') if filters else None
            
            with self.driver.session() as session:
                result = session.run(
                    cypher_query,
                    embedding=query_embedding,
                    k=k * 2,  # Get more candidates for filtering
                    entity_type=entity_type
                )
                
                retrieval_results = []
                for record in result:
                    # Build context from entity information
                    labels = record['labels']
                    name = record['name']
                    properties = record['properties']
                    relationships = record['relationships']
                    score = record['score']
                    
                    # Create readable content
                    content_parts = [f"Entity: {name}"]
                    content_parts.append(f"Type: {', '.join([l for l in labels if l not in ['__Entity__', '__Node__']])}")
                    
                    # Add key properties
                    for key, value in properties.items():
                        if key not in ['embedding', 'id', 'triplet_source_id', 'name']:
                            content_parts.append(f"{key}: {value}")
                    
                    # Add relationships
                    if relationships:
                        content_parts.append("\nRelationships:")
                        for rel in relationships:
                            if rel['related_name']:
                                content_parts.append(f"  - {rel['type']} -> {rel['related_entity']}: {rel['related_name']}")
                    
                    content = "\n".join(content_parts)
                    
                    retrieval_result = RetrievalResult(
                        content=content,
                        metadata={
                            "entity_type": labels,
                            "entity_name": name,
                            "relationship_count": len(relationships)
                        },
                        source="enhanced_vector",
                        score=float(score)
                    )
                    retrieval_results.append(retrieval_result)
                
                # Limit to k results
                retrieval_results = retrieval_results[:k]
                
                logger.info(f"Enhanced vector search returned {len(retrieval_results)} results for query: {query[:50]}...")
                return retrieval_results
                
        except Exception as e:
            logger.error(f"Error in enhanced vector retrieval: {e}")
            return []
    
    def get_retriever_type(self) -> str:
        """Get the type identifier for this retriever."""
        return "enhanced_vector"
    
    def __del__(self):
        """Clean up driver connection."""
        if hasattr(self, 'driver'):
            self.driver.close()