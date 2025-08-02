"""Data generator for creating realistic test data"""

import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import uuid
from faker import Faker


class DataGenerator:
    """Generates realistic test data for SpyroSolutions entities"""
    
    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional seed for deterministic output"""
        self.seed = seed
        self.fake = Faker()
        if seed is not None:
            # Set both random and Faker seeds for determinism
            random.seed(seed)
            Faker.seed(seed)
        
        # Pre-generated data for relationships
        self.customers = []
        self.products = []
        self.teams = []
        self.subscriptions = []
    
    def _reset_random_state(self, entity_type: str):
        """Reset random state for consistent generation per entity type"""
        if self.seed is not None:
            # Use entity type hash to create unique but deterministic seed
            entity_seed = self.seed + hash(entity_type) % 1000
            random.seed(entity_seed)
            # Note: Faker state is global, so we reset it less frequently
    
    def generate_customer(self, index: int) -> Dict[str, Any]:
        """Generate a customer entity"""
        size_options = ["SMB", "Mid-Market", "Enterprise"]
        size_weights = [0.5, 0.3, 0.2]
        industry_options = [
            "Technology", "Finance", "Healthcare", "Retail", 
            "Manufacturing", "Education", "Media", "Consulting"
        ]
        
        # Use deterministic selection based on index for consistency
        size_index = index % len(size_options)
        if index < 5:  # First few customers get specific sizes for testing
            size = size_options[size_index]
        else:
            # Use weighted random for the rest
            rand_val = random.random()
            if rand_val < 0.5:
                size = "SMB"
            elif rand_val < 0.8:
                size = "Mid-Market"
            else:
                size = "Enterprise"
        
        # Base ARR based on size
        arr_ranges = {
            "SMB": (10000, 100000),
            "Mid-Market": (100000, 1000000),
            "Enterprise": (1000000, 10000000)
        }
        arr_min, arr_max = arr_ranges[size]
        
        # Make ARR deterministic for first few customers
        if index < 5:
            arr_range = arr_max - arr_min
            arr = arr_min + (arr_range * (index + 1) // 10)
        else:
            arr = random.randint(arr_min, arr_max)
        
        # Make health_score deterministic for first few customers
        if index < 5:
            health_score = 70 + (index * 5)  # 70, 75, 80, 85, 90
        else:
            health_score = random.randint(40, 100)
        
        customer = {
            "id": f"cust_{index:04d}",
            "name": self.fake.company(),
            "size": size,
            "industry": random.choice(industry_options),
            "arr": arr,
            "employee_count": random.randint(10, 10000),
            "created_date": self.fake.date_between(start_date="-3y", end_date="-6m").isoformat(),
            "updated_date": self.fake.date_between(start_date="-6m", end_date="today").isoformat(),
            "health_score": health_score,
            "churn_risk": random.choice(["low", "medium", "high"]),
            "region": random.choice(["North America", "Europe", "Asia Pacific", "Latin America"]),
            "website": self.fake.url(),
            "contact_email": self.fake.company_email(),
            "account_manager": self.fake.name()
        }
        
        self.customers.append(customer)
        return customer
    
    def generate_product(self, index: int) -> Dict[str, Any]:
        """Generate a product entity"""
        products = [
            {
                "name": "SpyroCloud",
                "category": "Infrastructure",
                "description": "Cloud infrastructure management platform",
                "features": ["Auto-scaling", "Multi-region deployment", "Real-time monitoring", "API Gateway"]
            },
            {
                "name": "SpyroAI",
                "category": "Analytics",
                "description": "AI-powered analytics and insights platform",
                "features": ["Predictive Analytics", "ML Model Training", "Real-time Insights", "Custom Models"]
            },
            {
                "name": "SpyroSecure",
                "category": "Security",
                "description": "Enterprise security and compliance platform",
                "features": ["Threat Detection", "Compliance Reports", "Access Control", "Audit Logs"]
            }
        ]
        
        if index < len(products):
            product_template = products[index]
        else:
            product_template = random.choice(products)
        
        product = {
            "id": f"prod_{index:04d}",
            "name": product_template["name"],
            "category": product_template["category"],
            "description": product_template["description"],
            "features": product_template["features"],
            "version": f"{random.randint(1, 5)}.{random.randint(0, 20)}.{random.randint(0, 50)}",
            "release_date": self.fake.date_between(start_date="-2y", end_date="-3m").isoformat(),
            "status": random.choice(["active", "beta", "deprecated"]),
            "pricing_model": random.choice(["subscription", "usage-based", "tiered"]),
            "base_price": random.randint(100, 10000)
        }
        
        self.products.append(product)
        return product
    
    def generate_subscription(self, index: int) -> Dict[str, Any]:
        """Generate a SaaS subscription entity"""
        if not self.customers or not self.products:
            raise ValueError("Generate customers and products first")
        
        customer = random.choice(self.customers)
        product = random.choice(self.products)
        
        # Calculate MRR based on customer size and product
        mrr_multipliers = {
            "SMB": 0.8,
            "Mid-Market": 1.0,
            "Enterprise": 1.5
        }
        base_mrr = product["base_price"] * mrr_multipliers.get(customer["size"], 1.0)
        mrr = int(base_mrr * random.uniform(0.8, 1.2))
        
        start_date = self.fake.date_between(start_date="-2y", end_date="-1m")
        
        subscription = {
            "id": f"sub_{index:04d}",
            "customer_id": customer["id"],
            "product_id": product["id"],
            "mrr": mrr,
            "arr": mrr * 12,
            "start_date": start_date.isoformat(),
            "end_date": (start_date + timedelta(days=365)).isoformat(),
            "status": random.choice(["active", "pending_renewal", "churned"]),
            "payment_method": random.choice(["credit_card", "invoice", "wire_transfer"]),
            "billing_cycle": random.choice(["monthly", "quarterly", "annual"]),
            "discount_percentage": random.choice([0, 5, 10, 15, 20]),
            "seats": random.randint(1, 500),
            "usage_limit": random.randint(1000, 100000)
        }
        
        self.subscriptions.append(subscription)
        return subscription
    
    def generate_team(self, index: int) -> Dict[str, Any]:
        """Generate a team entity"""
        team_names = [
            "Cloud Platform Team",
            "AI Research Team", 
            "Security Team",
            "Customer Success Team",
            "Product Development Team",
            "DevOps Team",
            "Data Engineering Team",
            "Mobile Team"
        ]
        
        focus_areas = [
            "infrastructure", "development", "security", 
            "customer_success", "analytics", "operations"
        ]
        
        team = {
            "id": f"team_{index:04d}",
            "name": team_names[index % len(team_names)] if index < len(team_names) else f"Team {index}",
            "size": random.randint(3, 50),
            "focus_area": random.choice(focus_areas),
            "manager": self.fake.name(),
            "created_date": self.fake.date_between(start_date="-3y", end_date="-1y").isoformat(),
            "velocity": random.randint(50, 100),
            "capacity": random.randint(10, 100),
            "utilization": round(random.uniform(0.5, 0.95), 2),
            "location": random.choice(["San Francisco", "New York", "London", "Singapore", "Remote"])
        }
        
        # Link to products
        if self.products:
            team["supported_products"] = random.sample(
                [p["id"] for p in self.products], 
                k=min(len(self.products), random.randint(1, 3))
            )
        
        self.teams.append(team)
        return team
    
    def generate_project(self, index: int) -> Dict[str, Any]:
        """Generate a project entity"""
        if not self.teams:
            raise ValueError("Generate teams first")
        
        project_types = ["feature", "infrastructure", "security", "performance", "migration"]
        statuses = ["planning", "active", "completed", "on_hold", "cancelled"]
        
        team = random.choice(self.teams)
        
        project = {
            "id": f"proj_{index:04d}",
            "name": f"{self.fake.catch_phrase()} Project",
            "description": self.fake.text(max_nb_chars=200),
            "type": random.choice(project_types),
            "status": random.choice(statuses),
            "team_id": team["id"],
            "start_date": self.fake.date_between(start_date="-6m", end_date="-1m").isoformat(),
            "end_date": self.fake.date_between(start_date="+1m", end_date="+6m").isoformat(),
            "budget": random.randint(10000, 500000),
            "completion_percentage": random.randint(0, 100),
            "priority": random.choice(["low", "medium", "high", "critical"]),
            "stakeholders": [self.fake.name() for _ in range(random.randint(1, 5))]
        }
        
        # Link to customers if relevant
        if self.customers and random.random() > 0.5:
            project["customer_id"] = random.choice(self.customers)["id"]
        
        return project
    
    def generate_risk(self, index: int) -> Dict[str, Any]:
        """Generate a risk entity"""
        risk_types = ["operational", "financial", "security", "compliance", "strategic", "reputational"]
        severities = ["low", "medium", "high", "critical"]
        
        risk = {
            "id": f"risk_{index:04d}",
            "type": random.choice(risk_types),
            "severity": random.choice(severities),
            "description": self.fake.text(max_nb_chars=150),
            "probability": round(random.uniform(0.1, 0.9), 2),
            "impact": random.randint(1, 10),
            "identified_date": self.fake.date_between(start_date="-6m", end_date="today").isoformat(),
            "status": random.choice(["identified", "analyzing", "mitigating", "resolved", "accepted"]),
            "owner": self.fake.name(),
            "mitigation_plan": self.fake.text(max_nb_chars=200) if random.random() > 0.3 else None
        }
        
        # Link to entities
        if random.random() > 0.5 and self.customers:
            risk["customer_id"] = random.choice(self.customers)["id"]
        if random.random() > 0.5 and self.teams:
            risk["team_id"] = random.choice(self.teams)["id"]
        
        return risk
    
    def generate_event(self, index: int) -> Dict[str, Any]:
        """Generate an event entity"""
        event_types = [
            "customer_meeting", "product_launch", "incident", 
            "maintenance", "training", "webinar", "conference"
        ]
        
        event = {
            "id": f"event_{index:04d}",
            "type": random.choice(event_types),
            "title": self.fake.catch_phrase(),
            "description": self.fake.text(max_nb_chars=150),
            "date": self.fake.date_time_between(start_date="-1y", end_date="+3m").isoformat(),
            "duration_hours": random.uniform(0.5, 8.0),
            "attendees": random.randint(2, 100),
            "location": random.choice([self.fake.city(), "Virtual", "Hybrid"]),
            "status": random.choice(["scheduled", "in_progress", "completed", "cancelled"]),
            "organizer": self.fake.name()
        }
        
        # Link to entities
        if event["type"] == "customer_meeting" and self.customers:
            event["customer_id"] = random.choice(self.customers)["id"]
        if self.teams:
            event["team_id"] = random.choice(self.teams)["id"]
        
        return event
    
    def generate_customer_success_score(self, customer_id: str) -> Dict[str, Any]:
        """Generate customer success score data"""
        return {
            "id": f"css_{customer_id}",
            "customer_id": customer_id,
            "score": random.randint(40, 100),
            "trend": random.choice(["improving", "stable", "declining"]),
            "factors": {
                "product_adoption": random.randint(30, 100),
                "support_tickets": random.randint(0, 50),
                "engagement_level": random.choice(["low", "medium", "high"]),
                "renewal_likelihood": random.uniform(0.3, 0.95)
            },
            "last_updated": datetime.now().isoformat(),
            "next_review_date": (datetime.now() + timedelta(days=random.randint(7, 30))).isoformat()
        }
    
    def get_schema(self) -> Dict[str, Dict[str, Any]]:
        """Get schema information for all entity types"""
        return {
            "Customer": {
                "fields": [
                    "id", "name", "size", "industry", "arr", "employee_count",
                    "created_date", "updated_date", "health_score", "churn_risk",
                    "region", "website", "contact_email", "account_manager"
                ],
                "count": 100,
                "sample": self.generate_customer(9999)  # Generate sample
            },
            "Product": {
                "fields": [
                    "id", "name", "category", "description", "features",
                    "version", "release_date", "status", "pricing_model", "base_price"
                ],
                "count": 3,
                "sample": self.generate_product(9999)
            },
            "SaaSSubscription": {
                "fields": [
                    "id", "customer_id", "product_id", "mrr", "arr",
                    "start_date", "end_date", "status", "payment_method",
                    "billing_cycle", "discount_percentage", "seats", "usage_limit"
                ],
                "count": 150,
                "sample": None  # Will generate after customers/products exist
            },
            "Team": {
                "fields": [
                    "id", "name", "size", "focus_area", "manager",
                    "created_date", "velocity", "capacity", "utilization",
                    "location", "supported_products"
                ],
                "count": 8,
                "sample": self.generate_team(9999)
            },
            "Project": {
                "fields": [
                    "id", "name", "description", "type", "status",
                    "team_id", "start_date", "end_date", "budget",
                    "completion_percentage", "priority", "stakeholders"
                ],
                "count": 20,
                "sample": None
            },
            "Risk": {
                "fields": [
                    "id", "type", "severity", "description", "probability",
                    "impact", "identified_date", "status", "owner",
                    "mitigation_plan", "customer_id", "team_id"
                ],
                "count": 30,
                "sample": None
            },
            "Event": {
                "fields": [
                    "id", "type", "title", "description", "date",
                    "duration_hours", "attendees", "location", "status",
                    "organizer", "customer_id", "team_id"
                ],
                "count": 50,
                "sample": None
            },
            "CustomerSuccessScore": {
                "fields": [
                    "id", "customer_id", "score", "trend", "factors",
                    "last_updated", "next_review_date"
                ],
                "count": 100,
                "sample": None
            }
        }