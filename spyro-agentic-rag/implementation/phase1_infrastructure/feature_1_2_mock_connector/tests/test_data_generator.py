"""Tests for DataGenerator"""

import pytest
from datetime import datetime
import json

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.data_generator import DataGenerator


class TestDataGenerator:
    """Test cases for DataGenerator"""
    
    def test_deterministic_generation_with_seed(self):
        """Test that same seed produces same data"""
        gen1 = DataGenerator(seed=42)
        gen2 = DataGenerator(seed=42)
        
        # Generate multiple items to verify determinism
        customers1 = [gen1.generate_customer(i) for i in range(5)]
        customers2 = [gen2.generate_customer(i) for i in range(5)]
        
        # Check key fields are the same (not all fields due to Faker variations)
        for c1, c2 in zip(customers1, customers2):
            assert c1["id"] == c2["id"]
            assert c1["size"] == c2["size"]
            assert c1["arr"] == c2["arr"]
            assert c1["health_score"] == c2["health_score"]
    
    def test_random_generation_without_seed(self):
        """Test that no seed produces different data"""
        gen1 = DataGenerator()
        gen2 = DataGenerator()
        
        # Generate multiple customers to ensure randomness
        customers1 = [gen1.generate_customer(i) for i in range(10)]
        customers2 = [gen2.generate_customer(i) for i in range(10)]
        
        # At least some should be different
        assert customers1 != customers2
    
    def test_generate_customer(self):
        """Test customer generation"""
        gen = DataGenerator(seed=42)
        customer = gen.generate_customer(1)
        
        # Check required fields
        assert "id" in customer
        assert customer["id"] == "cust_0001"
        assert "name" in customer
        assert "size" in customer
        assert customer["size"] in ["SMB", "Mid-Market", "Enterprise"]
        assert "industry" in customer
        assert "arr" in customer
        assert isinstance(customer["arr"], int)
        assert customer["arr"] > 0
        assert "health_score" in customer
        assert 40 <= customer["health_score"] <= 100
        assert "churn_risk" in customer
        assert customer["churn_risk"] in ["low", "medium", "high"]
        
        # Check dates are ISO format
        assert datetime.fromisoformat(customer["created_date"])
        assert datetime.fromisoformat(customer["updated_date"])
    
    def test_generate_product(self):
        """Test product generation"""
        gen = DataGenerator(seed=42)
        
        # First 3 products should be the predefined ones
        products = [gen.generate_product(i) for i in range(3)]
        
        assert products[0]["name"] == "SpyroCloud"
        assert products[1]["name"] == "SpyroAI"
        assert products[2]["name"] == "SpyroSecure"
        
        # Check product structure
        product = products[0]
        assert "id" in product
        assert "category" in product
        assert "description" in product
        assert "features" in product
        assert isinstance(product["features"], list)
        assert len(product["features"]) > 0
        assert "version" in product
        assert "status" in product
        assert product["status"] in ["active", "beta", "deprecated"]
    
    def test_generate_subscription(self):
        """Test subscription generation"""
        gen = DataGenerator(seed=42)
        
        # Need customers and products first
        gen.generate_customer(0)
        gen.generate_product(0)
        
        subscription = gen.generate_subscription(0)
        
        assert "id" in subscription
        assert subscription["id"] == "sub_0000"
        assert "customer_id" in subscription
        assert subscription["customer_id"].startswith("cust_")
        assert "product_id" in subscription
        assert subscription["product_id"].startswith("prod_")
        assert "mrr" in subscription
        assert "arr" in subscription
        assert subscription["arr"] == subscription["mrr"] * 12
        assert "status" in subscription
        assert subscription["status"] in ["active", "pending_renewal", "churned"]
        
    def test_generate_subscription_requires_dependencies(self):
        """Test that subscription generation fails without customers/products"""
        gen = DataGenerator()
        
        with pytest.raises(ValueError, match="Generate customers and products first"):
            gen.generate_subscription(0)
    
    def test_generate_team(self):
        """Test team generation"""
        gen = DataGenerator(seed=42)
        
        # Generate a product first for linking
        gen.generate_product(0)
        
        team = gen.generate_team(0)
        
        assert "id" in team
        assert "name" in team
        assert "size" in team
        assert 3 <= team["size"] <= 50
        assert "focus_area" in team
        assert "velocity" in team
        assert 50 <= team["velocity"] <= 100
        assert "utilization" in team
        assert 0.5 <= team["utilization"] <= 0.95
        assert "supported_products" in team
        assert isinstance(team["supported_products"], list)
    
    def test_generate_project(self):
        """Test project generation"""
        gen = DataGenerator(seed=42)
        
        # Need team first
        gen.generate_team(0)
        
        project = gen.generate_project(0)
        
        assert "id" in project
        assert "name" in project
        assert "type" in project
        assert project["type"] in ["feature", "infrastructure", "security", "performance", "migration"]
        assert "status" in project
        assert "team_id" in project
        assert project["team_id"].startswith("team_")
        assert "budget" in project
        assert project["budget"] > 0
        assert "priority" in project
        assert project["priority"] in ["low", "medium", "high", "critical"]
    
    def test_generate_risk(self):
        """Test risk generation"""
        gen = DataGenerator(seed=42)
        
        # Generate dependencies
        gen.generate_customer(0)
        gen.generate_team(0)
        
        risk = gen.generate_risk(0)
        
        assert "id" in risk
        assert "type" in risk
        assert risk["type"] in ["operational", "financial", "security", "compliance", "strategic", "reputational"]
        assert "severity" in risk
        assert risk["severity"] in ["low", "medium", "high", "critical"]
        assert "probability" in risk
        assert 0.1 <= risk["probability"] <= 0.9
        assert "impact" in risk
        assert 1 <= risk["impact"] <= 10
        assert "status" in risk
        
        # May have links to customer/team
        if "customer_id" in risk:
            assert risk["customer_id"].startswith("cust_")
        if "team_id" in risk:
            assert risk["team_id"].startswith("team_")
    
    def test_generate_event(self):
        """Test event generation"""
        gen = DataGenerator(seed=42)
        
        # Generate dependencies
        gen.generate_customer(0)
        gen.generate_team(0)
        
        event = gen.generate_event(0)
        
        assert "id" in event
        assert "type" in event
        assert "title" in event
        assert "date" in event
        assert datetime.fromisoformat(event["date"])
        assert "duration_hours" in event
        assert 0.5 <= event["duration_hours"] <= 8.0
        assert "status" in event
        assert event["status"] in ["scheduled", "in_progress", "completed", "cancelled"]
    
    def test_generate_customer_success_score(self):
        """Test customer success score generation"""
        gen = DataGenerator(seed=42)
        
        score = gen.generate_customer_success_score("cust_0001")
        
        assert "id" in score
        assert score["id"] == "css_cust_0001"
        assert "customer_id" in score
        assert score["customer_id"] == "cust_0001"
        assert "score" in score
        assert 40 <= score["score"] <= 100
        assert "trend" in score
        assert score["trend"] in ["improving", "stable", "declining"]
        assert "factors" in score
        assert "product_adoption" in score["factors"]
        assert "support_tickets" in score["factors"]
        assert "engagement_level" in score["factors"]
        assert score["factors"]["engagement_level"] in ["low", "medium", "high"]
    
    def test_get_schema(self):
        """Test schema generation"""
        gen = DataGenerator(seed=42)
        
        schema = gen.get_schema()
        
        # Check all entity types present
        expected_types = [
            "Customer", "Product", "SaaSSubscription", "Team",
            "Project", "Risk", "Event", "CustomerSuccessScore"
        ]
        
        for entity_type in expected_types:
            assert entity_type in schema
            assert "fields" in schema[entity_type]
            assert "count" in schema[entity_type]
            assert isinstance(schema[entity_type]["fields"], list)
            assert len(schema[entity_type]["fields"]) > 0
    
    def test_arr_based_on_customer_size(self):
        """Test that ARR is appropriate for customer size"""
        gen = DataGenerator(seed=42)
        
        # Generate multiple customers
        customers = [gen.generate_customer(i) for i in range(20)]
        
        # Check ARR ranges
        for customer in customers:
            if customer["size"] == "SMB":
                assert 10000 <= customer["arr"] <= 100000
            elif customer["size"] == "Mid-Market":
                assert 100000 <= customer["arr"] <= 1000000
            elif customer["size"] == "Enterprise":
                assert 1000000 <= customer["arr"] <= 10000000
    
    def test_data_relationships(self):
        """Test that generated data maintains relationships"""
        gen = DataGenerator(seed=42)
        
        # Generate related data
        gen.generate_customer(0)
        gen.generate_product(0)
        subscription = gen.generate_subscription(0)
        
        # Verify subscription links to existing customer and product
        assert subscription["customer_id"] in [c["id"] for c in gen.customers]
        assert subscription["product_id"] in [p["id"] for p in gen.products]