#!/usr/bin/env python3
"""Basic usage example for the knowledge graph pipeline"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline import KnowledgeGraphPipeline
from src.config import Config, GraphSchema
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def main():
    """Demonstrate basic usage of the knowledge graph pipeline"""
    
    # Create configuration
    config = Config()
    
    # Optionally customize the schema for your domain
    schema = GraphSchema(
        entities=[
            "PERSON", "COMPANY", "PRODUCT", "DEPARTMENT",
            "FINANCIAL_METRIC", "PROJECT", "TECHNOLOGY"
        ],
        relations=[
            "WORKS_FOR", "MANAGES", "PRODUCES", "USES",
            "PARTNERS_WITH", "INVESTS_IN", "REPORTS_TO"
        ]
    )
    
    try:
        # Initialize pipeline
        logger.info("Initializing knowledge graph pipeline...")
        pipeline = KnowledgeGraphPipeline(config=config, schema=schema)
        
        # Example 1: Process a single document
        logger.info("\n" + "="*60)
        logger.info("Example 1: Processing a single document")
        logger.info("="*60)
        
        # Replace with your actual PDF path
        pdf_path = Path("../data/sample.pdf")
        
        if pdf_path.exists():
            results = pipeline.process_document(
                file_path=pdf_path,
                clear_existing=True  # Clear any existing data
            )
            
            # Display results
            logger.info("\nProcessing Results:")
            logger.info(f"Documents parsed: {results['parsing']['documents_parsed']}")
            logger.info(f"Text nodes: {results['extraction']['text_nodes']}")
            logger.info(f"Table nodes: {results['extraction']['table_nodes']}")
            logger.info(f"Total nodes in graph: {results['graph']['node_count']}")
            logger.info(f"Total relationships: {results['graph']['relationship_count']}")
            
            # Show node type distribution
            logger.info("\nNode Types:")
            for node_type, count in results['graph']['node_types'].items():
                logger.info(f"  {node_type}: {count}")
            
            # Show relationship type distribution
            logger.info("\nRelationship Types:")
            for rel_type, count in results['graph']['relationship_types'].items():
                logger.info(f"  {rel_type}: {count}")
        else:
            logger.warning(f"Sample PDF not found at {pdf_path}")
            logger.info("Please place a PDF file in the data directory")
        
        # Example 2: Query the knowledge graph
        logger.info("\n" + "="*60)
        logger.info("Example 2: Querying the knowledge graph")
        logger.info("="*60)
        
        sample_queries = [
            "What companies are mentioned in the document?",
            "Who are the key people and their roles?",
            "What products or services are described?",
            "What are the main financial metrics?"
        ]
        
        for query in sample_queries[:2]:  # Run first 2 queries
            logger.info(f"\nQuery: {query}")
            try:
                response = pipeline.query(query)
                logger.info(f"Response: {response}")
            except Exception as e:
                logger.error(f"Query failed: {e}")
        
        # Example 3: Process multiple documents
        logger.info("\n" + "="*60)
        logger.info("Example 3: Processing multiple documents")
        logger.info("="*60)
        
        # List of PDF paths
        pdf_paths = [
            Path("../data/report1.pdf"),
            Path("../data/report2.pdf"),
            Path("../data/report3.pdf")
        ]
        
        # Filter existing files
        existing_pdfs = [p for p in pdf_paths if p.exists()]
        
        if existing_pdfs:
            results = pipeline.process_multiple_documents(
                file_paths=existing_pdfs,
                clear_existing=True
            )
            
            logger.info(f"\nProcessed {results['files_processed']} files")
            logger.info(f"Total nodes created: {results['total_nodes']}")
            logger.info(f"Final graph size: {results['graph']['node_count']} nodes, "
                       f"{results['graph']['relationship_count']} relationships")
        else:
            logger.info("No additional PDF files found for batch processing")
        
        # Example 4: Get graph statistics
        logger.info("\n" + "="*60)
        logger.info("Example 4: Graph Statistics")
        logger.info("="*60)
        
        stats = pipeline.graph.get_statistics()
        logger.info(f"Total nodes: {stats['node_count']}")
        logger.info(f"Total relationships: {stats['relationship_count']}")
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())