"""Base retriever interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from src.state.types import RetrievalResult


class BaseRetriever(ABC):
    """Abstract base class for all retrievers."""
    
    @abstractmethod
    async def retrieve(
        self, 
        query: str, 
        k: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[RetrievalResult]:
        """Retrieve relevant documents/nodes for the query.
        
        Args:
            query: The search query
            k: Number of results to return
            filters: Optional filters to apply
            
        Returns:
            List of retrieval results
        """
        pass
    
    @abstractmethod
    def get_retriever_type(self) -> str:
        """Get the type identifier for this retriever."""
        pass