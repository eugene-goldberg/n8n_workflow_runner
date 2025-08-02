"""LlamaIndex Knowledge Graph Ingestion Pipeline"""

from .pipeline import KnowledgeGraphPipeline
from .config import Config

__all__ = ['KnowledgeGraphPipeline', 'Config']
__version__ = '0.1.0'