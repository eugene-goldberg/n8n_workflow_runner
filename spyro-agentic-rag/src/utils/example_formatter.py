"""Formatter for Cypher examples and instructions"""

def format_instructions(instructions: str) -> str:
    """Format instructions for the Text2Cypher retriever"""
    return f"""
You are an expert at generating Cypher queries for Neo4j.

{instructions}

User Query: {{query_text}}

Generate a Cypher query that answers the user's question based on the schema and examples provided.
Return only the Cypher query without any explanation.
"""

def format_examples(examples: list) -> str:
    """Format examples for the Text2Cypher retriever"""
    formatted = []
    for example in examples:
        formatted.append(f"""
Question: {example['question']}
Cypher:
```cypher
{example['cypher']}
```
""")
    return "\n".join(formatted)