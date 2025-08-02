"""Main pipeline for knowledge graph construction"""

import os
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import logging

from .config import Config, GraphSchema
from .parser import DocumentParser
from .extractor import KnowledgeExtractor
from .graph_store import Neo4jKnowledgeGraph

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KnowledgeGraphPipeline:
    """End-to-end pipeline for constructing knowledge graphs from documents"""
    
    def __init__(self, config: Optional[Config] = None, schema: Optional[GraphSchema] = None):
        """
        Initialize the knowledge graph pipeline
        
        Args:
            config: Configuration object (creates default if not provided)
            schema: Graph schema definition (creates default if not provided)
        """
        self.config = config or Config()
        self.config.validate()
        
        self.schema = schema or GraphSchema()
        
        # Set OpenAI API key
        os.environ["OPENAI_API_KEY"] = self.config.openai_api_key
        
        # Initialize components
        self.parser = DocumentParser(
            api_key=self.config.llama_cloud_api_key,
            result_type=self.config.parser_result_type,
            verbose=self.config.parser_verbose
        )
        
        self.extractor = KnowledgeExtractor(
            llm_model=self.config.llm_model,
            temperature=self.config.llm_temperature,
            num_workers=self.config.parser_num_workers,
            schema=self.schema
        )
        
        self.graph = Neo4jKnowledgeGraph(
            config=self.config,
            schema=self.schema
        )
        
        logger.info("Knowledge graph pipeline initialized")
    
    def process_document(self, file_path: Union[str, Path], 
                        clear_existing: bool = False) -> Dict[str, Any]:
        """
        Process a single document through the entire pipeline
        
        Args:
            file_path: Path to the document
            clear_existing: Clear existing graph data before processing
            
        Returns:
            Processing results and statistics
        """
        file_path = Path(file_path)
        logger.info(f"Processing document: {file_path}")
        
        # Clear existing data if requested
        if clear_existing:
            self.graph.clear_graph()
        
        # Step 1: Parse document
        logger.info("Step 1: Parsing document with LlamaParse")
        documents = self.parser.parse_document(str(file_path))
        
        # Step 2: Extract nodes
        logger.info("Step 2: Extracting nodes from markdown")
        base_nodes, table_nodes = self.extractor.parse_nodes(documents)
        all_nodes = base_nodes + table_nodes
        
        # Step 3: Build knowledge graph
        logger.info("Step 3: Building knowledge graph in Neo4j")
        index = self.graph.build_graph(all_nodes, show_progress=self.config.extraction_show_progress)
        
        # Step 4: Create indexes for performance
        logger.info("Step 4: Creating database indexes")
        self.graph.create_indexes()
        
        # Get statistics
        stats = self.graph.get_statistics()
        
        # Prepare results
        results = {
            "status": "success",
            "file": str(file_path),
            "parsing": {
                "documents_parsed": len(documents),
                "total_characters": sum(len(doc.text) for doc in documents)
            },
            "extraction": {
                "text_nodes": len(base_nodes),
                "table_nodes": len(table_nodes),
                "total_nodes": len(all_nodes)
            },
            "graph": stats
        }
        
        logger.info(f"Processing complete. Created {stats['node_count']} nodes and {stats['relationship_count']} relationships")
        
        return results
    
    def process_multiple_documents(self, file_paths: List[Union[str, Path]], 
                                 clear_existing: bool = True) -> Dict[str, Any]:
        """
        Process multiple documents
        
        Args:
            file_paths: List of document paths
            clear_existing: Clear existing graph data before processing
            
        Returns:
            Combined processing results
        """
        logger.info(f"Processing {len(file_paths)} documents")
        
        # Clear existing data if requested
        if clear_existing:
            self.graph.clear_graph()
        
        all_results = []
        all_nodes = []
        
        # Parse all documents
        for file_path in file_paths:
            try:
                documents = self.parser.parse_document(str(file_path))
                base_nodes, table_nodes = self.extractor.parse_nodes(documents)
                all_nodes.extend(base_nodes + table_nodes)
                
                all_results.append({
                    "file": str(file_path),
                    "status": "parsed",
                    "nodes": len(base_nodes) + len(table_nodes)
                })
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                all_results.append({
                    "file": str(file_path),
                    "status": "error",
                    "error": str(e)
                })
        
        # Build graph from all nodes
        if all_nodes:
            logger.info(f"Building graph from {len(all_nodes)} total nodes")
            self.graph.build_graph(all_nodes, show_progress=self.config.extraction_show_progress)
            self.graph.create_indexes()
        
        # Get final statistics
        stats = self.graph.get_statistics()
        
        return {
            "status": "complete",
            "files_processed": len(file_paths),
            "individual_results": all_results,
            "total_nodes": len(all_nodes),
            "graph": stats
        }
    
    def query(self, query_text: str) -> str:
        """
        Query the knowledge graph
        
        Args:
            query_text: Natural language query
            
        Returns:
            Query response
        """
        return self.graph.query(query_text)
    
    def get_sample_queries(self) -> List[str]:
        """
        Get sample queries based on the schema
        
        Returns:
            List of sample query strings
        """
        return [
            "What companies are mentioned in the documents?",
            "Who are the key people and what companies do they work for?",
            "What products are produced by each company?",
            "What are the main financial metrics?",
            "What partnerships exist between companies?",
            "What technologies are being used?",
            "What are the identified risks?",
            "Show me the organizational structure",
            "What events occurred and when?",
            "What are the relationships between different entities?"
        ]