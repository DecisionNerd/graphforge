"""Basic usage example for GraphForge.

This demonstrates creating and querying a simple graph using
the in-memory storage backend.
"""

from graphforge.storage.memory import Graph
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherString

# Create an empty graph
graph = Graph()

# Create some nodes
alice = NodeRef(
    id=1,
    labels=frozenset(["Person"]),
    properties={
        "name": CypherString("Alice"),
        "age": CypherInt(30),
    },
)

bob = NodeRef(
    id=2,
    labels=frozenset(["Person"]),
    properties={
        "name": CypherString("Bob"),
        "age": CypherInt(35),
    },
)

company = NodeRef(
    id=3,
    labels=frozenset(["Company"]),
    properties={
        "name": CypherString("TechCorp"),
    },
)

# Add nodes to the graph
graph.add_node(alice)
graph.add_node(bob)
graph.add_node(company)

print(f"Graph has {graph.node_count()} nodes")

# Create relationships
knows = EdgeRef(
    id=10,
    type="KNOWS",
    src=alice,
    dst=bob,
    properties={"since": CypherInt(2015)},
)

works_at_alice = EdgeRef(
    id=11,
    type="WORKS_AT",
    src=alice,
    dst=company,
    properties={},
)

works_at_bob = EdgeRef(
    id=12,
    type="WORKS_AT",
    src=bob,
    dst=company,
    properties={},
)

# Add edges to the graph
graph.add_edge(knows)
graph.add_edge(works_at_alice)
graph.add_edge(works_at_bob)

print(f"Graph has {graph.edge_count()} edges")

# Query the graph
print("\n--- Query: All Person nodes ---")
persons = graph.get_nodes_by_label("Person")
for person in persons:
    name = person.properties["name"].value
    age = person.properties["age"].value
    print(f"  {name}, age {age}")

print("\n--- Query: Who does Alice know? ---")
alice_knows = graph.get_outgoing_edges(1)
for edge in alice_knows:
    if edge.type == "KNOWS":
        person = graph.get_node(edge.dst.id)
        print(f"  {person.properties['name'].value}")

print("\n--- Query: Who works at TechCorp? ---")
company_employees = graph.get_incoming_edges(3)
for edge in company_employees:
    if edge.type == "WORKS_AT":
        person = graph.get_node(edge.src.id)
        print(f"  {person.properties['name'].value}")

print("\n--- Query: All WORKS_AT relationships ---")
works_at_edges = graph.get_edges_by_type("WORKS_AT")
print(f"  Found {len(works_at_edges)} WORKS_AT relationships")
