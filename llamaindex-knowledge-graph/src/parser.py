"""Document parsing using LlamaParse"""

import os
from typing import List, Optional
from llama_parse import LlamaParse
from llama_index.core.schema import Document
import logging

logger = logging.getLogger(__name__)


class DocumentParser:
    """Handle document parsing with LlamaParse"""
    
    def __init__(self, api_key: str, result_type: str = "markdown", verbose: bool = True):
        """
        Initialize the document parser
        
        Args:
            api_key: LlamaCloud API key
            result_type: Output format (markdown recommended)
            verbose: Enable verbose logging
        """
        self.api_key = api_key
        self.result_type = result_type
        self.verbose = verbose
        
        # Set API key in environment
        os.environ["LLAMA_CLOUD_API_KEY"] = api_key
        
        # Initialize parser
        self.parser = LlamaParse(
            result_type=result_type,
            verbose=verbose
        )
    
    def parse_document(self, file_path: str) -> List[Document]:
        """
        Parse a document file into structured content
        
        Args:
            file_path: Path to the document file
            
        Returns:
            List of Document objects with parsed content
        """
        logger.info(f"Parsing document: {file_path}")
        
        try:
            # Load and parse the document
            documents = self.parser.load_data(file_path)
            
            logger.info(f"Successfully parsed {len(documents)} document(s)")
            
            # Log sample of parsed content
            if documents and self.verbose:
                sample_text = documents[0].text[:500]
                logger.debug(f"Sample parsed content: {sample_text}...")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error parsing document: {e}")
            raise
    
    def parse_multiple_documents(self, file_paths: List[str]) -> List[Document]:
        """
        Parse multiple documents
        
        Args:
            file_paths: List of paths to document files
            
        Returns:
            Combined list of Document objects
        """
        all_documents = []
        
        for file_path in file_paths:
            try:
                documents = self.parse_document(file_path)
                all_documents.extend(documents)
            except Exception as e:
                logger.error(f"Failed to parse {file_path}: {e}")
                continue
        
        return all_documents
    
    def extract_metadata(self, documents: List[Document]) -> dict:
        """
        Extract metadata from parsed documents
        
        Args:
            documents: List of Document objects
            
        Returns:
            Dictionary of extracted metadata
        """
        metadata = {
            "total_documents": len(documents),
            "total_characters": sum(len(doc.text) for doc in documents),
            "document_ids": [doc.doc_id for doc in documents]
        }
        
        return metadata