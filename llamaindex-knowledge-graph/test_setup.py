#!/usr/bin/env python3
"""Test setup script to verify all components are working"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_setup():
    """Check if all required components are configured"""
    
    print("LlamaIndex Knowledge Graph - Setup Checker")
    print("=" * 50)
    
    issues = []
    
    # Check API keys
    print("\n1. Checking API Keys:")
    
    llama_key = os.getenv("LLAMA_CLOUD_API_KEY", "")
    if llama_key:
        print("   ✓ LLAMA_CLOUD_API_KEY is set")
    else:
        print("   ✗ LLAMA_CLOUD_API_KEY is missing")
        issues.append("LLAMA_CLOUD_API_KEY")
    
    openai_key = os.getenv("OPENAI_API_KEY", "")
    if openai_key:
        print("   ✓ OPENAI_API_KEY is set")
    else:
        print("   ✗ OPENAI_API_KEY is missing")
        issues.append("OPENAI_API_KEY")
    
    # Check Neo4j configuration
    print("\n2. Checking Neo4j Configuration:")
    
    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user = os.getenv("NEO4J_USERNAME", "neo4j")
    neo4j_pass = os.getenv("NEO4J_PASSWORD", "")
    
    print(f"   Neo4j URI: {neo4j_uri}")
    print(f"   Neo4j Username: {neo4j_user}")
    
    if neo4j_pass:
        print("   ✓ NEO4J_PASSWORD is set")
    else:
        print("   ✗ NEO4J_PASSWORD is missing")
        issues.append("NEO4J_PASSWORD")
    
    # Test Neo4j connection
    print("\n3. Testing Neo4j Connection:")
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_pass))
        with driver.session() as session:
            result = session.run("RETURN 1 as test")
            record = result.single()
            if record["test"] == 1:
                print("   ✓ Successfully connected to Neo4j")
            else:
                print("   ✗ Neo4j connection test failed")
                issues.append("Neo4j connection")
        driver.close()
    except Exception as e:
        print(f"   ✗ Failed to connect to Neo4j: {e}")
        issues.append("Neo4j connection")
    
    # Check for test data
    print("\n4. Checking Test Data:")
    data_dir = Path("data")
    if data_dir.exists():
        pdf_files = list(data_dir.glob("*.pdf"))
        if pdf_files:
            print(f"   ✓ Found {len(pdf_files)} PDF files in data/")
            for pdf in pdf_files[:3]:
                print(f"     - {pdf.name}")
        else:
            print("   ⚠ No PDF files found in data/")
            print("   Suggestion: Add some PDF files to test with")
    else:
        print("   ⚠ data/ directory not found")
        data_dir.mkdir(exist_ok=True)
        print("   Created data/ directory - add PDF files here")
    
    # Summary
    print("\n" + "=" * 50)
    if issues:
        print("Setup Issues Found:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nPlease fix these issues before running the pipeline.")
        return False
    else:
        print("✓ All checks passed! Ready to run the pipeline.")
        return True


def test_minimal_pipeline():
    """Run a minimal test of the pipeline"""
    
    print("\n\nRunning Minimal Pipeline Test...")
    print("=" * 50)
    
    try:
        # Add parent directory to path
        sys.path.append(str(Path(__file__).parent))
        
        from src.config import Config
        from src.pipeline import KnowledgeGraphPipeline
        
        # Test configuration
        print("1. Testing configuration...")
        config = Config()
        try:
            config.validate()
            print("   ✓ Configuration is valid")
        except Exception as e:
            print(f"   ✗ Configuration error: {e}")
            return False
        
        # Test pipeline initialization
        print("\n2. Initializing pipeline...")
        try:
            pipeline = KnowledgeGraphPipeline(config=config)
            print("   ✓ Pipeline initialized successfully")
        except Exception as e:
            print(f"   ✗ Pipeline initialization failed: {e}")
            return False
        
        # Test sample queries (without documents)
        print("\n3. Testing query engine...")
        try:
            # This will fail if no data is loaded, but tests the engine setup
            sample_queries = pipeline.get_sample_queries()
            print(f"   ✓ Generated {len(sample_queries)} sample queries")
        except Exception as e:
            print(f"   ⚠ Query test warning: {e}")
        
        print("\n✓ Minimal pipeline test completed!")
        return True
        
    except Exception as e:
        print(f"\n✗ Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # Check setup
    setup_ok = check_setup()
    
    if setup_ok:
        # Run minimal test
        test_minimal_pipeline()
    else:
        print("\nTo get started:")
        print("1. Copy .env.example to .env")
        print("2. Add your API keys to .env")
        print("3. Install and start Neo4j")
        print("4. Add PDF files to data/ directory")
        print("5. Run this script again")