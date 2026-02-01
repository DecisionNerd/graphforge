"""Knowledge Graph with GraphForge

This example demonstrates building a knowledge base with entities and relationships.

Use Case: Store facts about concepts and query relationships between them
"""

from graphforge import GraphForge


def main():
    # Create persistent graph
    db = GraphForge("knowledge-graph.db")

    print("Building knowledge graph...")

    try:
        db.begin()

        # Create concepts
        concepts = [
            ("Python", "Programming Language", 1991),
            ("Graph Database", "Technology", 2000),
            ("Machine Learning", "Field", 1959),
            ("Neural Networks", "Technique", 1943),
            ("Data Science", "Field", 2008),
            ("SQL", "Programming Language", 1974),
        ]

        for name, category, year in concepts:
            db.execute(f"""
                CREATE (:Concept {{
                    name: '{name}',
                    category: '{category}',
                    established: {year}
                }})
            """)

        # Create relationships
        relationships = [
            ("Python", "used_in", "Data Science"),
            ("Python", "used_in", "Machine Learning"),
            ("Machine Learning", "uses", "Neural Networks"),
            ("Data Science", "uses", "Machine Learning"),
            ("Graph Database", "different_from", "SQL"),
            ("Neural Networks", "inspired_by", "Data Science"),
        ]

        for src, rel, dst in relationships:
            db.execute(f"""
                MATCH (a:Concept {{name: '{src}'}}), (b:Concept {{name: '{dst}'}})
                CREATE (a)-[:{rel.upper()}]->(b)
            """)

        db.commit()
        print(f"Created {len(concepts)} concepts and {len(relationships)} relationships\n")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        return

    # Query 1: Find all technologies
    print("=" * 60)
    print("QUERY 1: All Technologies")
    print("=" * 60)

    results = db.execute("""
        MATCH (c:Concept)
        WHERE c.category = 'Technology'
        RETURN c.name AS name, c.established AS year
        ORDER BY year
    """)

    for row in results:
        print(f"  {row['name'].value} (est. {row['year'].value})")

    # Query 2: What is Python used in?
    print("\n" + "=" * 60)
    print("QUERY 2: What is Python Used In?")
    print("=" * 60)

    results = db.execute("""
        MATCH (python:Concept {name: 'Python'})-[r:USED_IN]->(field)
        RETURN field.name AS field
    """)

    for row in results:
        print(f"  → {row['field'].value}")

    # Query 3: Find all outgoing relationships for a concept
    print("\n" + "=" * 60)
    print("QUERY 3: Machine Learning Relationships")
    print("=" * 60)

    results = db.execute("""
        MATCH (ml:Concept {name: 'Machine Learning'})-[r]->(target)
        RETURN type(r) AS relationship, target.name AS target
    """)

    # Note: type(r) is not yet supported, so we'll work around it
    # For now, just show targets
    results = db.execute("""
        MATCH (ml:Concept {name: 'Machine Learning'})-[r]->(target)
        RETURN target.name AS related_to
    """)

    for row in results:
        print(f"  → {row['related_to'].value}")

    # Query 4: Technologies by age
    print("\n" + "=" * 60)
    print("QUERY 4: Concepts by Age")
    print("=" * 60)

    results = db.execute("""
        MATCH (c:Concept)
        RETURN c.name AS name, c.established AS year
        ORDER BY year
        LIMIT 5
    """)

    for row in results:
        print(f"  {row['year'].value}: {row['name'].value}")

    # Query 5: Find programming languages
    print("\n" + "=" * 60)
    print("QUERY 5: Programming Languages")
    print("=" * 60)

    results = db.execute("""
        MATCH (c:Concept)
        WHERE c.category = 'Programming Language'
        RETURN c.name AS language, c.established AS year
        ORDER BY year
    """)

    for row in results:
        print(f"  {row['language'].value} (since {row['year'].value})")

    # Query 6: Two-hop connections
    print("\n" + "=" * 60)
    print("QUERY 6: What Uses Neural Networks? (Two Hops)")
    print("=" * 60)

    results = db.execute("""
        MATCH (source)-[]->(intermediate)-[:USES]->(nn:Concept {name: 'Neural Networks'})
        RETURN DISTINCT source.name AS source
    """)

    for row in results:
        print(f"  {row['source'].value} (indirectly)")

    # Query 7: Count relationships by type
    print("\n" + "=" * 60)
    print("QUERY 7: Concept Statistics")
    print("=" * 60)

    results = db.execute("""
        MATCH (c:Concept)
        RETURN c.category AS category, count(*) AS count
        ORDER BY count DESC
    """)

    for row in results:
        print(f"  {row['category'].value}: {row['count'].value} concepts")

    print("\n" + "=" * 60)
    print("Analysis Complete!")
    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
