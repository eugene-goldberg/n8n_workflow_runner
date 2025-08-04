"""Vector-based retriever using pgvector or Neo4j vector index."""

import logging
from typing import List, Dict, Any, Optional

from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import PGVector
from langchain_community.vectorstores import Neo4jVector

from config.settings import settings
from src.state.types import RetrievalResult
from .base import BaseRetriever

logger = logging.getLogger(__name__)


class VectorRetriever(BaseRetriever):
    """Pure semantic search retriever using vector embeddings."""
    
    def __init__(self, use_neo4j: bool = True):  # Default to Neo4j for spyro data
        """Initialize the vector retriever.
        
        Args:
            use_neo4j: If True, use Neo4j vector index. Otherwise use pgvector.
        """
        self.use_neo4j = use_neo4j
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=settings.openai.api_key
        )
        
        if use_neo4j:
            self._init_neo4j_store()
        else:
            self._init_pgvector_store()
    
    def _init_pgvector_store(self):
        """Initialize pgvector store."""
        self.vector_store = PGVector(
            connection_string=settings.postgres.pgvector_connection_string,
            embedding_function=self.embeddings,
            collection_name="documents",
            distance_strategy="cosine"
        )
        logger.info("Initialized pgvector store")
    
    def _init_neo4j_store(self):
        """Initialize Neo4j vector store using spyro index."""
        try:
            # Use existing spyro_vector_index
            self.vector_store = Neo4jVector.from_existing_index(
                embedding=self.embeddings,
                url=settings.neo4j.uri,
                username=settings.neo4j.username,
                password=settings.neo4j.password,
                index_name="spyro_vector_index",  # Use spyro index
                node_label="__Chunk__",            # Spyro uses __Chunk__
                text_node_property="text",         # Property name for text
                embedding_node_property="embedding"
            )
            logger.info("Initialized Neo4j vector store with spyro_vector_index")
        except Exception as e:
            logger.warning(f"Failed to use spyro index, trying entity index: {e}")
            # Fallback to entity index
            self.vector_store = Neo4jVector.from_existing_index(
                embedding=self.embeddings,
                url=settings.neo4j.uri,
                username=settings.neo4j.username,
                password=settings.neo4j.password,
                index_name="entity",
                node_label="__Entity__",
                text_node_property="name",
                embedding_node_property="embedding"
            )
            logger.info("Initialized Neo4j vector store with entity index")
    
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve documents using semantic similarity search.
        
        Args:
            query: The search query
            k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            List of retrieval results
        """
        try:
            # Perform similarity search
            docs_with_scores = self.vector_store.similarity_search_with_score(
                query, 
                k=k,
                filter=filters
            )
            
            # Convert to RetrievalResult format
            results = []
            for doc, score in docs_with_scores:
                result = RetrievalResult(
                    content=doc.page_content,
                    metadata=doc.metadata,
                    source=doc.metadata.get("source", "neo4j_vector" if self.use_neo4j else "pgvector"),
                    score=float(score)
                )
                results.append(result)
            
            logger.info(f"Vector search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in vector retrieval: {e}")
            return []
    
    def get_retriever_type(self) -> str:
        """Get the type identifier for this retriever."""
        return "neo4j_vector" if self.use_neo4j else "pgvector"