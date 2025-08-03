"""
Enhanced Cypher Examples v4 - Includes relationship model and better filtering
Combines v3 examples with fixes for failing queries
"""

# Import the base examples
from .cypher_examples_enhanced_v3 import ENHANCED_CYPHER_EXAMPLES as V3_EXAMPLES
from .cypher_examples_relationship_fixes import RELATIONSHIP_MODEL_EXAMPLES
from .cypher_examples_risk_queries import RISK_FILTERING_EXAMPLES
from .cypher_examples_data_quality import DATA_QUALITY_EXAMPLES

# Combine all examples, with new ones taking precedence
ENHANCED_CYPHER_EXAMPLES = (
    RELATIONSHIP_MODEL_EXAMPLES +  # Fixes for Q7, Q52, Q53
    RISK_FILTERING_EXAMPLES +      # Fixes for Q4, Q29, Q45, Q48
    DATA_QUALITY_EXAMPLES +        # Fixes for Q54, Q50, Q60, Q31
    V3_EXAMPLES                    # Keep existing working examples
)

# Same instructions as v3
CYPHER_GENERATION_INSTRUCTIONS = """
When generating Cypher queries:
1. ALL entities use the '__Entity__' label for LlamaIndex compatibility
2. Check for specific entity types using: '__Entity__' IN labels(n) AND 'TYPE' IN labels(n)
3. String values often need parsing (e.g., '$8M' → 8000000)
4. Use 'active' for risk status, not 'Unmitigated'
5. Success scores are in HAS_SUCCESS_SCORE relationships
6. For relationship model entities (PROJECTION, MARKETING_CHANNEL, REVENUE), traverse relationships to find data
7. Always filter to avoid returning all entities when looking for "at risk" or specific conditions
"""