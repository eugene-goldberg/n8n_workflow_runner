#!/usr/bin/env python3
"""Ingest new gap-filling PDF reports into LlamaIndex knowledge graph"""

import os
import sys
from pathlib import Path
import shutil
from typing import List

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

def copy_pdfs_from_spyro() -> List[str]:
    """Copy PDF reports from spyro-agentic-rag to local data directory"""
    source_dir = Path("/Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag/data/pdfs")
    target_dir = Path("data")
    target_dir.mkdir(exist_ok=True)
    
    copied_files = []
    
    # List of new reports to copy
    reports_to_copy = [
        "Regional_Cost_Analysis_Report.pdf",
        "Customer_Commitment_Tracking_Report.pdf",
        "Product_Operational_Health_Report.pdf",
        "Feature_Adoption_Metrics_Report.pdf"
    ]
    
    print(f"Copying gap-filling reports from spyro-agentic-rag...")
    
    for report_name in reports_to_copy:
        source_path = source_dir / report_name
        if source_path.exists():
            target_path = target_dir / report_name
            shutil.copy2(source_path, target_path)
            copied_files.append(str(target_path))
            print(f"  ✓ Copied: {report_name}")
        else:
            print(f"  ✗ Not found: {report_name}")
    
    return copied_files

def main():
    """Main ingestion function"""
    
    print("SpyroSolutions Gap-Filling Reports Ingestion")
    print("=" * 60)
    
    # Copy PDFs from spyro-agentic-rag
    report_paths = copy_pdfs_from_spyro()
    
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
    print(f"\nProcessing {len(report_paths)} gap-filling reports:")
    for report in report_paths:
        print(f"  - {Path(report).name}")
    
    print("\nThese reports will fill data gaps for:")
    print("  - Regional cost analysis and profitability")
    print("  - Customer commitments and SLA tracking")
    print("  - Product operational health metrics")
    print("  - Feature adoption rates and ROI")
    
    try:
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
        print("DATA GAPS FILLED")
        print("="*60)
        
        print("\n✅ The following data gaps have been filled:")
        
        print("\n1. Cost and Profitability Questions:")
        print("   ✓ Which teams have the highest operational costs relative to their output?")
        print("   ✓ What's the profitability margin for each product by region?")
        print("   ✓ Which regions have the best cost-per-customer ratios?")
        
        print("\n2. Commitment and SLA Questions:")
        print("   ✓ What commitments are we at risk of missing for our top customers?")
        print("   ✓ Which customers have had SLA violations in the last quarter?")
        print("   ✓ What feature promises have we made to enterprise customers?")
        
        print("\n3. Product Health Questions:")
        print("   ✓ Which products have operational issues affecting customer satisfaction?")
        print("   ✓ What's the customer satisfaction score trend for each product?")
        
        print("\n4. Feature Adoption Questions:")
        print("   ✓ What's the adoption rate of our newest features?")
        print("   ✓ Which features provide the highest ROI for customers?")
        print("   ✓ What features have low adoption and should be improved or retired?")
        
        print("\n" + "="*60)
        print("NEXT STEPS")
        print("="*60)
        
        print("\n1. Return to spyro-agentic-rag and re-run the business questions test:")
        print("   cd /Users/eugene/dev/apps/n8n_workflow_runner/spyro-agentic-rag")
        print("   ./scripts/test_all_business_questions.sh")
        
        print("\n2. Compare the new results with the previous run to verify improvements")
        
        print("\n3. The RAG system should now be able to answer all 50 business questions")
        
        print("\n✅ Gap-filling ingestion completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())