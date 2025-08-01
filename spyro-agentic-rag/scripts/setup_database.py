#!/usr/bin/env python3
"""
Setup script to initialize the Neo4j database with SpyroSolutions data
and create necessary indexes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import GraphDatabase
from src.utils.config import Config
from src.utils.logging import setup_logging

logger = setup_logging(__name__)


class DatabaseSetup:
    def __init__(self, config: Config):
        self.config = config
        self.driver = GraphDatabase.driver(
            config.neo4j_uri,
            auth=(config.neo4j_username, config.neo4j_password)
        )
        
    def create_indexes(self):
        """Create vector and fulltext indexes"""
        with self.driver.session() as session:
            # Create vector index
            try:
                session.run(f"""
                CREATE VECTOR INDEX {self.config.vector_index_name} IF NOT EXISTS
                FOR (n:Document)
                ON n.embedding
                OPTIONS {{
                    indexConfig: {{
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }}
                }}
                """)
                logger.info(f"Vector index '{self.config.vector_index_name}' created/verified")
            except Exception as e:
                logger.warning(f"Vector index creation warning: {e}")
                
            # Create fulltext index
            try:
                session.run(f"""
                CREATE FULLTEXT INDEX {self.config.fulltext_index_name} IF NOT EXISTS
                FOR (n:Document)
                ON EACH [n.text, n.name, n.description]
                """)
                logger.info(f"Fulltext index '{self.config.fulltext_index_name}' created/verified")
            except Exception as e:
                logger.warning(f"Fulltext index creation warning: {e}")
                
    def load_sample_data(self):
        """Load SpyroSolutions sample data"""
        with self.driver.session() as session:
            # Clear existing data
            session.run("MATCH (n) DETACH DELETE n")
            logger.info("Cleared existing data")
            
            # Create Products
            session.run("""
            CREATE (p1:Product {
                name: 'SpyroCloud',
                type: 'Platform',
                description: 'Comprehensive cloud platform for enterprise solutions',
                features: ['Multi-tenant', 'Scalable', 'API-first', 'Real-time analytics'],
                market_focus: 'Enterprise SaaS'
            })
            CREATE (p2:Product {
                name: 'SpyroAI',
                type: 'AI/ML',
                description: 'Advanced AI and machine learning capabilities',
                features: ['AutoML', 'NLP', 'Computer Vision', 'Predictive Analytics'],
                market_focus: 'AI-driven automation'
            })
            CREATE (p3:Product {
                name: 'SpyroSecure',
                type: 'Security',
                description: 'Enterprise-grade security and compliance platform',
                features: ['Zero Trust', 'Compliance Automation', 'Threat Detection', 'Data Encryption'],
                market_focus: 'Security & Compliance'
            })
            """)
            
            # Create Customers
            session.run("""
            CREATE (c1:Customer {
                name: 'TechCorp',
                industry: 'Technology',
                size: 'Enterprise',
                region: 'North America'
            })
            CREATE (c2:Customer {
                name: 'FinanceHub',
                industry: 'Financial Services',
                size: 'Enterprise',
                region: 'Europe'
            })
            CREATE (c3:Customer {
                name: 'HealthFirst',
                industry: 'Healthcare',
                size: 'Mid-Market',
                region: 'Asia Pacific'
            })
            """)
            
            # Create Subscriptions and relationships
            session.run("""
            MATCH (c:Customer {name: 'TechCorp'})
            MATCH (p:Product {name: 'SpyroCloud'})
            CREATE (s:SaaSSubscription {
                product: 'SpyroCloud',
                value: '$8M',
                start_date: date('2023-01-15'),
                end_date: date('2025-01-14'),
                status: 'Active'
            })
            CREATE (c)-[:SUBSCRIBES_TO {
                revenue: '$8M',
                contract_length: 24,
                renewal_probability: 0.85
            }]->(s)
            CREATE (c)-[:USES {
                satisfaction_score: 4.5,
                usage_level: 'High'
            }]->(p)
            CREATE (arr:AnnualRecurringRevenue {
                amount: '$8M',
                year: 2024
            })
            CREATE (s)-[:GENERATES {
                monthly_value: 666667,
                growth_rate: 0.15
            }]->(arr)
            """)
            
            session.run("""
            MATCH (c:Customer {name: 'FinanceHub'})
            MATCH (p1:Product {name: 'SpyroAI'})
            MATCH (p2:Product {name: 'SpyroSecure'})
            CREATE (s:SaaSSubscription {
                product: 'SpyroAI + SpyroSecure',
                value: '$5M',
                start_date: date('2023-06-01'),
                end_date: date('2024-05-31'),
                status: 'Active'
            })
            CREATE (c)-[:SUBSCRIBES_TO {
                revenue: '$5M',
                contract_length: 12,
                renewal_probability: 0.90
            }]->(s)
            CREATE (c)-[:USES {
                satisfaction_score: 4.8,
                usage_level: 'Very High'
            }]->(p1)
            CREATE (c)-[:USES {
                satisfaction_score: 4.9,
                usage_level: 'High'
            }]->(p2)
            CREATE (arr:AnnualRecurringRevenue {
                amount: '$5M',
                year: 2024
            })
            CREATE (s)-[:GENERATES {
                monthly_value: 416667,
                growth_rate: 0.20
            }]->(arr)
            """)
            
            # Create Teams and Projects
            session.run("""
            CREATE (t1:Team {
                name: 'Cloud Platform Team',
                department: 'Engineering',
                size: 25,
                focus_area: 'Platform Development'
            })
            CREATE (t2:Team {
                name: 'AI Research Team',
                department: 'R&D',
                size: 15,
                focus_area: 'ML/AI Innovation'
            })
            CREATE (t3:Team {
                name: 'Security Team',
                department: 'Security',
                size: 20,
                focus_area: 'Security & Compliance'
            })
            """)
            
            # Create team-product relationships
            session.run("""
            MATCH (t1:Team {name: 'Cloud Platform Team'})
            MATCH (p:Product {name: 'SpyroCloud'})
            CREATE (t1)-[:SUPPORTS {
                alignment_score: 0.95,
                priority: 'High'
            }]->(p)
            """)
            
            session.run("""
            MATCH (t2:Team {name: 'AI Research Team'})
            MATCH (p:Product {name: 'SpyroAI'})
            CREATE (t2)-[:SUPPORTS {
                alignment_score: 0.98,
                priority: 'Critical'
            }]->(p)
            """)
            
            # Create Risks and Objectives
            session.run("""
            CREATE (r1:Risk {
                type: 'Technical',
                description: 'Legacy system integration challenges',
                severity: 'High',
                mitigation_strategy: 'Phased migration approach',
                status: 'Active'
            })
            CREATE (r2:Risk {
                type: 'Market',
                description: 'Increased competition in AI space',
                severity: 'Medium',
                mitigation_strategy: 'Accelerate innovation cycle',
                status: 'Monitoring'
            })
            
            CREATE (o1:Objective {
                title: 'Expand Enterprise Market Share',
                description: 'Increase enterprise customer base by 40%',
                target_date: date('2024-12-31'),
                progress: 0.65,
                status: 'On Track'
            })
            CREATE (o2:Objective {
                title: 'AI Platform Enhancement',
                description: 'Launch next-gen AI capabilities',
                target_date: date('2024-09-30'),
                progress: 0.80,
                status: 'On Track'
            })
            """)
            
            # Create objective-risk relationship
            session.run("""
            MATCH (o1:Objective {title: 'Expand Enterprise Market Share'})
            MATCH (r1:Risk {type: 'Technical'})
            CREATE (o1)-[:AT_RISK {
                likelihood: 0.3,
                impact: 'High',
                identified_date: date('2024-01-15')
            }]->(r1)
            """)
            
            # Create sample Documents for RAG
            session.run("""
            CREATE (d1:Document {
                text: 'SpyroCloud provides comprehensive cloud platform capabilities with multi-tenant architecture, 
                       scalable infrastructure, and real-time analytics. It serves as the foundation for 
                       enterprise digital transformation.',
                name: 'SpyroCloud Overview',
                description: 'Product overview document',
                embedding: null
            })
            CREATE (d2:Document {
                text: 'SpyroAI leverages advanced machine learning algorithms including AutoML, natural language 
                       processing, and computer vision to deliver intelligent automation solutions for enterprises.',
                name: 'SpyroAI Capabilities',
                description: 'AI product features',
                embedding: null
            })
            CREATE (d3:Document {
                text: 'TechCorp has an $8M annual subscription for SpyroCloud with high satisfaction scores 
                       and 85% renewal probability. They are a strategic enterprise customer in North America.',
                name: 'TechCorp Account Summary',
                description: 'Customer account details',
                embedding: null
            })
            """)
            
            logger.info("Sample data loaded successfully")
            
    def verify_setup(self):
        """Verify the database setup"""
        with self.driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count")
            logger.info("Node counts:")
            for record in result:
                logger.info(f"  {record['label']}: {record['count']}")
                
            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count")
            logger.info("Relationship counts:")
            for record in result:
                logger.info(f"  {record['type']}: {record['count']}")
                
    def close(self):
        """Close database connection"""
        self.driver.close()


def main():
    """Main setup function"""
    logger.info("Starting SpyroSolutions database setup...")
    
    try:
        # Load configuration
        config = Config.from_env()
        
        # Create setup instance
        setup = DatabaseSetup(config)
        
        # Run setup steps
        logger.info("Creating indexes...")
        setup.create_indexes()
        
        logger.info("Loading sample data...")
        setup.load_sample_data()
        
        logger.info("Verifying setup...")
        setup.verify_setup()
        
        setup.close()
        
        logger.info("Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Setup failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()