"""Contextual enrichment for entities"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass

from .models import Entity, EntityType, EnrichmentRule

logger = logging.getLogger(__name__)


class ContextualEnricher:
    """Enriches entities with contextual and derived data"""
    
    def __init__(self):
        """Initialize enricher with default rules"""
        self.enrichment_rules = self._load_default_rules()
        self.industry_context = self._load_industry_context()
        self._enrichment_cache = {}
    
    async def enrich_entity(
        self,
        entity: Entity,
        context: Optional[Dict[str, Any]] = None,
        enable_all: bool = True
    ) -> Entity:
        """Enrich entity with contextual data
        
        Args:
            entity: Entity to enrich
            context: Additional context for enrichment
            enable_all: Whether to apply all enrichment types
            
        Returns:
            Enriched entity
        """
        # Create a copy to avoid modifying original
        enriched = Entity(
            id=entity.id,
            type=entity.type,
            source_id=entity.source_id,
            source_system=entity.source_system,
            attributes=entity.attributes.copy(),
            metadata=entity.metadata.copy(),
            confidence=entity.confidence,
            source_ids=entity.source_ids.copy(),
            merged_from=entity.merged_from.copy()
        )
        
        # Add enrichment metadata
        enriched.metadata["enriched"] = True
        enriched.metadata["enrichment_timestamp"] = datetime.now().isoformat()
        
        # Apply enrichment rules
        if enable_all or context.get("enable_industry_context", True):
            enriched = await self._add_industry_context(enriched, context)
        
        if enable_all or context.get("enable_derived_fields", True):
            enriched = await self._calculate_derived_fields(enriched, context)
        
        if enable_all or context.get("enable_categorization", True):
            enriched = await self._add_categorization(enriched, context)
        
        if enable_all or context.get("enable_temporal_context", True):
            enriched = await self._add_temporal_context(enriched, context)
        
        return enriched
    
    async def enrich_entities_bulk(
        self,
        entities: List[Entity],
        context: Optional[Dict[str, Any]] = None,
        batch_size: int = 100
    ) -> List[Entity]:
        """Enrich multiple entities"""
        enriched_entities = []
        
        # Process in batches
        for i in range(0, len(entities), batch_size):
            batch = entities[i:i + batch_size]
            
            # Enrich batch concurrently
            import asyncio
            tasks = [
                self.enrich_entity(entity, context)
                for entity in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Entity):
                    enriched_entities.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"Enrichment error: {result}")
        
        return enriched_entities
    
    async def _add_industry_context(
        self,
        entity: Entity,
        context: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """Add industry-specific context"""
        if entity.type != EntityType.CUSTOMER:
            return entity
        
        # Get industry from attributes or context
        industry = (
            entity.attributes.get("industry") or
            (context or {}).get("industry")
        )
        
        if industry and industry in self.industry_context:
            industry_data = self.industry_context[industry]
            
            # Add industry benchmarks
            entity.attributes["industry_growth_rate"] = industry_data["growth_rate"]
            entity.attributes["industry_churn_risk"] = industry_data["churn_risk"]
            entity.attributes["industry_avg_deal_size"] = industry_data["avg_deal_size"]
            
            # Calculate relative performance
            if "arr" in entity.attributes:
                arr = entity.attributes["arr"]
                avg_deal = industry_data["avg_deal_size"]
                entity.attributes["relative_deal_size"] = (
                    "above_average" if arr > avg_deal else "below_average"
                )
        
        return entity
    
    async def _calculate_derived_fields(
        self,
        entity: Entity,
        context: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """Calculate derived fields based on existing attributes"""
        
        if entity.type == EntityType.CUSTOMER:
            # Customer lifetime value estimation
            if "arr" in entity.attributes and "churn_risk" in entity.attributes:
                arr = entity.attributes["arr"]
                churn_risk = entity.attributes["churn_risk"]
                
                # Simple CLV calculation
                retention_rate = {
                    "low": 0.9,
                    "medium": 0.7,
                    "high": 0.5
                }.get(churn_risk, 0.7)
                
                entity.attributes["estimated_clv"] = arr * (1 / (1 - retention_rate))
            
            # Customer tier calculation
            if "arr" in entity.attributes:
                arr = entity.attributes["arr"]
                if arr >= 1000000:
                    entity.attributes["customer_tier"] = "enterprise"
                elif arr >= 100000:
                    entity.attributes["customer_tier"] = "mid_market"
                else:
                    entity.attributes["customer_tier"] = "smb"
            
            # Health score calculation
            health_factors = []
            
            if entity.attributes.get("support_tickets", 0) < 5:
                health_factors.append(0.3)
            if entity.attributes.get("engagement_score", 0) > 0.7:
                health_factors.append(0.3)
            if entity.attributes.get("payment_status") == "current":
                health_factors.append(0.4)
            
            if health_factors:
                entity.attributes["health_score"] = sum(health_factors)
        
        elif entity.type == EntityType.SUBSCRIPTION:
            # Subscription metrics
            if "start_date" in entity.attributes and "value" in entity.attributes:
                start_date = datetime.fromisoformat(
                    entity.attributes["start_date"].replace('Z', '+00:00')
                )
                
                # Calculate MRR
                entity.attributes["mrr"] = entity.attributes["value"] / 12
                
                # Calculate subscription age
                age_days = (datetime.now() - start_date).days
                entity.attributes["subscription_age_days"] = age_days
                entity.attributes["subscription_age_months"] = age_days // 30
            
            # Renewal risk
            if "end_date" in entity.attributes:
                end_date = datetime.fromisoformat(
                    entity.attributes["end_date"].replace('Z', '+00:00')
                )
                days_to_renewal = (end_date - datetime.now()).days
                
                entity.attributes["days_to_renewal"] = days_to_renewal
                
                if days_to_renewal < 30:
                    entity.attributes["renewal_risk"] = "high"
                elif days_to_renewal < 90:
                    entity.attributes["renewal_risk"] = "medium"
                else:
                    entity.attributes["renewal_risk"] = "low"
        
        elif entity.type == EntityType.RISK:
            # Risk scoring
            severity = entity.attributes.get("severity", "medium")
            probability = entity.attributes.get("probability", 0.5)
            
            severity_scores = {
                "low": 0.25,
                "medium": 0.5,
                "high": 0.75,
                "critical": 1.0
            }
            
            risk_score = severity_scores.get(severity, 0.5) * probability
            entity.attributes["risk_score"] = risk_score
            
            # Risk category
            if risk_score >= 0.75:
                entity.attributes["risk_category"] = "critical"
            elif risk_score >= 0.5:
                entity.attributes["risk_category"] = "high"
            elif risk_score >= 0.25:
                entity.attributes["risk_category"] = "medium"
            else:
                entity.attributes["risk_category"] = "low"
        
        return entity
    
    async def _add_categorization(
        self,
        entity: Entity,
        context: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """Add automatic categorization"""
        
        if entity.type == EntityType.CUSTOMER:
            # Size categorization
            if "employee_count" in entity.attributes:
                employees = entity.attributes["employee_count"]
                if employees <= 50:
                    entity.attributes["size_category"] = "small"
                elif employees <= 500:
                    entity.attributes["size_category"] = "medium"
                elif employees <= 5000:
                    entity.attributes["size_category"] = "large"
                else:
                    entity.attributes["size_category"] = "enterprise"
            
            # Geographic categorization
            if "country" in entity.attributes:
                country = entity.attributes["country"]
                # Simple region mapping
                regions = {
                    "US": "north_america",
                    "CA": "north_america",
                    "MX": "north_america",
                    "GB": "europe",
                    "DE": "europe",
                    "FR": "europe",
                    "JP": "asia_pacific",
                    "AU": "asia_pacific",
                    "CN": "asia_pacific"
                }
                entity.attributes["region"] = regions.get(country, "other")
        
        elif entity.type == EntityType.PRODUCT:
            # Product categorization based on name
            name = entity.attributes.get("name", "").lower()
            
            if "cloud" in name or "saas" in name:
                entity.attributes["delivery_model"] = "saas"
            elif "enterprise" in name:
                entity.attributes["delivery_model"] = "on_premise"
            else:
                entity.attributes["delivery_model"] = "hybrid"
            
            # Tier based on name patterns
            if "enterprise" in name or "pro" in name:
                entity.attributes["product_tier"] = "premium"
            elif "basic" in name or "starter" in name:
                entity.attributes["product_tier"] = "basic"
            else:
                entity.attributes["product_tier"] = "standard"
        
        return entity
    
    async def _add_temporal_context(
        self,
        entity: Entity,
        context: Optional[Dict[str, Any]] = None
    ) -> Entity:
        """Add temporal context and time-based calculations"""
        current_time = datetime.now()
        
        # Add fiscal period context
        current_quarter = (current_time.month - 1) // 3 + 1
        entity.attributes["current_quarter"] = f"Q{current_quarter}"
        entity.attributes["current_fiscal_year"] = current_time.year
        
        # Time-based flags
        if entity.type == EntityType.CUSTOMER:
            # New customer flag
            if "created_date" in entity.attributes:
                created = datetime.fromisoformat(
                    entity.attributes["created_date"].replace('Z', '+00:00')
                )
                days_since_creation = (current_time - created).days
                entity.attributes["is_new_customer"] = days_since_creation <= 90
                entity.attributes["customer_age_days"] = days_since_creation
        
        elif entity.type == EntityType.RISK:
            # Risk aging
            if "identified_date" in entity.attributes:
                identified = datetime.fromisoformat(
                    entity.attributes["identified_date"].replace('Z', '+00:00')
                )
                days_open = (current_time - identified).days
                entity.attributes["days_open"] = days_open
                entity.attributes["is_overdue"] = days_open > 30
        
        return entity
    
    def _load_default_rules(self) -> List[EnrichmentRule]:
        """Load default enrichment rules"""
        return [
            EnrichmentRule(
                entity_type=EntityType.CUSTOMER,
                field_name="estimated_clv",
                rule_type="derived",
                configuration={
                    "required_fields": ["arr", "churn_risk"],
                    "formula": "arr * (1 / (1 - retention_rate))"
                }
            ),
            EnrichmentRule(
                entity_type=EntityType.CUSTOMER,
                field_name="customer_tier",
                rule_type="conditional",
                configuration={
                    "conditions": [
                        {"if": "arr >= 1000000", "then": "enterprise"},
                        {"if": "arr >= 100000", "then": "mid_market"},
                        {"else": "smb"}
                    ]
                }
            )
        ]
    
    def _load_industry_context(self) -> Dict[str, Dict[str, Any]]:
        """Load industry context data"""
        return {
            "technology": {
                "growth_rate": 0.15,
                "churn_risk": "medium",
                "avg_deal_size": 250000,
                "typical_contract_length": 12
            },
            "finance": {
                "growth_rate": 0.08,
                "churn_risk": "low",
                "avg_deal_size": 500000,
                "typical_contract_length": 36
            },
            "healthcare": {
                "growth_rate": 0.12,
                "churn_risk": "low",
                "avg_deal_size": 350000,
                "typical_contract_length": 24
            },
            "retail": {
                "growth_rate": 0.05,
                "churn_risk": "high",
                "avg_deal_size": 100000,
                "typical_contract_length": 12
            },
            "manufacturing": {
                "growth_rate": 0.06,
                "churn_risk": "medium",
                "avg_deal_size": 300000,
                "typical_contract_length": 24
            }
        }