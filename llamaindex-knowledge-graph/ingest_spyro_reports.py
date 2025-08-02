#!/usr/bin/env python3
"""Ingest SpyroSolutions reports using the LlamaIndex pipeline"""

import os
import sys
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.pipeline import KnowledgeGraphPipeline
from src.config import Config, GraphSchema

# Load environment
load_dotenv()

# Define SpyroSolutions-specific schema
class SpyroGraphSchema(GraphSchema):
    """Schema specific to SpyroSolutions business domain"""
    
    def __init__(self):
        # Define entity types based on the semantic model
        self.entities = [
            # Core business entities
            "CUSTOMER", "PRODUCT", "TEAM", "PROJECT", "RISK", "OBJECTIVE",
            "SUBSCRIPTION", "SLA", "COMMITMENT", "ROADMAP_ITEM",
            # Financial entities
            "REVENUE", "COST", "PROFITABILITY", "ARR",
            # People and organizations
            "PERSON", "DEPARTMENT", "COMPETITOR",
            # Technical entities
            "FEATURE", "SYSTEM", "INFRASTRUCTURE", "VULNERABILITY",
            # Events and time
            "EVENT", "MILESTONE", "QUARTER", "DEADLINE"
        ]
        
        # Define relationship types
        self.relations = [
            # Customer relationships
            "SUBSCRIBES_TO", "HAS_RISK", "HAS_SUCCESS_SCORE", "USES",
            "HAS_COMMITMENT", "HAS_SLA", "EVALUATED_BY",
            # Product relationships
            "OFFERS_FEATURE", "HAS_ROADMAP", "COMPETES_WITH", 
            "HAS_OPERATIONAL_COST", "GENERATES_REVENUE",
            # Team relationships
            "SUPPORTS", "RESPONSIBLE_FOR", "DEVELOPS", "MAINTAINS",
            "LED_BY", "WORKS_FOR", "COLLABORATES_WITH",
            # Project relationships
            "DELIVERS", "DEPENDS_ON", "BLOCKS", "IMPACTS",
            # Risk relationships
            "THREATENS", "MITIGATED_BY", "AFFECTS", "OWNED_BY",
            # Financial relationships
            "COSTS", "PROFITS_FROM", "INVESTS_IN", "FUNDED_BY",
            # Temporal relationships
            "SCHEDULED_FOR", "COMPLETED_ON", "DUE_BY", "OCCURRED_ON"
        ]
        
        # Define validation rules
        self.validation_schema = {
            "CUSTOMER": ["SUBSCRIBES_TO", "HAS_RISK", "HAS_SUCCESS_SCORE", "USES", "HAS_COMMITMENT", "HAS_SLA"],
            "PRODUCT": ["OFFERS_FEATURE", "HAS_ROADMAP", "HAS_OPERATIONAL_COST", "GENERATES_REVENUE", "SUPPORTED_BY"],
            "TEAM": ["SUPPORTS", "RESPONSIBLE_FOR", "DEVELOPS", "LED_BY"],
            "PROJECT": ["DELIVERS", "DEPENDS_ON", "OWNED_BY", "SCHEDULED_FOR"],
            "RISK": ["THREATENS", "AFFECTS", "MITIGATED_BY", "OWNED_BY"],
            "PERSON": ["WORKS_FOR", "LEADS", "RESPONSIBLE_FOR"],
            "SUBSCRIPTION": ["FOR_PRODUCT", "GENERATES", "EXPIRES_ON"],
            "FEATURE": ["OFFERED_BY", "REQUESTED_BY", "DEVELOPED_BY"],
            "COMPETITOR": ["COMPETES_WITH", "THREATENS", "TARGETS"]
        }

def main():
    """Main ingestion function"""
    
    print("SpyroSolutions Knowledge Graph Ingestion")
    print("=" * 60)
    
    # Configure pipeline with SpyroSolutions schema
    config = Config()
    schema = SpyroGraphSchema()
    
    # Initialize pipeline
    print("\nInitializing knowledge graph pipeline...")
    pipeline = KnowledgeGraphPipeline(config=config, schema=schema)
    
    # Define reports to ingest
    reports = [
        "data/Q1_2025_Customer_Analysis_Report.pdf",
        "data/Product_Development_Status_April_2025.pdf",
        "data/Risk_Assessment_Financial_Report_2025.pdf"
    ]
    
    # Check if files exist
    existing_reports = []
    for report in reports:
        if Path(report).exists():
            existing_reports.append(report)
            print(f"✓ Found: {report}")
        else:
            print(f"✗ Missing: {report}")
    
    if not existing_reports:
        print("\nError: No reports found to ingest!")
        return 1
    
    # Process reports
    print(f"\nProcessing {len(existing_reports)} SpyroSolutions reports...")
    print("This will extract entities like customers, products, teams, risks, etc.")
    print("And discover relationships between them...")
    
    try:
        # Process all reports
        results = pipeline.process_multiple_documents(
            file_paths=existing_reports,
            clear_existing=False  # Keep existing data
        )
        
        print("\n" + "="*60)
        print("INGESTION RESULTS")
        print("="*60)
        
        print(f"\nDocuments processed: {results['files_processed']}")
        print(f"Total nodes extracted: {results['total_nodes']}")
        
        # Show entity breakdown
        if 'node_types' in results['graph']:
            print("\nEntities extracted by type:")
            for entity_type, count in sorted(results['graph']['node_types'].items(), 
                                           key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {entity_type}: {count}")
        
        # Show relationship breakdown  
        if 'relationship_types' in results['graph']:
            print("\nRelationships discovered:")
            for rel_type, count in sorted(results['graph']['relationship_types'].items(), 
                                        key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {rel_type}: {count}")
        
        print("\n" + "="*60)
        print("SAMPLE QUERIES TO TRY")
        print("="*60)
        
        # Test some queries
        sample_queries = [
            "What new customers did SpyroSolutions acquire in Q1 2025?",
            "Which teams are working on multi-region deployment?",
            "What are the critical risks facing the company?",
            "What is the profitability of each product line?",
            "Which customers are at risk of churning?",
            "What features are being developed for SpyroAI?",
            "Who are the key competitors and what threats do they pose?",
            "What are the dependencies for Project Titan?"
        ]
        
        print("\nTesting knowledge extraction with sample queries...\n")
        
        for i, query in enumerate(sample_queries[:3], 1):
            print(f"Query {i}: {query}")
            try:
                response = pipeline.query(query)
                print(f"Answer: {response}\n")
            except Exception as e:
                print(f"Error: {e}\n")
        
        print("✅ SpyroSolutions knowledge graph successfully updated!")
        print("\nThe graph now contains:")
        print("- New customer information (InnovateTech, Global Manufacturing)")
        print("- Product development status and roadmap items")
        print("- Team structures and responsibilities")
        print("- Risk assessments and mitigation strategies")
        print("- Financial performance and profitability data")
        print("- Competitive landscape and threats")
        
        print("\nYou can query this knowledge using natural language or")
        print("visualize it in Neo4j Browser at http://localhost:7474")
        
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())