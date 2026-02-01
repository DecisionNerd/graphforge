"""Migrating from NetworkX to GraphForge

This example demonstrates how to convert NetworkX graphs to GraphForge
and the key differences between the two libraries.

NetworkX: General-purpose graph algorithms
GraphForge: openCypher queries + persistence
"""

import sys

try:
    import networkx as nx
except ImportError:
    print("NetworkX not installed. Install with: pip install networkx")
    sys.exit(1)

from graphforge import GraphForge


def networkx_example():
    """Build a graph using NetworkX"""
    print("=" * 60)
    print("PART 1: NetworkX Example")
    print("=" * 60)

    # Create graph
    G = nx.Graph()

    # Add nodes with attributes
    G.add_node("Alice", age=30, city="NYC")
    G.add_node("Bob", age=25, city="NYC")
    G.add_node("Charlie", age=35, city="LA")

    # Add edges with attributes
    G.add_edge("Alice", "Bob", weight=0.9, since=2015)
    G.add_edge("Bob", "Charlie", weight=0.7, since=2018)

    # Query using NetworkX methods
    print(f"Nodes: {G.number_of_nodes()}")
    print(f"Edges: {G.number_of_edges()}")
    print(f"Alice's neighbors: {list(G.neighbors('Alice'))}")

    # Attributes
    print(f"Alice's age: {G.nodes['Alice']['age']}")
    print(f"Alice-Bob weight: {G['Alice']['Bob']['weight']}")

    return G


def graphforge_example():
    """Build the same graph using GraphForge"""
    print("\n" + "=" * 60)
    print("PART 2: GraphForge Example")
    print("=" * 60)

    # Create graph
    db = GraphForge()

    # Add nodes with properties (labels optional but recommended)
    db.execute("CREATE (:Person {name: 'Alice', age: 30, city: 'NYC'})")
    db.execute("CREATE (:Person {name: 'Bob', age: 25, city: 'NYC'})")
    db.execute("CREATE (:Person {name: 'Charlie', age: 35, city: 'LA'})")

    # Add relationships with properties
    db.execute("""
        MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
        CREATE (a)-[:KNOWS {weight: 0.9, since: 2015}]->(b)
    """)
    db.execute("""
        MATCH (a:Person {name: 'Bob'}), (b:Person {name: 'Charlie'})
        CREATE (a)-[:KNOWS {weight: 0.7, since: 2018}]->(b)
    """)

    # Query using Cypher
    results = db.execute("MATCH (n) RETURN count(*) AS count")
    print(f"Nodes: {results[0]['count'].value}")

    results = db.execute("MATCH ()-[r]->() RETURN count(*) AS count")
    print(f"Edges: {results[0]['count'].value}")

    # Find neighbors
    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(neighbor)
        RETURN neighbor.name AS name
    """)
    neighbors = [row["name"].value for row in results]
    print(f"Alice's neighbors: {neighbors}")

    # Access properties
    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})
        RETURN alice.age AS age
    """)
    print(f"Alice's age: {results[0]['age'].value}")

    results = db.execute("""
        MATCH (alice:Person {name: 'Alice'})-[r:KNOWS]->(bob:Person {name: 'Bob'})
        RETURN r.weight AS weight
    """)
    print(f"Alice-Bob weight: {results[0]['weight'].value}")

    return db


def migration_patterns():
    """Show migration patterns side-by-side"""
    print("\n" + "=" * 60)
    print("PART 3: Migration Patterns")
    print("=" * 60)

    print("\n1. CREATE NODES")
    print("-" * 60)
    print("NetworkX:")
    print("  G.add_node('Alice', age=30)")
    print("\nGraphForge (Python API):")
    print("  db.create_node(['Person'], name='Alice', age=30)")
    print("\nGraphForge (Cypher):")
    print("  db.execute(\"CREATE (:Person {name: 'Alice', age: 30})\")")

    print("\n2. CREATE EDGES")
    print("-" * 60)
    print("NetworkX:")
    print("  G.add_edge('Alice', 'Bob', weight=0.9)")
    print("\nGraphForge (Python API):")
    print("  db.create_relationship(alice, bob, 'KNOWS', weight=0.9)")
    print("\nGraphForge (Cypher):")
    print('  db.execute("""')
    print("    MATCH (a {name: 'Alice'}), (b {name: 'Bob'})")
    print("    CREATE (a)-[:KNOWS {weight: 0.9}]->(b)")
    print('  """)')

    print("\n3. FIND NEIGHBORS")
    print("-" * 60)
    print("NetworkX:")
    print("  neighbors = list(G.neighbors('Alice'))")
    print("\nGraphForge:")
    print('  results = db.execute("""')
    print("    MATCH (alice:Person {name: 'Alice'})-[:KNOWS]->(neighbor)")
    print("    RETURN neighbor.name AS name")
    print('  """)')

    print("\n4. GET NODE ATTRIBUTES")
    print("-" * 60)
    print("NetworkX:")
    print("  age = G.nodes['Alice']['age']")
    print("\nGraphForge:")
    print('  results = db.execute("""')
    print("    MATCH (alice:Person {name: 'Alice'})")
    print("    RETURN alice.age AS age")
    print('  """)')
    print("  age = results[0]['age'].value")

    print("\n5. FILTER NODES")
    print("-" * 60)
    print("NetworkX:")
    print("  young = [n for n, data in G.nodes(data=True)")
    print("           if data.get('age', 0) < 30]")
    print("\nGraphForge:")
    print('  results = db.execute("""')
    print("    MATCH (p:Person)")
    print("    WHERE p.age < 30")
    print("    RETURN p.name AS name")
    print('  """)')

    print("\n6. DEGREE CENTRALITY")
    print("-" * 60)
    print("NetworkX:")
    print("  centrality = nx.degree_centrality(G)")
    print("\nGraphForge:")
    print('  results = db.execute("""')
    print("    MATCH (p:Person)-[:KNOWS]-(neighbor)")
    print("    RETURN p.name AS name, count(neighbor) AS degree")
    print("    ORDER BY degree DESC")
    print('  """)')


def key_differences():
    """Highlight key differences"""
    print("\n" + "=" * 60)
    print("PART 4: Key Differences")
    print("=" * 60)

    print("\n✅ GraphForge Advantages:")
    print("  • Declarative queries (Cypher)")
    print("  • Persistence to SQLite")
    print("  • ACID transactions")
    print("  • Standard query language (openCypher)")
    print("  • Type-safe property values")
    print("  • Multi-label nodes")

    print("\n✅ NetworkX Advantages:")
    print("  • Rich algorithm library (pagerank, shortest paths, etc.)")
    print("  • Visualization support (matplotlib)")
    print("  • Mature ecosystem")
    print("  • Scientific computing focus")
    print("  • NumPy/SciPy integration")

    print("\n💡 When to Choose GraphForge:")
    print("  • You need persistence")
    print("  • You want SQL-like queries")
    print("  • You need transactions")
    print("  • You prefer declarative queries over procedural code")
    print("  • You're building a production data system")

    print("\n💡 When to Choose NetworkX:")
    print("  • You need advanced graph algorithms")
    print("  • You're doing research/prototyping")
    print("  • You need visualization")
    print("  • You're analyzing in-memory graphs")
    print("  • You need NumPy/SciPy integration")


def interoperability():
    """Show how to convert between NetworkX and GraphForge"""
    print("\n" + "=" * 60)
    print("PART 5: Interoperability (Future Feature)")
    print("=" * 60)

    print("\nPlanned feature - converting NetworkX graph to GraphForge:")
    print("""
    import networkx as nx
    from graphforge import GraphForge

    # Build NetworkX graph
    G = nx.karate_club_graph()

    # Convert to GraphForge (future API)
    db = GraphForge()
    # db.import_networkx(G)  # Not yet implemented

    # For now, manual conversion:
    for node, data in G.nodes(data=True):
        props = {k: v for k, v in data.items()}
        db.create_node(['Node'], id=node, **props)

    for u, v, data in G.edges(data=True):
        # Match nodes and create relationship
        db.execute(f'''
            MATCH (a:Node {{id: {u}}}), (b:Node {{id: {v}}})
            CREATE (a)-[:CONNECTED]->(b)
        ''')
    """)


def main():
    # Run examples
    nx_graph = networkx_example()
    gf_graph = graphforge_example()

    # Show migration patterns
    migration_patterns()

    # Highlight differences
    key_differences()

    # Show interoperability
    interoperability()

    print("\n" + "=" * 60)
    print("Migration Guide Complete!")
    print("=" * 60)
    print("\nFor more information:")
    print("  • NetworkX: https://networkx.org/")
    print("  • GraphForge: See docs/tutorial.md")


if __name__ == "__main__":
    main()
