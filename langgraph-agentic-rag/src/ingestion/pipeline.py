"""Main ingestion pipeline for building the knowledge graph."""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path

from neo4j import GraphDatabase
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import PGVector

from config.settings import settings
from .extractors import EntityRelationExtractor

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """Pipeline for ingesting documents into the knowledge graph."""
    
    def __init__(self):
        """Initialize the ingestion pipeline."""
        # Neo4j driver
        self.neo4j_driver = GraphDatabase.driver(
            settings.neo4j.uri,
            auth=(settings.neo4j.username, settings.neo4j.password)
        )
        
        # Embeddings
        self.embeddings = OpenAIEmbeddings(
            api_key=settings.openai.api_key
        )
        
        # PGVector store
        self.vector_store = PGVector(
            connection_string=settings.postgres.pgvector_connection_string,
            embedding_function=self.embeddings,
            collection_name="documents",
            distance_strategy="cosine"
        )
        
        # Entity extractor
        self.extractor = EntityRelationExtractor()
        
        # Text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        
        logger.info("Ingestion pipeline initialized")
    
    async def ingest_file(self, file_path: str) -> Dict[str, Any]:
        """Ingest a single file into the knowledge graph.
        
        Args:
            file_path: Path to the file to ingest
            
        Returns:
            Summary of ingestion results
        """
        path = Path(file_path)
        
        # Load document
        if path.suffix.lower() == ".pdf":
            loader = PyPDFLoader(file_path)
        else:
            loader = TextLoader(file_path)
        
        documents = loader.load()
        logger.info(f"Loaded {len(documents)} documents from {file_path}")
        
        # Split into chunks
        chunks = self.text_splitter.split_documents(documents)
        logger.info(f"Split into {len(chunks)} chunks")
        
        # Store in vector database
        chunk_ids = self.vector_store.add_documents(chunks)
        logger.info(f"Added {len(chunk_ids)} chunks to vector store")
        
        # Extract entities and relationships
        all_entities = []
        all_relationships = []
        
        for chunk in chunks:
            extraction = await self.extractor.extract(chunk.page_content)
            all_entities.extend(extraction["entities"])
            all_relationships.extend(extraction["relationships"])
        
        # Deduplicate entities
        unique_entities = self.extractor.deduplicate_entities(all_entities)
        
        # Store in Neo4j
        await self._store_in_neo4j(
            document_path=file_path,
            chunks=chunks,
            entities=unique_entities,
            relationships=all_relationships
        )
        
        return {
            "file": file_path,
            "chunks": len(chunks),
            "entities": len(unique_entities),
            "relationships": len(all_relationships)
        }
    
    async def _store_in_neo4j(
        self,
        document_path: str,
        chunks: List[Any],
        entities: List[Dict[str, Any]],
        relationships: List[Dict[str, Any]]
    ) -> None:
        """Store extracted data in Neo4j.
        
        Args:
            document_path: Path to the source document
            chunks: Document chunks
            entities: Extracted entities
            relationships: Extracted relationships
        """
        with self.neo4j_driver.session() as session:
            # Create document node
            doc_result = session.run(
                """
                MERGE (d:Document {path: $path})
                SET d.title = $title
                RETURN id(d) as doc_id
                """,
                path=document_path,
                title=Path(document_path).name
            )
            doc_id = doc_result.single()["doc_id"]
            
            # Create chunk nodes and link to document
            for i, chunk in enumerate(chunks):
                chunk_text = chunk.page_content
                chunk_embedding = self.embeddings.embed_query(chunk_text)
                
                session.run(
                    """
                    CREATE (c:Chunk {
                        content: $content,
                        index: $index,
                        embedding: $embedding
                    })
                    WITH c
                    MATCH (d:Document) WHERE id(d) = $doc_id
                    CREATE (d)-[:HAS_CHUNK]->(c)
                    """,
                    content=chunk_text,
                    index=i,
                    embedding=chunk_embedding,
                    doc_id=doc_id
                )
            
            # Create entities with __Entity__ label
            entity_mapping = {}
            for entity in entities:
                result = session.run(
                    """
                    MERGE (e:__Entity__ {name: $name})
                    SET e:$label
                    SET e += $properties
                    RETURN id(e) as entity_id
                    """,
                    name=entity["name"],
                    label=entity["type"],
                    properties=entity.get("properties", {})
                )
                entity_mapping[entity["name"]] = result.single()["entity_id"]
            
            # Create relationships
            for rel in relationships:
                if rel["source"] in entity_mapping and rel["target"] in entity_mapping:
                    session.run(
                        """
                        MATCH (s:__Entity__) WHERE id(s) = $source_id
                        MATCH (t:__Entity__) WHERE id(t) = $target_id
                        CREATE (s)-[r:$type]->(t)
                        SET r += $properties
                        """,
                        source_id=entity_mapping[rel["source"]],
                        target_id=entity_mapping[rel["target"]],
                        type=rel["relation"],
                        properties=rel.get("properties", {})
                    )
            
            # Create indexes for better performance
            session.run("CREATE INDEX IF NOT EXISTS FOR (n:__Entity__) ON (n.name)")
            session.run("CREATE INDEX IF NOT EXISTS FOR (d:Document) ON (d.path)")
            session.run("CREATE VECTOR INDEX document_embeddings IF NOT EXISTS FOR (c:Chunk) ON c.embedding")
            session.run("CREATE FULLTEXT INDEX document_fulltext IF NOT EXISTS FOR (c:Chunk) ON EACH [c.content]")
            
            logger.info(f"Stored document with {len(entities)} entities and {len(relationships)} relationships in Neo4j")
    
    async def ingest_directory(self, directory_path: str) -> List[Dict[str, Any]]:
        """Ingest all files in a directory.
        
        Args:
            directory_path: Path to directory containing files
            
        Returns:
            List of ingestion summaries
        """
        path = Path(directory_path)
        if not path.is_dir():
            raise ValueError(f"{directory_path} is not a directory")
        
        # Find all PDF and text files
        files = list(path.glob("**/*.pdf")) + list(path.glob("**/*.txt"))
        logger.info(f"Found {len(files)} files to ingest")
        
        results = []
        for file in files:
            try:
                result = await self.ingest_file(str(file))
                results.append(result)
            except Exception as e:
                logger.error(f"Error ingesting {file}: {e}")
                results.append({
                    "file": str(file),
                    "error": str(e)
                })
        
        return results
    
    def close(self):
        """Close database connections."""
        self.neo4j_driver.close()


# CLI entry point
async def main():
    """Main entry point for the ingestion pipeline."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ingest documents into knowledge graph")
    parser.add_argument("path", help="File or directory path to ingest")
    args = parser.parse_args()
    
    pipeline = IngestionPipeline()
    
    try:
        path = Path(args.path)
        if path.is_file():
            result = await pipeline.ingest_file(args.path)
            print(f"Ingested: {result}")
        elif path.is_dir():
            results = await pipeline.ingest_directory(args.path)
            for result in results:
                print(f"Ingested: {result}")
        else:
            print(f"Path not found: {args.path}")
    finally:
        pipeline.close()


if __name__ == "__main__":
    asyncio.run(main())