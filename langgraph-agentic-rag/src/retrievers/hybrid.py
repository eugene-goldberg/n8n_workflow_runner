"""Hybrid retriever combining vector search with keyword/full-text search."""

import logging
from typing import List, Dict, Any, Optional

from neo4j_graphrag.retrievers import HybridRetriever as Neo4jHybridRetriever
from neo4j_graphrag.embeddings.openai import OpenAIEmbeddings as Neo4jOpenAIEmbeddings

from config.settings import settings
from src.state.types import RetrievalResult
from .base import BaseRetriever

logger = logging.getLogger(__name__)


class HybridRetriever(BaseRetriever):
    """Hybrid retriever combining semantic and keyword search."""
    
    def __init__(self):
        """Initialize the hybrid retriever using Neo4j."""
        # Initialize Neo4j embeddings
        self.embeddings = Neo4jOpenAIEmbeddings(
            api_key=settings.openai.api_key,
            model="text-embedding-ada-002"
        )
        
        # Initialize the Neo4j hybrid retriever using spyro indexes
        self.retriever = Neo4jHybridRetriever(
            driver=self._get_neo4j_driver(),
            vector_index_name="spyro_vector_index",  # Use spyro vector index
            fulltext_index_name="spyro_fulltext_index",  # Use spyro fulltext index
            embedder=self.embeddings,
            return_properties=["text", "source", "metadata"]  # spyro uses 'text' property
        )
        
        logger.info("Initialized Neo4j hybrid retriever")
    
    def _get_neo4j_driver(self):
        """Get Neo4j driver instance."""
        from neo4j import GraphDatabase
        return GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve using combined vector and keyword search.
        
        Args:
            query: The search query
            k: Number of results to return
            filters: Optional filters (not used in current implementation)
            
        Returns:
            List of retrieval results
        """
        try:
            # Perform hybrid search
            results = self.retriever.search(
                query_text=query,
                top_k=k
            )
            
            # Convert to RetrievalResult format
            retrieval_results = []
            for result in results:
                # Extract content and metadata from the result
                content = result.content
                metadata = result.metadata if hasattr(result, 'metadata') else {}
                score = result.score if hasattr(result, 'score') else 1.0
                
                retrieval_result = RetrievalResult(
                    content=content,
                    metadata=metadata,
                    source=metadata.get("source", "neo4j_hybrid"),
                    score=float(score)
                )
                retrieval_results.append(retrieval_result)
            
            logger.info(f"Hybrid search returned {len(retrieval_results)} results for query: {query[:50]}...")
            return retrieval_results
            
        except Exception as e:
            logger.error(f"Error in hybrid retrieval: {e}")
            return []
    
    def get_retriever_type(self) -> str:
        """Get the type identifier for this retriever."""
        return "hybrid"