#!/usr/bin/env python3
"""Extract complete schema from Neo4j database"""

import json
from collections import defaultdict
from neo4j import GraphDatabase
from src.utils.config import Config

def extract_schema():
    config = Config.from_env()
    driver = GraphDatabase.driver(config.neo4j_uri, auth=(config.neo4j_username, config.neo4j_password))
    
    schema = {
        "entities": {},
        "relationships": {},
        "statistics": {}
    }
    
    with driver.session() as session:
        # Get all node labels and counts
        print("Extracting entity types...")
        result = session.run("""
            CALL db.labels() YIELD label
            CALL {
                WITH label
                MATCH (n) WHERE label IN labels(n)
                RETURN count(n) as count
            }
            RETURN label, count
            ORDER BY label
        """)
        
        for record in result:
            label = record["label"]
            count = record["count"]
            schema["entities"][label] = {
                "count": count,
                "properties": {},
                "sample_values": {}
            }
        
        # Get properties for each entity type
        print("Extracting entity properties...")
        for label in schema["entities"]:
            # Get all properties for this label
            result = session.run(f"""
                MATCH (n:{label})
                WITH n LIMIT 100
                UNWIND keys(n) as key
                WITH key, collect(n[key])[..5] as sample_values
                RETURN key, sample_values
                ORDER BY key
            """)
            
            properties = {}
            sample_values = {}
            for record in result:
                key = record["key"]
                samples = [str(v) for v in record["sample_values"] if v is not None]
                properties[key] = {
                    "samples": samples[:3]  # Keep first 3 samples
                }
                sample_values[key] = samples[:3]
            
            schema["entities"][label]["properties"] = properties
            schema["entities"][label]["sample_values"] = sample_values
        
        # Get all relationship types
        print("Extracting relationship types...")
        result = session.run("""
            CALL db.relationshipTypes() YIELD relationshipType
            RETURN relationshipType
        """)
        
        rel_types = [record["relationshipType"] for record in result]
        
        # Get relationship patterns
        for rel_type in rel_types:
            result = session.run(f"""
                MATCH (a)-[r:{rel_type}]->(b)
                WITH labels(a) as from_labels, labels(b) as to_labels, count(r) as count
                RETURN from_labels, to_labels, count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            patterns = []
            total_count = 0
            for record in result:
                from_labels = [l for l in record["from_labels"] if not l.startswith("__")]
                to_labels = [l for l in record["to_labels"] if not l.startswith("__")]
                if from_labels and to_labels:
                    patterns.append({
                        "from": from_labels[0] if from_labels else "Unknown",
                        "to": to_labels[0] if to_labels else "Unknown",
                        "count": record["count"]
                    })
                    total_count += record["count"]
            
            schema["relationships"][rel_type] = {
                "patterns": patterns,
                "total_count": total_count
            }
        
        # Get statistics
        result = session.run("MATCH (n) RETURN count(n) as node_count")
        schema["statistics"]["total_nodes"] = result.single()["node_count"]
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as rel_count")
        schema["statistics"]["total_relationships"] = result.single()["rel_count"]
        
        schema["statistics"]["entity_types"] = len(schema["entities"])
        schema["statistics"]["relationship_types"] = len(schema["relationships"])
    
    driver.close()
    return schema

def main():
    print("Extracting Neo4j schema...")
    schema = extract_schema()
    
    # Save to JSON file
    with open("neo4j_schema_complete.json", "w") as f:
        json.dump(schema, f, indent=2)
    
    # Create human-readable documentation
    with open("NEO4J_SCHEMA_DOCUMENTATION.md", "w") as f:
        f.write("# Neo4j Schema Documentation\n\n")
        f.write("## Overview\n")
        f.write(f"- Total Nodes: {schema['statistics']['total_nodes']:,}\n")
        f.write(f"- Total Relationships: {schema['statistics']['total_relationships']:,}\n")
        f.write(f"- Entity Types: {schema['statistics']['entity_types']}\n")
        f.write(f"- Relationship Types: {schema['statistics']['relationship_types']}\n\n")
        
        f.write("## Entity Types\n\n")
        for label, info in sorted(schema["entities"].items()):
            if label.startswith("__"):
                continue
            f.write(f"### {label} ({info['count']} nodes)\n")
            if info['properties']:
                f.write("**Properties:**\n")
                for prop, prop_info in sorted(info['properties'].items()):
                    samples = prop_info['samples']
                    if samples:
                        f.write(f"- `{prop}`: {', '.join(samples[:2])}\n")
                    else:
                        f.write(f"- `{prop}`\n")
            f.write("\n")
        
        f.write("## Relationship Types\n\n")
        for rel_type, info in sorted(schema["relationships"].items()):
            f.write(f"### {rel_type} ({info['total_count']} relationships)\n")
            if info['patterns']:
                f.write("**Patterns:**\n")
                for pattern in info['patterns'][:5]:  # Show top 5 patterns
                    f.write(f"- ({pattern['from']})-[:{rel_type}]->({pattern['to']}) - {pattern['count']} instances\n")
            f.write("\n")
    
    print("Schema extraction complete!")
    print("- JSON schema saved to: neo4j_schema_complete.json")
    print("- Documentation saved to: NEO4J_SCHEMA_DOCUMENTATION.md")

if __name__ == "__main__":
    main()