"""Tests for contextual enricher"""

import pytest
import asyncio
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.contextual_enricher import ContextualEnricher
from src.models import Entity, EntityType


class TestContextualEnricher:
    """Test ContextualEnricher functionality"""
    
    @pytest.fixture
    def enricher(self):
        """Create enricher instance"""
        return ContextualEnricher()
    
    @pytest.mark.asyncio
    async def test_customer_industry_enrichment(self, enricher):
        """Test industry context enrichment for customers"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "TechCorp",
                "industry": "technology",
                "arr": 300000
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Should have industry context
        assert "industry_growth_rate" in enriched.attributes
        assert enriched.attributes["industry_growth_rate"] == 0.15
        assert enriched.attributes["industry_churn_risk"] == "medium"
        assert enriched.attributes["industry_avg_deal_size"] == 250000
        
        # Should calculate relative performance
        assert enriched.attributes["relative_deal_size"] == "above_average"
    
    @pytest.mark.asyncio
    async def test_customer_derived_fields(self, enricher):
        """Test derived field calculation for customers"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "BigCorp",
                "arr": 1500000,
                "churn_risk": "low",
                "support_tickets": 2,
                "engagement_score": 0.8,
                "payment_status": "current"
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Check CLV calculation
        assert "estimated_clv" in enriched.attributes
        assert enriched.attributes["estimated_clv"] > enriched.attributes["arr"]
        
        # Check tier calculation
        assert enriched.attributes["customer_tier"] == "enterprise"
        
        # Check health score
        assert "health_score" in enriched.attributes
        assert 0 <= enriched.attributes["health_score"] <= 1
    
    @pytest.mark.asyncio
    async def test_customer_categorization(self, enricher):
        """Test automatic categorization for customers"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "SmallBiz",
                "employee_count": 25,
                "country": "US"
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Size categorization
        assert enriched.attributes["size_category"] == "small"
        
        # Geographic categorization
        assert enriched.attributes["region"] == "north_america"
    
    @pytest.mark.asyncio
    async def test_subscription_enrichment(self, enricher):
        """Test subscription entity enrichment"""
        start_date = datetime.now() - timedelta(days=180)
        end_date = datetime.now() + timedelta(days=45)
        
        entity = Entity(
            type=EntityType.SUBSCRIPTION,
            attributes={
                "id": "sub_001",
                "value": 120000,  # Annual value
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Check MRR calculation
        assert enriched.attributes["mrr"] == 10000  # 120000 / 12
        
        # Check subscription age
        assert "subscription_age_days" in enriched.attributes
        assert enriched.attributes["subscription_age_days"] >= 180
        assert enriched.attributes["subscription_age_months"] >= 6
        
        # Check renewal risk
        assert enriched.attributes["days_to_renewal"] <= 45
        assert enriched.attributes["renewal_risk"] == "medium"
    
    @pytest.mark.asyncio
    async def test_risk_enrichment(self, enricher):
        """Test risk entity enrichment"""
        entity = Entity(
            type=EntityType.RISK,
            attributes={
                "title": "Customer churn risk",
                "severity": "high",
                "probability": 0.7,
                "identified_date": (datetime.now() - timedelta(days=45)).isoformat()
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Check risk score calculation
        assert "risk_score" in enriched.attributes
        assert enriched.attributes["risk_score"] == 0.75 * 0.7  # severity * probability
        
        # Check risk category
        assert enriched.attributes["risk_category"] == "high"
        
        # Check aging
        assert enriched.attributes["days_open"] >= 45
        assert enriched.attributes["is_overdue"] is True
    
    @pytest.mark.asyncio
    async def test_product_categorization(self, enricher):
        """Test product entity categorization"""
        entity = Entity(
            type=EntityType.PRODUCT,
            attributes={
                "name": "SpyroCloud Enterprise",
                "description": "Cloud-based SaaS solution"
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Delivery model based on name
        assert enriched.attributes["delivery_model"] == "saas"
        
        # Tier based on name
        assert enriched.attributes["product_tier"] == "premium"
    
    @pytest.mark.asyncio
    async def test_temporal_context(self, enricher):
        """Test temporal context enrichment"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "NewCustomer",
                "created_date": (datetime.now() - timedelta(days=30)).isoformat()
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Should have fiscal period context
        assert "current_quarter" in enriched.attributes
        assert enriched.attributes["current_quarter"] in ["Q1", "Q2", "Q3", "Q4"]
        assert "current_fiscal_year" in enriched.attributes
        
        # Should be marked as new customer (< 90 days)
        assert enriched.attributes["is_new_customer"] is True
        assert enriched.attributes["customer_age_days"] >= 30
    
    @pytest.mark.asyncio
    async def test_selective_enrichment(self, enricher):
        """Test selective enrichment with context flags"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "SelectiveCorp",
                "arr": 500000
            }
        )
        
        # Only enable derived fields
        context = {
            "enable_industry_context": False,
            "enable_derived_fields": True,
            "enable_categorization": False,
            "enable_temporal_context": False
        }
        
        enriched = await enricher.enrich_entity(entity, context, enable_all=False)
        
        # Should have derived fields
        assert "customer_tier" in enriched.attributes
        
        # Should not have industry context
        assert "industry_growth_rate" not in enriched.attributes
        
        # Should not have temporal context
        assert "current_quarter" not in enriched.attributes
    
    @pytest.mark.asyncio
    async def test_bulk_enrichment(self, enricher):
        """Test bulk entity enrichment"""
        entities = [
            Entity(
                type=EntityType.CUSTOMER,
                attributes={
                    "name": f"Customer{i}",
                    "arr": i * 100000
                }
            )
            for i in range(5)
        ]
        
        enriched_entities = await enricher.enrich_entities_bulk(
            entities,
            batch_size=2
        )
        
        assert len(enriched_entities) == 5
        
        # Check all were enriched
        for entity in enriched_entities:
            assert entity.metadata.get("enriched") is True
            assert "customer_tier" in entity.attributes
    
    @pytest.mark.asyncio
    async def test_enrichment_metadata(self, enricher):
        """Test enrichment metadata is added"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={"name": "MetaCorp"}
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Should have enrichment metadata
        assert enriched.metadata["enriched"] is True
        assert "enrichment_timestamp" in enriched.metadata
        
        # Timestamp should be recent
        enrichment_time = datetime.fromisoformat(
            enriched.metadata["enrichment_timestamp"]
        )
        assert (datetime.now() - enrichment_time).seconds < 5
    
    @pytest.mark.asyncio
    async def test_edge_cases(self, enricher):
        """Test edge cases in enrichment"""
        # Entity with minimal attributes
        entity1 = Entity(
            type=EntityType.CUSTOMER,
            attributes={"name": "MinimalCorp"}
        )
        
        enriched1 = await enricher.enrich_entity(entity1)
        assert enriched1 is not None
        assert enriched1.attributes["name"] == "MinimalCorp"
        
        # Entity with zero/null values
        entity2 = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "ZeroCorp",
                "arr": 0,
                "employee_count": 0
            }
        )
        
        enriched2 = await enricher.enrich_entity(entity2)
        assert enriched2.attributes["customer_tier"] == "smb"
        
        # Risk with zero probability
        entity3 = Entity(
            type=EntityType.RISK,
            attributes={
                "title": "Low risk",
                "severity": "high",
                "probability": 0
            }
        )
        
        enriched3 = await enricher.enrich_entity(entity3)
        assert enriched3.attributes["risk_score"] == 0
        assert enriched3.attributes["risk_category"] == "low"
    
    @pytest.mark.asyncio
    async def test_unknown_industry_handling(self, enricher):
        """Test handling of unknown industries"""
        entity = Entity(
            type=EntityType.CUSTOMER,
            attributes={
                "name": "UnknownIndustryCorp",
                "industry": "space_mining",  # Not in predefined industries
                "arr": 1000000
            }
        )
        
        enriched = await enricher.enrich_entity(entity)
        
        # Should not crash, but won't have industry benchmarks
        assert "industry_growth_rate" not in enriched.attributes
        assert "relative_deal_size" not in enriched.attributes
        
        # Should still have other enrichments
        assert enriched.attributes["customer_tier"] == "enterprise"