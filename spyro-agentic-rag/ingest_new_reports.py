#!/usr/bin/env python3
"""Ingest new PDF reports into LlamaIndex knowledge graph"""

import os
import sys
from pathlib import Path
import shutil
from typing import List

# Add llamaindex-knowledge-graph to path
LLAMAINDEX_PATH = "/Users/eugene/dev/apps/n8n_workflow_runner/llamaindex-knowledge-graph"
sys.path.append(LLAMAINDEX_PATH)

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

def copy_pdfs_to_llamaindex(pdf_dir: Path) -> List[str]:
    """Copy PDF reports to llamaindex-knowledge-graph data directory"""
    target_dir = Path(LLAMAINDEX_PATH) / "data"
    target_dir.mkdir(exist_ok=True)
    
    copied_files = []
    pdf_files = list(pdf_dir.glob("*.pdf"))
    
    print(f"Copying {len(pdf_files)} PDF files to LlamaIndex data directory...")
    
    for pdf_file in pdf_files:
        target_path = target_dir / pdf_file.name
        shutil.copy2(pdf_file, target_path)
        copied_files.append(str(target_path.relative_to(LLAMAINDEX_PATH)))
        print(f"  ✓ Copied: {pdf_file.name}")
    
    return copied_files

def main():
    """Main ingestion function"""
    
    print("SpyroSolutions New Reports Ingestion")
    print("=" * 60)
    
    # Path to PDF reports
    pdf_dir = Path("/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/data/pdfs")
    
    if not pdf_dir.exists():
        print(f"Error: PDF directory not found: {pdf_dir}")
        return 1
    
    # Change to llamaindex directory
    original_dir = os.getcwd()
    os.chdir(LLAMAINDEX_PATH)
    
    try:
        # Copy PDFs to llamaindex data directory
        report_paths = copy_pdfs_to_llamaindex(pdf_dir)
        
        if not report_paths:
            print("Error: No PDF files found to ingest!")
            return 1
        
        # Configure pipeline with SpyroSolutions schema
        config = Config()
        schema = SpyroGraphSchema()
        
        # Initialize pipeline
        print("\nInitializing knowledge graph pipeline...")
        pipeline = KnowledgeGraphPipeline(config=config, schema=schema)
        
        # Process reports
        print(f"\nProcessing {len(report_paths)} new SpyroSolutions reports:")
        for report in report_paths:
            print(f"  - {Path(report).name}")
        
        print("\nThis will extract:")
        print("  - Regional cost data and pricing strategies")
        print("  - Customer commitments and SLA performance")
        print("  - Product operational health metrics")
        print("  - Feature adoption rates and ROI analysis")
        
        # Process all reports
        results = pipeline.process_multiple_documents(
            file_paths=report_paths,
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
                                           key=lambda x: x[1], reverse=True)[:15]:
                print(f"  {entity_type}: {count}")
        
        # Show relationship breakdown  
        if 'relationship_types' in results['graph']:
            print("\nRelationships discovered:")
            for rel_type, count in sorted(results['graph']['relationship_types'].items(), 
                                        key=lambda x: x[1], reverse=True)[:15]:
                print(f"  {rel_type}: {count}")
        
        print("\n" + "="*60)
        print("KNOWLEDGE GRAPH ENHANCED WITH")
        print("="*60)
        
        print("\n✅ The knowledge graph now includes:")
        print("\n1. Regional Cost Analysis:")
        print("   - Operational costs by product and region")
        print("   - Cost-per-customer breakdowns")
        print("   - Profitability margins and optimization opportunities")
        
        print("\n2. Customer Commitment Tracking:")
        print("   - Feature promises and delivery status")
        print("   - SLA performance history")
        print("   - At-risk commitments and mitigation plans")
        
        print("\n3. Product Operational Health:")
        print("   - Customer satisfaction scores by product")
        print("   - Operational issues and resolution status")
        print("   - Feature adoption metrics")
        
        print("\n4. Feature Adoption Metrics:")
        print("   - Adoption rates by customer segment")
        print("   - ROI analysis for each feature")
        print("   - Competitive analysis and gaps")
        
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        
        print("\n1. Re-run the business questions test:")
        print("   cd /Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag")
        print("   ./scripts/test_all_business_questions.sh")
        
        print("\n2. The following questions should now have answers:")
        print("   - Which teams have the highest operational costs?")
        print("   - What commitments are we at risk of missing?")
        print("   - Which regions have the best profitability margins?")
        print("   - What's the adoption rate of our newest features?")
        print("   - Which products have operational issues affecting customer satisfaction?")
        
        print("\n✅ Ingestion completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Return to original directory
        os.chdir(original_dir)
    
    return 0

if __name__ == "__main__":
    exit(main())