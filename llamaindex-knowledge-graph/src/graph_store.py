"""Neo4j graph store integration"""

from typing import List, Dict, Any, Optional
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from llama_index.core import PropertyGraphIndex
from llama_index.core.schema import BaseNode
from llama_index.core.query_engine import BaseQueryEngine
import logging

from .config import Config, GraphSchema
from .extractor import KnowledgeExtractor

logger = logging.getLogger(__name__)


class Neo4jKnowledgeGraph:
    """Manage Neo4j knowledge graph operations"""
    
    def __init__(self, config: Config, schema: GraphSchema = None):
        """
        Initialize Neo4j knowledge graph
        
        Args:
            config: Configuration object
            schema: Graph schema definition
        """
        self.config = config
        self.schema = schema or GraphSchema()
        
        # Initialize Neo4j store
        self.graph_store = Neo4jPropertyGraphStore(
            username=config.neo4j_username,
            password=config.neo4j_password,
            url=config.neo4j_uri,
            database=config.neo4j_database
        )
        
        # Initialize knowledge extractor
        self.extractor = KnowledgeExtractor(
            llm_model=config.llm_model,
            temperature=config.llm_temperature,
            schema=self.schema
        )
        
        self.index: Optional[PropertyGraphIndex] = None
        
    def build_graph(self, nodes: List[BaseNode], show_progress: bool = True) -> PropertyGraphIndex:
        """
        Build knowledge graph from nodes
        
        Args:
            nodes: List of nodes to process
            show_progress: Show progress during extraction
            
        Returns:
            PropertyGraphIndex instance
        """
        logger.info(f"Building knowledge graph from {len(nodes)} nodes")
        
        # Create property graph index
        self.index = PropertyGraphIndex(
            nodes=nodes,
            property_graph_store=self.graph_store,
            kg_extractors=[self.extractor.kg_extractor],
            show_progress=show_progress
        )
        
        logger.info("Knowledge graph built successfully")
        return self.index
    
    def get_query_engine(self) -> BaseQueryEngine:
        """
        Get query engine for the knowledge graph
        
        Returns:
            Query engine instance
        """
        if not self.index:
            raise ValueError("Knowledge graph not built yet. Call build_graph first.")
        
        return self.index.as_query_engine()
    
    def query(self, query_text: str) -> str:
        """
        Query the knowledge graph
        
        Args:
            query_text: Natural language query
            
        Returns:
            Query response
        """
        query_engine = self.get_query_engine()
        response = query_engine.query(query_text)
        return str(response)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the knowledge graph
        
        Returns:
            Dictionary of statistics
        """
        stats = {
            "node_count": 0,
            "relationship_count": 0,
            "node_types": {},
            "relationship_types": {}
        }
        
        try:
            # Count nodes
            result = self.graph_store._driver.execute_query(
                "MATCH (n) RETURN labels(n) as labels, count(n) as count",
                database_=self.config.neo4j_database
            )
            
            for record in result.records:
                labels = record["labels"]
                count = record["count"]
                stats["node_count"] += count
                if labels:
                    label = labels[0]
                    stats["node_types"][label] = count
            
            # Count relationships
            result = self.graph_store._driver.execute_query(
                "MATCH ()-[r]->() RETURN type(r) as type, count(r) as count",
                database_=self.config.neo4j_database
            )
            
            for record in result.records:
                rel_type = record["type"]
                count = record["count"]
                stats["relationship_count"] += count
                stats["relationship_types"][rel_type] = count
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
        
        return stats
    
    def clear_graph(self):
        """Clear all data from the graph"""
        logger.warning("Clearing all data from the graph")
        
        try:
            self.graph_store._driver.execute_query(
                "MATCH (n) DETACH DELETE n",
                database_=self.config.neo4j_database
            )
            logger.info("Graph cleared successfully")
        except Exception as e:
            logger.error(f"Error clearing graph: {e}")
            raise
    
    def create_indexes(self):
        """Create recommended indexes for performance"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.id)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Entity) ON (n.name)",
            "CREATE INDEX IF NOT EXISTS FOR (n:Document) ON (n.doc_id)",
            "CREATE FULLTEXT INDEX entity_text IF NOT EXISTS FOR (n:Entity) ON EACH [n.text, n.description]"
        ]
        
        for index_query in indexes:
            try:
                self.graph_store._driver.execute_query(
                    index_query,
                    database_=self.config.neo4j_database
                )
                logger.info(f"Created index: {index_query}")
            except Exception as e:
                logger.warning(f"Index creation warning: {e}")