"""Knowledge extraction using MarkdownElementNodeParser and SchemaLLMPathExtractor"""

from typing import List, Tuple, Dict, Any
from llama_index.core.node_parser import MarkdownElementNodeParser
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.core.schema import Document, BaseNode, TextNode, IndexNode
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings
import logging

from .config import GraphSchema

logger = logging.getLogger(__name__)


class KnowledgeExtractor:
    """Extract knowledge from documents using LlamaIndex components"""
    
    def __init__(self, llm_model: str = "gpt-4o", temperature: float = 0.0, 
                 num_workers: int = 8, schema: GraphSchema = None):
        """
        Initialize the knowledge extractor
        
        Args:
            llm_model: OpenAI model to use
            temperature: LLM temperature setting
            num_workers: Number of parallel workers
            schema: Graph schema definition
        """
        # Configure LLM
        self.llm = OpenAI(model=llm_model, temperature=temperature)
        Settings.llm = self.llm
        
        # Initialize node parser
        self.node_parser = MarkdownElementNodeParser(
            llm=self.llm,
            num_workers=num_workers
        )
        
        # Initialize schema
        self.schema = schema or GraphSchema()
        
        # Initialize schema extractor
        # Convert lists to type literals for pydantic compatibility
        from typing import Literal, get_args
        
        # Create literal types from entity and relation lists
        entity_literal = Literal[tuple(self.schema.entities)]
        relation_literal = Literal[tuple(self.schema.relations)]
        
        self.kg_extractor = SchemaLLMPathExtractor(
            llm=self.llm,
            possible_entities=entity_literal,
            possible_relations=relation_literal,
            kg_validation_schema=self.schema.validation_schema,
            strict=True
        )
    
    def parse_nodes(self, documents: List[Document]) -> Tuple[List[BaseNode], List[BaseNode]]:
        """
        Parse documents into nodes, separating text and table nodes
        
        Args:
            documents: List of Document objects
            
        Returns:
            Tuple of (base_nodes, objects) where objects are tables
        """
        logger.info(f"Parsing {len(documents)} documents into nodes")
        
        # Parse documents into nodes
        nodes = self.node_parser.get_nodes_from_documents(documents)
        
        # Separate base nodes from objects (tables)
        base_nodes, objects = self.node_parser.get_nodes_and_objects(nodes)
        
        logger.info(f"Found {len(base_nodes)} text nodes and {len(objects)} table nodes")
        
        return base_nodes, objects
    
    def extract_entities_relations(self, nodes: List[BaseNode]) -> Dict[str, Any]:
        """
        Extract entities and relations from nodes
        
        Args:
            nodes: List of nodes to process
            
        Returns:
            Dictionary containing extracted entities and relations
        """
        logger.info(f"Extracting entities and relations from {len(nodes)} nodes")
        
        # Extract using the schema extractor
        # This is typically done through PropertyGraphIndex
        # For standalone extraction, we need to process each node
        
        extracted_data = {
            "entities": [],
            "relations": [],
            "metadata": {}
        }
        
        for node in nodes:
            try:
                # The actual extraction happens within PropertyGraphIndex
                # This is a placeholder for the extraction logic
                logger.debug(f"Processing node: {node.node_id}")
                
            except Exception as e:
                logger.error(f"Error processing node {node.node_id}: {e}")
                continue
        
        return extracted_data
    
    def analyze_content_types(self, base_nodes: List[BaseNode], 
                            objects: List[BaseNode]) -> Dict[str, Any]:
        """
        Analyze the types of content found in the document
        
        Args:
            base_nodes: Text nodes
            objects: Table/object nodes
            
        Returns:
            Analysis results
        """
        analysis = {
            "total_nodes": len(base_nodes) + len(objects),
            "text_nodes": len(base_nodes),
            "table_nodes": len(objects),
            "content_distribution": {},
            "sample_content": {}
        }
        
        # Analyze text nodes
        if base_nodes:
            text_lengths = [len(node.get_content()) for node in base_nodes]
            analysis["content_distribution"]["text"] = {
                "count": len(base_nodes),
                "avg_length": sum(text_lengths) / len(text_lengths),
                "min_length": min(text_lengths),
                "max_length": max(text_lengths)
            }
            analysis["sample_content"]["text"] = base_nodes[0].get_content()[:200]
        
        # Analyze table nodes
        if objects:
            analysis["content_distribution"]["tables"] = {
                "count": len(objects)
            }
            analysis["sample_content"]["table"] = str(objects[0])[:200]
        
        return analysis