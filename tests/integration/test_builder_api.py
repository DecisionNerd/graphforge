"""Integration tests for the Python builder API.

Tests the user-facing API for creating nodes and relationships without
using internal NodeRef/EdgeRef classes directly.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherList,
    CypherMap,
    CypherNull,
    CypherString,
)


class TestCreateNode:
    """Tests for create_node() method."""

    def test_create_node_with_single_label(self):
        """Create a node with a single label."""
        gf = GraphForge()
        node = gf.create_node(["Person"], name="Alice", age=30)

        assert isinstance(node, NodeRef)
        assert node.id == 1
        assert "Person" in node.labels
        assert len(node.labels) == 1
        assert node.properties["name"].value == "Alice"
        assert node.properties["age"].value == 30

    def test_create_node_with_multiple_labels(self):
        """Create a node with multiple labels."""
        gf = GraphForge()
        node = gf.create_node(["Person", "Employee"], name="Bob")

        assert "Person" in node.labels
        assert "Employee" in node.labels
        assert len(node.labels) == 2

    def test_create_node_with_no_labels(self):
        """Create a node without labels."""
        gf = GraphForge()
        node = gf.create_node(name="Unlabeled")

        assert len(node.labels) == 0
        assert node.properties["name"].value == "Unlabeled"

    def test_create_node_with_no_properties(self):
        """Create a node without properties."""
        gf = GraphForge()
        node = gf.create_node(["Person"])

        assert "Person" in node.labels
        assert len(node.properties) == 0

    def test_create_multiple_nodes_auto_increment_ids(self):
        """IDs should auto-increment for multiple nodes."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")

        assert alice.id == 1
        assert bob.id == 2
        assert charlie.id == 3

    def test_create_node_added_to_graph(self):
        """Created nodes should be added to the graph."""
        gf = GraphForge()
        gf.create_node(["Person"], name="Alice")
        gf.create_node(["Person"], name="Bob")

        # Query to verify nodes are in graph
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob"}


class TestCreateRelationship:
    """Tests for create_relationship() method."""

    def test_create_relationship_basic(self):
        """Create a basic relationship between two nodes."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        knows = gf.create_relationship(alice, bob, "KNOWS", since=2020)

        assert isinstance(knows, EdgeRef)
        assert knows.id == 1
        assert knows.type == "KNOWS"
        assert knows.src == alice
        assert knows.dst == bob
        assert knows.properties["since"].value == 2020

    def test_create_relationship_with_no_properties(self):
        """Create a relationship without properties."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        knows = gf.create_relationship(alice, bob, "KNOWS")

        assert knows.type == "KNOWS"
        assert len(knows.properties) == 0

    def test_create_multiple_relationships_auto_increment_ids(self):
        """IDs should auto-increment for multiple relationships."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")

        r1 = gf.create_relationship(alice, bob, "KNOWS")
        r2 = gf.create_relationship(bob, charlie, "KNOWS")
        r3 = gf.create_relationship(alice, charlie, "KNOWS")

        assert r1.id == 1
        assert r2.id == 2
        assert r3.id == 3

    def test_create_relationship_added_to_graph(self):
        """Created relationships should be added to the graph."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(alice, bob, "KNOWS", since=2020)

        # Query to verify relationship is in graph
        results = gf.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            RETURN a.name AS a_name, b.name AS b_name, r.since AS since
        """)
        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"
        assert results[0]["since"].value == 2020

    def test_create_multiple_relationship_types(self):
        """Create different relationship types."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        company = gf.create_node(["Company"], name="TechCorp")

        gf.create_relationship(alice, company, "WORKS_AT")
        gf.create_relationship(alice, company, "FOUNDED")

        # Verify both relationships exist by counting
        results = gf.execute("MATCH (p:Person)-[r]->(c:Company) RETURN COUNT(r) AS count")
        assert results[0]["count"].value == 2


class TestTypeConversion:
    """Tests for _to_cypher_value() type conversion."""

    def test_string_conversion(self):
        """String values should convert to CypherString."""
        gf = GraphForge()
        node = gf.create_node(["Person"], name="Alice")
        assert isinstance(node.properties["name"], CypherString)
        assert node.properties["name"].value == "Alice"

    def test_int_conversion(self):
        """Int values should convert to CypherInt."""
        gf = GraphForge()
        node = gf.create_node(["Person"], age=30)
        assert isinstance(node.properties["age"], CypherInt)
        assert node.properties["age"].value == 30

    def test_float_conversion(self):
        """Float values should convert to CypherFloat."""
        gf = GraphForge()
        node = gf.create_node(["Person"], height=5.9)
        assert isinstance(node.properties["height"], CypherFloat)
        assert node.properties["height"].value == 5.9

    def test_bool_conversion(self):
        """Bool values should convert to CypherBool."""
        gf = GraphForge()
        node = gf.create_node(["Person"], active=True, verified=False)
        assert isinstance(node.properties["active"], CypherBool)
        assert node.properties["active"].value is True
        assert isinstance(node.properties["verified"], CypherBool)
        assert node.properties["verified"].value is False

    def test_none_conversion(self):
        """None should convert to CypherNull."""
        gf = GraphForge()
        node = gf.create_node(["Person"], middle_name=None)
        assert isinstance(node.properties["middle_name"], CypherNull)

    def test_list_conversion(self):
        """Lists should convert to CypherList."""
        gf = GraphForge()
        node = gf.create_node(["Person"], hobbies=["reading", "coding"])
        assert isinstance(node.properties["hobbies"], CypherList)
        assert len(node.properties["hobbies"].value) == 2
        assert node.properties["hobbies"].value[0].value == "reading"
        assert node.properties["hobbies"].value[1].value == "coding"

    def test_nested_list_conversion(self):
        """Nested lists should convert recursively."""
        gf = GraphForge()
        node = gf.create_node(["Person"], matrix=[[1, 2], [3, 4]])
        assert isinstance(node.properties["matrix"], CypherList)
        assert isinstance(node.properties["matrix"].value[0], CypherList)
        assert node.properties["matrix"].value[0].value[0].value == 1

    def test_dict_conversion(self):
        """Dicts should convert to CypherMap."""
        gf = GraphForge()
        node = gf.create_node(["Person"], address={"city": "NYC", "zip": 10001})
        assert isinstance(node.properties["address"], CypherMap)
        assert node.properties["address"].value["city"].value == "NYC"
        assert node.properties["address"].value["zip"].value == 10001

    def test_nested_dict_conversion(self):
        """Nested dicts should convert recursively."""
        gf = GraphForge()
        node = gf.create_node(["Person"], location={"address": {"city": "NYC"}})
        assert isinstance(node.properties["location"], CypherMap)
        assert isinstance(node.properties["location"].value["address"], CypherMap)
        assert node.properties["location"].value["address"].value["city"].value == "NYC"

    def test_mixed_types(self):
        """Multiple property types in one node."""
        gf = GraphForge()
        node = gf.create_node(
            ["Person"],
            name="Alice",
            age=30,
            height=5.9,
            active=True,
            middle_name=None,
            hobbies=["reading", "coding"],
            address={"city": "NYC", "zip": 10001},
        )
        assert isinstance(node.properties["name"], CypherString)
        assert isinstance(node.properties["age"], CypherInt)
        assert isinstance(node.properties["height"], CypherFloat)
        assert isinstance(node.properties["active"], CypherBool)
        assert isinstance(node.properties["middle_name"], CypherNull)
        assert isinstance(node.properties["hobbies"], CypherList)
        assert isinstance(node.properties["address"], CypherMap)

    def test_unsupported_type_raises_error(self):
        """Unsupported types should raise TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="Unsupported property value type"):
            gf.create_node(["Person"], obj=object())


class TestCreateAndQuery:
    """Integration tests combining create and query operations."""

    def test_create_and_query_nodes(self):
        """Create nodes and query them."""
        gf = GraphForge()
        gf.create_node(["Person"], name="Alice", age=30)
        gf.create_node(["Person"], name="Bob", age=25)
        gf.create_node(["Person"], name="Charlie", age=35)

        # Query all persons
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
        assert len(results) == 3
        names = [r["name"].value for r in results]
        assert names == ["Alice", "Bob", "Charlie"]

        # Query with WHERE clause
        results = gf.execute("MATCH (p:Person) WHERE p.age > 30 RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Charlie"

    def test_create_and_query_relationships(self):
        """Create relationships and query them."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")

        gf.create_relationship(alice, bob, "KNOWS", since=2020)
        gf.create_relationship(bob, charlie, "KNOWS", since=2021)

        # Query relationships
        results = gf.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            RETURN a.name AS a_name, b.name AS b_name
            ORDER BY a_name, b_name
        """)
        assert len(results) == 2
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"
        assert results[1]["a_name"].value == "Bob"
        assert results[1]["b_name"].value == "Charlie"

    def test_create_graph_and_traverse(self):
        """Create a small graph and traverse it."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")
        dave = gf.create_node(["Person"], name="Dave")

        # Create relationships: Alice -> Bob -> Charlie
        #                      Alice -> Dave
        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(bob, charlie, "KNOWS")
        gf.create_relationship(alice, dave, "KNOWS")

        # Find friends of Alice using WHERE clause
        results = gf.execute("""
            MATCH (alice:Person)-[:KNOWS]->(friend:Person)
            WHERE alice.name = 'Alice'
            RETURN friend.name AS name
            ORDER BY name
        """)
        assert len(results) == 2
        names = [r["name"].value for r in results]
        assert names == ["Bob", "Dave"]

    def test_create_and_aggregate(self):
        """Create nodes and use aggregation queries."""
        gf = GraphForge()
        gf.create_node(["Person"], name="Alice", city="NYC")
        gf.create_node(["Person"], name="Bob", city="NYC")
        gf.create_node(["Person"], name="Charlie", city="LA")
        gf.create_node(["Person"], name="Dave", city="LA")
        gf.create_node(["Person"], name="Eve", city="LA")

        # Count by city
        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.city AS city, COUNT(*) AS count
            ORDER BY city
        """)
        assert len(results) == 2
        assert results[0]["city"].value == "LA"
        assert results[0]["count"].value == 3
        assert results[1]["city"].value == "NYC"
        assert results[1]["count"].value == 2


class TestRealWorldExample:
    """Real-world usage example."""

    def test_social_network_example(self):
        """Build a small social network and query it."""
        gf = GraphForge()

        # Create people
        alice = gf.create_node(["Person"], name="Alice", age=30, city="NYC")
        bob = gf.create_node(["Person"], name="Bob", age=25, city="NYC")
        charlie = gf.create_node(["Person"], name="Charlie", age=35, city="LA")
        dave = gf.create_node(["Person"], name="Dave", age=28, city="LA")

        # Create friendships
        gf.create_relationship(alice, bob, "KNOWS", since=2015, closeness=0.9)
        gf.create_relationship(alice, charlie, "KNOWS", since=2018, closeness=0.7)
        gf.create_relationship(bob, dave, "KNOWS", since=2020, closeness=0.8)
        gf.create_relationship(charlie, dave, "KNOWS", since=2019, closeness=0.6)

        # Query: Find Alice's friends using WHERE clause
        results = gf.execute("""
            MATCH (alice:Person)-[r:KNOWS]->(friend:Person)
            WHERE alice.name = 'Alice'
            RETURN friend.name AS name, r.closeness AS closeness
            ORDER BY closeness DESC
        """)
        assert len(results) == 2
        assert results[0]["name"].value == "Bob"
        assert results[0]["closeness"].value == 0.9

        # Query: Find people in NYC using WHERE clause
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.city = 'NYC'
            RETURN p.name AS name
            ORDER BY name
        """)
        assert len(results) == 2
        names = [r["name"].value for r in results]
        assert names == ["Alice", "Bob"]

        # Query: Average age by city
        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.city AS city, AVG(p.age) AS avg_age
            ORDER BY city
        """)
        assert len(results) == 2
        assert results[0]["city"].value == "LA"
        assert results[0]["avg_age"].value == 31.5  # (35 + 28) / 2
        assert results[1]["city"].value == "NYC"
        assert results[1]["avg_age"].value == 27.5  # (30 + 25) / 2
