#!/usr/bin/env python3
"""Ingest a single PDF report into LlamaIndex knowledge graph"""

import os
import sys
from pathlib import Path
import shutil
import time
from typing import Optional

# Add src to path
sys.path.append(str(Path(__file__).parent))

from src.pipeline import KnowledgeGraphPipeline
from src.config import Config, GraphSchema

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
            "REVENUE", "COST", "PROFITABILITY", "ARR", "OPERATIONAL_COST",
            # People and organizations
            "PERSON", "DEPARTMENT", "COMPETITOR", "REGION",
            # Technical entities
            "FEATURE", "SYSTEM", "INFRASTRUCTURE", "VULNERABILITY", "ISSUE",
            # Events and time
            "EVENT", "MILESTONE", "QUARTER", "DEADLINE",
            # Additional entities for new reports
            "PRICING_TIER", "COST_DRIVER", "SATISFACTION_SCORE", "ADOPTION_METRIC"
        ]
        
        # Define relationship types
        self.relations = [
            # Customer relationships
            "SUBSCRIBES_TO", "HAS_RISK", "HAS_SUCCESS_SCORE", "USES",
            "HAS_COMMITMENT", "HAS_SLA", "EVALUATED_BY", "LOCATED_IN",
            # Product relationships
            "OFFERS_FEATURE", "HAS_ROADMAP", "COMPETES_WITH", 
            "HAS_OPERATIONAL_COST", "GENERATES_REVENUE", "HAS_ADOPTION_RATE",
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
            "SCHEDULED_FOR", "COMPLETED_ON", "DUE_BY", "OCCURRED_ON",
            # Additional relationships for new reports
            "HAS_PRICING", "INCURS_COST", "TRACKS_METRIC", "PROMISES_FEATURE"
        ]
        
        # Define validation rules
        self.validation_schema = {
            "CUSTOMER": ["SUBSCRIBES_TO", "HAS_RISK", "HAS_SUCCESS_SCORE", "USES", "HAS_COMMITMENT", "HAS_SLA", "LOCATED_IN"],
            "PRODUCT": ["OFFERS_FEATURE", "HAS_ROADMAP", "HAS_OPERATIONAL_COST", "GENERATES_REVENUE", "SUPPORTED_BY", "HAS_ADOPTION_RATE"],
            "TEAM": ["SUPPORTS", "RESPONSIBLE_FOR", "DEVELOPS", "LED_BY"],
            "PROJECT": ["DELIVERS", "DEPENDS_ON", "OWNED_BY", "SCHEDULED_FOR"],
            "RISK": ["THREATENS", "AFFECTS", "MITIGATED_BY", "OWNED_BY"],
            "PERSON": ["WORKS_FOR", "LEADS", "RESPONSIBLE_FOR"],
            "SUBSCRIPTION": ["FOR_PRODUCT", "GENERATES", "EXPIRES_ON"],
            "FEATURE": ["OFFERED_BY", "REQUESTED_BY", "DEVELOPED_BY", "HAS_ADOPTION_RATE"],
            "COMPETITOR": ["COMPETES_WITH", "THREATENS", "TARGETS"],
            "REGION": ["CONTAINS", "HAS_COST_STRUCTURE", "HAS_PRICING"],
            "COMMITMENT": ["PROMISED_TO", "DELIVERED_BY", "DEPENDS_ON"]
        }

def ingest_single_pdf(pdf_name: str, source_dir: Path) -> bool:
    """Ingest a single PDF file"""
    
    print(f"\n{'='*60}")
    print(f"Ingesting: {pdf_name}")
    print(f"{'='*60}")
    
    # Copy PDF to local data directory
    target_dir = Path("data")
    target_dir.mkdir(exist_ok=True)
    
    source_path = source_dir / pdf_name
    if not source_path.exists():
        print(f"Error: {source_path} not found!")
        return False
    
    target_path = target_dir / pdf_name
    shutil.copy2(source_path, target_path)
    print(f"✓ Copied {pdf_name} to data directory")
    
    # Initialize pipeline
    config = Config()
    schema = SpyroGraphSchema()
    pipeline = KnowledgeGraphPipeline(config=config, schema=schema)
    
    try:
        # Process single document
        print(f"\nProcessing {pdf_name}...")
        results = pipeline.process_multiple_documents(
            file_paths=[str(target_path)],
            clear_existing=False  # Keep existing data
        )
        
        print(f"\n✅ Successfully ingested {pdf_name}")
        print(f"   - Nodes extracted: {results['total_nodes']}")
        
        # Show entity breakdown if available
        if 'node_types' in results['graph']:
            print("\n   Entity types extracted:")
            for entity_type, count in sorted(results['graph']['node_types'].items(), 
                                           key=lambda x: x[1], reverse=True)[:5]:
                print(f"     - {entity_type}: {count}")
        
        # Show relationship breakdown if available
        if 'relationship_types' in results['graph']:
            print("\n   Relationships discovered:")
            for rel_type, count in sorted(results['graph']['relationship_types'].items(), 
                                        key=lambda x: x[1], reverse=True)[:5]:
                print(f"     - {rel_type}: {count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Failed to ingest {pdf_name}: {e}")
        if "rate_limit" in str(e).lower():
            print("   Rate limit detected. Please wait before trying the next document.")
        return False

def main():
    """Main function to ingest PDFs one by one"""
    
    # Source directory
    source_dir = Path("/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/data/pdfs")
    
    # List of PDFs to ingest in order
    pdfs_to_ingest = [
        "Regional_Cost_Analysis_Report.pdf",
        "Customer_Commitment_Tracking_Report.pdf",
        "Product_Operational_Health_Report.pdf",
        "Feature_Adoption_Metrics_Report.pdf"
    ]
    
    print("SpyroSolutions Single PDF Ingestion")
    print("=" * 60)
    print(f"Total PDFs to ingest: {len(pdfs_to_ingest)}")
    
    # Check if we're starting with a specific PDF
    if len(sys.argv) > 1:
        start_index = int(sys.argv[1]) - 1
        print(f"Starting from PDF #{start_index + 1}: {pdfs_to_ingest[start_index]}")
    else:
        start_index = 0
        print("Starting with the first PDF")
    
    # Ingest first PDF only (or specified PDF)
    pdf_name = pdfs_to_ingest[start_index]
    success = ingest_single_pdf(pdf_name, source_dir)
    
    if success:
        print(f"\n✅ Successfully completed ingestion of PDF #{start_index + 1}")
        print(f"\nNext steps:")
        print(f"1. Wait 30-60 seconds to avoid rate limits")
        print(f"2. Run the next PDF:")
        print(f"   python3 ingest_single_report.py {start_index + 2}")
        
        if start_index < len(pdfs_to_ingest) - 1:
            print(f"\nRemaining PDFs to ingest:")
            for i in range(start_index + 1, len(pdfs_to_ingest)):
                print(f"   {i + 1}. {pdfs_to_ingest[i]}")
    else:
        print(f"\n❌ Failed to ingest PDF #{start_index + 1}")
        print(f"Please wait a few minutes and retry:")
        print(f"   python3 ingest_single_report.py {start_index + 1}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())