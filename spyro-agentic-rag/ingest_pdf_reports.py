#!/usr/bin/env python3
"""Ingest PDF reports using LlamaIndex pipeline"""

import os
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.storage.storage_context import StorageContext
from llama_index.core.graph_stores import SimpleGraphStore
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def ingest_pdfs():
    """Ingest PDF reports into LlamaIndex"""
    
    # Path to PDF directory
    pdf_dir = Path("data/pdfs")
    
    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_dir}")
        return
    
    # List all PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))
    logger.info(f"Found {len(pdf_files)} PDF files to ingest")
    
    # Initialize LlamaIndex reader
    try:
        logger.info("Loading PDF documents...")
        documents = SimpleDirectoryReader(
            input_dir=str(pdf_dir),
            filename_as_id=True,
            required_exts=[".pdf"]
        ).load_data()
        
        logger.info(f"Loaded {len(documents)} documents")
        
        # Parse documents into nodes
        logger.info("Parsing documents into nodes...")
        parser = SimpleNodeParser.from_defaults(
            chunk_size=1024,
            chunk_overlap=200
        )
        nodes = parser.get_nodes_from_documents(documents)
        logger.info(f"Created {len(nodes)} nodes")
        
        # Create index
        logger.info("Creating vector index...")
        index = VectorStoreIndex(nodes)
        
        # Persist index
        logger.info("Persisting index...")
        index.storage_context.persist(persist_dir="storage")
        
        logger.info("PDF ingestion completed successfully!")
        
        # Print summary
        print("\n" + "="*60)
        print("INGESTION SUMMARY")
        print("="*60)
        print(f"Documents ingested: {len(documents)}")
        print(f"Nodes created: {len(nodes)}")
        print("\nIngested files:")
        for pdf_file in pdf_files:
            print(f"  - {pdf_file.name}")
        print("\nNext steps:")
        print("1. Re-run the business questions test")
        print("2. Verify that the data gaps have been filled")
        print("="*60)
        
    except Exception as e:
        logger.error(f"Error during ingestion: {e}")
        raise

def main():
    """Main function"""
    logger.info("Starting PDF report ingestion...")
    
    try:
        ingest_pdfs()
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())