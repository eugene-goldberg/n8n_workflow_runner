#!/usr/bin/env python3
"""Simple example following the implementation guide exactly"""

import os
from typing import Literal
from llama_parse import LlamaParse
from llama_index.core.node_parser import MarkdownElementNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings, PropertyGraphIndex
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
LLAMA_CLOUD_API_KEY = os.getenv("LLAMA_CLOUD_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")

# Set API keys
os.environ["LLAMA_CLOUD_API_KEY"] = LLAMA_CLOUD_API_KEY
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

print("Simple LlamaIndex Knowledge Graph Example")
print("=" * 50)

# Step 1: Check if we have a PDF to process
pdf_path = "data/sample.pdf"
if not os.path.exists(pdf_path):
    print(f"\nError: No PDF found at {pdf_path}")
    print("Please add a PDF file to the data/ directory")
    print("\nYou can download sample PDFs from:")
    print("- SEC EDGAR: https://www.sec.gov/edgar")
    print("- arXiv: https://arxiv.org/")
    print("- Company annual reports")
    exit(1)

print(f"\nStep 1: Parsing PDF: {pdf_path}")

# Step 2: Parse with LlamaParse
parser = LlamaParse(result_type="markdown", verbose=True)
documents = parser.load_data(pdf_path)
print(f"✓ Parsed {len(documents)} document(s)")

# Step 3: Configure LLM
llm = OpenAI(model="gpt-4o")
Settings.llm = llm

# Step 4: Parse markdown into nodes
print("\nStep 2: Extracting nodes from markdown")
node_parser = MarkdownElementNodeParser(llm=llm, num_workers=8)
nodes = node_parser.get_nodes_from_documents(documents)
base_nodes, objects = node_parser.get_nodes_and_objects(nodes)
print(f"✓ Found {len(base_nodes)} text nodes and {len(objects)} table nodes")

# Step 5: Define schema (following the guide exactly)
print("\nStep 3: Setting up knowledge extraction schema")

# Define entity and relation types as Literals
entities = Literal["PERSON", "COMPANY", "PRODUCT", "FINANCIAL_METRIC"]
relations = Literal["WORKS_FOR", "PRODUCES", "REPORTS", "INVESTS_IN"]

# Define validation schema
validation_schema = {
    "PERSON": ["WORKS_FOR"],
    "COMPANY": ["PRODUCES", "INVESTS_IN"],
    "PRODUCT": ["PRODUCED_BY"],
    "FINANCIAL_METRIC": ["REPORTS"],
}

# Create schema extractor
kg_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=entities,
    possible_relations=relations,
    kg_validation_schema=validation_schema,
    strict=True
)

# Step 6: Connect to Neo4j
print("\nStep 4: Connecting to Neo4j")
graph_store = Neo4jPropertyGraphStore(
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    url=NEO4J_URI,
    database=NEO4J_DATABASE
)
print("✓ Connected to Neo4j")

# Step 7: Build the knowledge graph
print("\nStep 5: Building knowledge graph")
print("This may take a few minutes...")

index = PropertyGraphIndex(
    nodes=base_nodes + objects,
    property_graph_store=graph_store,
    kg_extractors=[kg_extractor],
    show_progress=True
)
print("✓ Knowledge graph built successfully")

# Step 8: Create query engine and test
print("\nStep 6: Testing queries")
query_engine = index.as_query_engine()

# Sample queries
sample_queries = [
    "What companies are mentioned in the document?",
    "Who are the key people and their roles?",
    "What products are mentioned?",
    "What are the financial metrics?"
]

for i, query in enumerate(sample_queries[:2], 1):
    print(f"\nQuery {i}: {query}")
    try:
        response = query_engine.query(query)
        print(f"Response: {response}")
    except Exception as e:
        print(f"Error: {e}")

print("\n✓ Example completed successfully!")
print("\nYou can now:")
print("1. Run more queries against the knowledge graph")
print("2. Visualize the graph in Neo4j Browser")
print("3. Process additional documents")