This guide provides the necessary code patterns to construct the ingestion pipeline using Python and the LlamaIndex framework.

Step 1: Environment Setup

First, ensure all required libraries are installed and environment variables are configured. This includes the core LlamaIndex library, the LlamaParse client, and the Neo4j integration packages.1

Python


# Install necessary packages
!pip install llama-parse
!pip install llama-index
!pip install llama-index-llms-openai
!pip install llama-index-embeddings-openai
!pip install llama-index-graph-stores-neo4j
!pip install neo4j

import os
from getpass import getpass

# Set API Keys
# It is recommended to set these as environment variables
if "LLAMA_CLOUD_API_KEY" not in os.environ:
    os.environ = getpass("Enter LlamaCloud API Key: ")
if "OPENAI_API_KEY" not in os.environ:
    os.environ = getpass("Enter OpenAI API Key: ")

# Set Neo4j Credentials
NEO4J_URI = "bolt://localhost:7687" # Replace with your Neo4j instance URI
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = getpass("Enter Neo4j Password: ")
NEO4J_DATABASE = "neo4j"



Step 2: Parsing the Document with LlamaParse

The next step is to use LlamaParse to process the source PDF. The key is to set result_type="markdown" to obtain the structured output necessary for the subsequent stages.5

Python


from llama_parse import LlamaParse

# Instantiate the parser
# The 'markdown' result_type is crucial for preserving structure
parser = LlamaParse(result_type="markdown", verbose=True)

# Load the data from a local PDF file
# This sends the document to the LlamaCloud API for processing
documents = parser.load_data("./annual-report-2023.pdf")

# The output is a list of LlamaIndex Document objects,
# with the parsed markdown content in the.text attribute
print(documents.text[:2000])



Step 3: Processing Markdown with MarkdownElementNodeParser

With the Markdown content available, the MarkdownElementNodeParser is used to intelligently segment it into a list of semantic nodes. This parser understands Markdown syntax and will create distinct TableNode objects for tables and TextNode objects for other content like paragraphs and headers.5

Python


from llama_index.core.node_parser import MarkdownElementNodeParser
from llama_index.llms.openai import OpenAI
from llama_index.core import Settings

# Configure the LLM to be used by the node parser and extractors
llm = OpenAI(model="gpt-4o")
Settings.llm = llm

# Instantiate the node parser
node_parser = MarkdownElementNodeParser(llm=llm, num_workers=8)

# Parse the documents into nodes
# This process identifies text vs. tables and creates distinct node types
nodes = node_parser.get_nodes_from_documents(documents)

# Separate the base text nodes from table and other objects
base_nodes, objects = node_parser.get_nodes_and_objects(nodes)

print(f"Found {len(base_nodes)} text nodes and {len(objects)} objects (tables).")



Step 4: Extracting Triplets with PropertyGraphIndex

This is the core knowledge creation step. A PropertyGraphIndex is configured with a SchemaLLMPathExtractor to enforce a consistent graph structure and a Neo4jPropertyGraphStore to connect to the database. The index then processes the nodes generated in the previous step.1

Python


from typing import Literal
from llama_index.core import PropertyGraphIndex
from llama_index.core.indices.property_graph import SchemaLLMPathExtractor
from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

# Define the graph schema based on the domain (e.g., corporate reports)
entities = Literal
relations = Literal

# Define the validation schema to enforce relationship constraints
validation_schema = {
    "PERSON":,
    "COMPANY":,
    "PRODUCT":,
    "FINANCIAL_METRIC":,
}

# Instantiate the schema-driven extractor
kg_extractor = SchemaLLMPathExtractor(
    llm=llm,
    possible_entities=entities,
    possible_relations=relations,
    kg_validation_schema=validation_schema,
    strict=True, # Enforce the schema strictly
)

# Instantiate the Neo4j graph store
graph_store = Neo4jPropertyGraphStore(
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    url=NEO4J_URI,
    database=NEO4J_DATABASE,
)

# Construct the PropertyGraphIndex
# This will process the nodes, extract triplets, and load them into Neo4j
index = PropertyGraphIndex(
    nodes=base_nodes + objects, # Process both text and table nodes
    property_graph_store=graph_store,
    kg_extractors=[kg_extractor],
    show_progress=True,
)



Step 5: Persisting and Querying in Neo4j

Once the PropertyGraphIndex has been constructed, the knowledge graph is populated in Neo4j. The index can then be used to create a query engine that allows for natural language querying of the graph.3

Python


# Create a query engine from the index
query_engine = index.as_query_engine()

# Formulate a natural language query
response = query_engine.query("What was the company's revenue in 2023?")
print(str(response))

# Example of a more complex, multi-hop query
response = query_engine.query("List the products produced by companies that were acquired.")
print(str(response))


Works cited
Constructing a Knowledge Graph with LlamaIndex and Memgraph, accessed August 1, 2025, https://www.llamaindex.ai/blog/constructing-a-knowledge-graph-with-llamaindex-and-memgraph
LlamaParse - Llama Hub, accessed August 1, 2025, https://llamahub.ai/l/readers/llama-index-readers-llama-parse?from=
Neo4j Graph Store - LlamaIndex, accessed August 1, 2025, https://docs.llamaindex.ai/en/stable/examples/index_structs/knowledge_graph/Neo4jKGIndexDemo/
Neo4j Property Graph Index - LlamaIndex, accessed August 1, 2025, https://docs.llamaindex.ai/en/stable/examples/property_graph/property_graph_neo4j/
Creating Knowledge Graphs from Documents Using LlamaParse - Llama 2, accessed August 1, 2025, https://llama-2.ai/creating-knowledge-graphs-from-documents-using-llamaparse/
Document Parsing: Extracting Embedded Objects with LlamaParse, accessed August 1, 2025, https://www.analyticsvidhya.com/blog/2024/05/document-parsing-with-llamaparse/
LlamaIndex - Neo4j Labs, accessed August 1, 2025, https://neo4j.com/labs/genai-ecosystem/llamaindex/
Knowledge Graph Query Engine - LlamaIndex, accessed August 1, 2025, https://docs.llamaindex.ai/en/stable/examples/query_engine/knowledge_graph_query_engine/
