# LlamaIndex Knowledge Graph Ingestion Pipeline

A comprehensive implementation of knowledge graph construction using LlamaIndex, LlamaParse, and Neo4j.

## Overview

This project implements an intelligent document ingestion pipeline that:
- Parses PDF documents using LlamaParse to extract structured markdown
- Processes markdown content to identify tables, text, and semantic relationships
- Extracts knowledge triplets using schema-driven LLM extraction
- Stores the knowledge graph in Neo4j for querying and analysis

## Features

- **Document Parsing**: Convert PDFs to structured markdown using LlamaParse
- **Content Segmentation**: Intelligently separate tables from text content
- **Schema-Driven Extraction**: Enforce consistent entity and relationship types
- **Neo4j Integration**: Direct storage and querying of knowledge graphs
- **Natural Language Queries**: Query the knowledge graph using natural language

## Architecture

```
PDF Document → LlamaParse → Markdown → MarkdownElementNodeParser → 
→ PropertyGraphIndex → Neo4j Knowledge Graph → Query Engine
```

## Requirements

- Python 3.8+
- Neo4j 4.0+
- OpenAI API key
- LlamaCloud API key

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Set the following environment variables:
- `LLAMA_CLOUD_API_KEY`: Your LlamaCloud API key
- `OPENAI_API_KEY`: Your OpenAI API key
- `NEO4J_URI`: Neo4j connection URI (default: bolt://localhost:7687)
- `NEO4J_USERNAME`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password

## Usage

```python
from src.pipeline import KnowledgeGraphPipeline

# Initialize the pipeline
pipeline = KnowledgeGraphPipeline()

# Process a document
knowledge_graph = pipeline.process_document("path/to/document.pdf")

# Query the knowledge graph
result = pipeline.query("What was the company's revenue in 2023?")
print(result)
```

## Project Structure

```
llamaindex-knowledge-graph/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── parser.py          # LlamaParse integration
│   ├── extractor.py       # Knowledge extraction logic
│   ├── graph_store.py     # Neo4j integration
│   └── pipeline.py        # Main pipeline orchestration
├── tests/
│   └── test_pipeline.py
├── examples/
│   └── basic_usage.py
├── docs/
│   └── architecture.md
├── data/
│   └── sample.pdf
├── requirements.txt
└── README.md
```