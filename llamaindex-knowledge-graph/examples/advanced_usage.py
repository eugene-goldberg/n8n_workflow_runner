#!/usr/bin/env python3
"""Advanced usage examples for the knowledge graph pipeline"""

import os
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.pipeline import KnowledgeGraphPipeline
from src.config import Config, GraphSchema
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CustomGraphSchema(GraphSchema):
    """Custom schema for financial documents"""
    
    def __init__(self):
        super().__init__(
            entities=[
                # Financial entities
                "COMPANY", "SUBSIDIARY", "INVESTOR", "ANALYST",
                # Products and services
                "PRODUCT", "SERVICE", "TECHNOLOGY", "PATENT",
                # Financial metrics
                "REVENUE", "EXPENSE", "PROFIT", "ASSET", "LIABILITY",
                # People and roles
                "EXECUTIVE", "BOARD_MEMBER", "EMPLOYEE",
                # Events and time
                "QUARTER", "FISCAL_YEAR", "ACQUISITION", "MERGER",
                # Geography
                "COUNTRY", "REGION", "MARKET"
            ],
            relations=[
                # Corporate structure
                "OWNS", "SUBSIDIARY_OF", "ACQUIRED", "MERGED_WITH",
                # Financial relationships
                "GENERATED_REVENUE", "INCURRED_EXPENSE", "REPORTED_PROFIT",
                # People relationships
                "CEO_OF", "BOARD_MEMBER_OF", "WORKS_FOR", "REPORTS_TO",
                # Product relationships
                "PRODUCES", "SELLS", "LICENSES", "USES_TECHNOLOGY",
                # Market relationships
                "OPERATES_IN", "COMPETES_WITH", "PARTNERS_WITH",
                # Time relationships
                "OCCURRED_IN", "REPORTED_IN", "FORECAST_FOR"
            ],
            validation_schema={
                "COMPANY": ["OWNS", "SUBSIDIARY_OF", "PRODUCES", "OPERATES_IN", "GENERATED_REVENUE"],
                "EXECUTIVE": ["CEO_OF", "WORKS_FOR", "REPORTS_TO"],
                "PRODUCT": ["PRODUCED_BY", "USES_TECHNOLOGY", "GENERATED_REVENUE"],
                "REVENUE": ["GENERATED_BY", "REPORTED_IN", "FROM_MARKET"],
                "ACQUISITION": ["OCCURRED_IN", "INVOLVED", "VALUE"]
            }
        )


def analyze_financial_documents(pipeline: KnowledgeGraphPipeline, pdf_paths: List[Path]) -> Dict:
    """Analyze financial documents and extract key insights"""
    
    logger.info("Analyzing financial documents...")
    
    # Process all documents
    results = pipeline.process_multiple_documents(
        file_paths=pdf_paths,
        clear_existing=True
    )
    
    # Run analysis queries
    insights = {}
    
    analysis_queries = {
        "revenue_sources": "What are all the revenue sources and their amounts?",
        "key_executives": "Who are the executives and what companies do they lead?",
        "market_presence": "Which markets and regions does the company operate in?",
        "acquisitions": "What acquisitions or mergers were mentioned?",
        "product_portfolio": "What products and services are offered?",
        "financial_performance": "What are the key financial metrics and their trends?",
        "competitive_landscape": "Who are the main competitors?",
        "technology_stack": "What technologies are being used or developed?"
    }
    
    for key, query in analysis_queries.items():
        try:
            logger.info(f"Running analysis: {key}")
            response = pipeline.query(query)
            insights[key] = response
        except Exception as e:
            logger.error(f"Failed to analyze {key}: {e}")
            insights[key] = f"Error: {e}"
    
    return insights


def create_executive_summary(insights: Dict) -> str:
    """Create an executive summary from the insights"""
    
    summary = """
EXECUTIVE SUMMARY
=================

Financial Performance:
{financial_performance}

Revenue Sources:
{revenue_sources}

Leadership:
{key_executives}

Market Presence:
{market_presence}

Strategic Activities:
{acquisitions}

Product Portfolio:
{product_portfolio}

Technology:
{technology_stack}

Competitive Position:
{competitive_landscape}
"""
    
    return summary.format(**insights)


def main():
    """Demonstrate advanced usage patterns"""
    
    # Use custom schema for financial documents
    config = Config()
    schema = CustomGraphSchema()
    
    try:
        # Initialize pipeline with custom schema
        pipeline = KnowledgeGraphPipeline(config=config, schema=schema)
        
        # Example 1: Analyze annual reports
        logger.info("\n" + "="*60)
        logger.info("Example 1: Analyzing Annual Reports")
        logger.info("="*60)
        
        annual_reports = [
            Path("../data/annual_report_2023.pdf"),
            Path("../data/annual_report_2022.pdf"),
            Path("../data/annual_report_2021.pdf")
        ]
        
        existing_reports = [p for p in annual_reports if p.exists()]
        
        if existing_reports:
            insights = analyze_financial_documents(pipeline, existing_reports)
            
            # Generate executive summary
            summary = create_executive_summary(insights)
            logger.info("\n" + summary)
            
            # Save summary to file
            with open("executive_summary.txt", "w") as f:
                f.write(summary)
            logger.info("Executive summary saved to executive_summary.txt")
        else:
            logger.warning("No annual reports found in data directory")
        
        # Example 2: Complex multi-hop queries
        logger.info("\n" + "="*60)
        logger.info("Example 2: Complex Multi-hop Queries")
        logger.info("="*60)
        
        complex_queries = [
            "Which executives manage products that generate more than $1M in revenue?",
            "What companies were acquired by firms operating in the Asia Pacific region?",
            "Which technologies are used by our most profitable products?",
            "What are the connections between board members across different companies?",
            "How has revenue changed for products launched in the last 3 years?"
        ]
        
        for query in complex_queries[:3]:
            logger.info(f"\nComplex Query: {query}")
            try:
                response = pipeline.query(query)
                logger.info(f"Response: {response[:500]}...")  # Truncate long responses
            except Exception as e:
                logger.error(f"Query failed: {e}")
        
        # Example 3: Export graph data
        logger.info("\n" + "="*60)
        logger.info("Example 3: Exporting Graph Data")
        logger.info("="*60)
        
        # Get all entities of specific types
        export_queries = {
            "companies": "MATCH (c:COMPANY) RETURN c.name as name, c.revenue as revenue",
            "executives": "MATCH (e:EXECUTIVE)-[r:CEO_OF|WORKS_FOR]->(c:COMPANY) RETURN e.name as executive, type(r) as role, c.name as company",
            "products": "MATCH (p:PRODUCT)-[r:PRODUCED_BY]->(c:COMPANY) RETURN p.name as product, c.name as company",
            "acquisitions": "MATCH (c1:COMPANY)-[a:ACQUIRED]->(c2:COMPANY) RETURN c1.name as acquirer, c2.name as acquired, a.date as date, a.value as value"
        }
        
        # Note: These are Cypher queries that would need direct Neo4j access
        # The pipeline could be extended to support direct Cypher queries
        
        logger.info("Graph data export queries prepared (requires direct Neo4j access)")
        
        # Example 4: Monitoring and metrics
        logger.info("\n" + "="*60)
        logger.info("Example 4: Pipeline Metrics")
        logger.info("="*60)
        
        stats = pipeline.graph.get_statistics()
        
        # Calculate metrics
        total_nodes = stats['node_count']
        total_relationships = stats['relationship_count']
        avg_relationships_per_node = total_relationships / max(total_nodes, 1)
        
        logger.info(f"Total nodes: {total_nodes}")
        logger.info(f"Total relationships: {total_relationships}")
        logger.info(f"Average relationships per node: {avg_relationships_per_node:.2f}")
        
        # Analyze node type distribution
        if stats['node_types']:
            logger.info("\nNode Type Distribution:")
            sorted_types = sorted(stats['node_types'].items(), key=lambda x: x[1], reverse=True)
            for node_type, count in sorted_types[:10]:
                percentage = (count / total_nodes) * 100
                logger.info(f"  {node_type}: {count} ({percentage:.1f}%)")
        
        # Analyze relationship type distribution
        if stats['relationship_types']:
            logger.info("\nRelationship Type Distribution:")
            sorted_rels = sorted(stats['relationship_types'].items(), key=lambda x: x[1], reverse=True)
            for rel_type, count in sorted_rels[:10]:
                percentage = (count / total_relationships) * 100
                logger.info(f"  {rel_type}: {count} ({percentage:.1f}%)")
        
    except Exception as e:
        logger.error(f"Pipeline error: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())