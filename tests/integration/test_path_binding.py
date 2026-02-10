"""Integration tests for path binding functionality."""

import pytest

from graphforge import GraphForge
from graphforge.types import CypherPath


class TestPathBindingSingleHop:
    """Test path binding with single-hop patterns."""

    def test_simple_path_binding(self):
        """Test simple path binding: p = (a)-[:R]->(b)"""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute("MATCH p = (a:Person)-[:KNOWS]->(b:Person) RETURN p")

        assert len(results) == 1
        path = results[0]["p"]
        assert isinstance(path, CypherPath)
        assert path.length() == 1
        assert len(path.nodes) == 2
        assert len(path.relationships) == 1
        assert path.nodes[0].id == a.id
        assert path.nodes[1].id == b.id

    def test_path_binding_with_properties(self):
        """Test path binding with node and relationship properties."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice", age=30)
        b = gf.create_node(["Person"], name="Bob", age=25)
        gf.create_relationship(a, b, "KNOWS", since=2020)

        results = gf.execute(
            "MATCH p = (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person) RETURN p"
        )

        assert len(results) == 1
        path = results[0]["p"]
        assert path.length() == 1
        assert path.nodes[0].properties["name"].value == "Alice"
        assert path.nodes[1].properties["name"].value == "Bob"

    def test_path_binding_return_path_variable(self):
        """Test returning just the path variable."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute("MATCH p = (a)-[:KNOWS]->(b) RETURN p")

        assert len(results) == 1
        assert "p" in results[0]
        assert isinstance(results[0]["p"], CypherPath)

    def test_path_binding_with_node_variables(self):
        """Test path binding while also binding node variables."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            "MATCH p = (a:Person)-[:KNOWS]->(b:Person) RETURN p, a.name, b.name"
        )

        assert len(results) == 1
        assert isinstance(results[0]["p"], CypherPath)
        assert results[0]["a.name"].value == "Alice"
        assert results[0]["b.name"].value == "Bob"

    def test_path_binding_undirected(self):
        """Test path binding with undirected relationship."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute("MATCH p = (a:Person)-[:KNOWS]-(b:Person) RETURN p")

        # Should match both directions
        assert len(results) == 2
        for result in results:
            assert isinstance(result["p"], CypherPath)
            assert result["p"].length() == 1

    def test_path_binding_left_direction(self):
        """Test path binding with incoming relationship."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute("MATCH p = (b:Person)<-[:KNOWS]-(a:Person) RETURN p")

        assert len(results) == 1
        path = results[0]["p"]
        assert path.nodes[0].properties["name"].value == "Bob"
        assert path.nodes[1].properties["name"].value == "Alice"

    def test_multiple_path_bindings(self):
        """Test multiple path bindings in same query."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        c = gf.create_node(["Company"], name="TechCorp")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(a, c, "WORKS_AT")

        results = gf.execute(
            """
            MATCH p1 = (a:Person)-[:KNOWS]->(b:Person),
                  p2 = (a)-[:WORKS_AT]->(c:Company)
            RETURN p1, p2
            """
        )

        assert len(results) == 1
        assert isinstance(results[0]["p1"], CypherPath)
        assert isinstance(results[0]["p2"], CypherPath)
        assert results[0]["p1"].length() == 1
        assert results[0]["p2"].length() == 1


class TestPathBindingVariableLength:
    """Test path binding with variable-length patterns."""

    def test_path_binding_variable_length_basic(self):
        """Test path binding with variable-length pattern."""
        gf = GraphForge()

        # Create chain: A -> B -> C
        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute("MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x) RETURN p")

        assert len(results) == 2  # A->B and A->B->C

        # Check 1-hop path
        one_hop = [r for r in results if r["p"].length() == 1][0]
        assert one_hop["p"].length() == 1
        assert len(one_hop["p"].nodes) == 2
        assert len(one_hop["p"].relationships) == 1

        # Check 2-hop path
        two_hop = [r for r in results if r["p"].length() == 2][0]
        assert two_hop["p"].length() == 2
        assert len(two_hop["p"].nodes) == 3
        assert len(two_hop["p"].relationships) == 2

    def test_path_binding_variable_length_unbounded(self):
        """Test path binding with unbounded variable-length pattern."""
        gf = GraphForge()

        # Create chain: A -> B -> C
        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute("MATCH p = (a {name: 'A'})-[:KNOWS*]->(x) RETURN p")

        assert len(results) == 2
        lengths = [r["p"].length() for r in results]
        assert 1 in lengths  # A->B
        assert 2 in lengths  # A->B->C

    def test_path_binding_variable_length_node_sequence(self):
        """Test that variable-length path has correct node sequence."""
        gf = GraphForge()

        # Create chain: A -> B -> C -> D
        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")
        d = gf.create_node(["Person"], name="D")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")
        gf.create_relationship(c, d, "KNOWS")

        results = gf.execute("MATCH p = (a {name: 'A'})-[:KNOWS*3..3]->(x) RETURN p")

        assert len(results) == 1
        path = results[0]["p"]
        assert path.length() == 3
        assert len(path.nodes) == 4

        # Verify node sequence
        names = [node.properties["name"].value for node in path.nodes]
        assert names == ["A", "B", "C", "D"]

    def test_path_binding_variable_length_relationship_sequence(self):
        """Test that variable-length path has correct relationship sequence."""
        gf = GraphForge()

        # Create chain with different relationship types
        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute("MATCH p = (a {name: 'A'})-[:KNOWS*2..2]->(x) RETURN p")

        assert len(results) == 1
        path = results[0]["p"]
        assert len(path.relationships) == 2
        assert all(rel.type == "KNOWS" for rel in path.relationships)

    def test_path_binding_variable_length_min_only(self):
        """Test variable-length with minimum only."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute("MATCH p = (a {name: 'A'})-[:KNOWS*2..]->(x) RETURN p")

        # Should only match 2-hop path
        assert len(results) == 1
        assert results[0]["p"].length() == 2

    def test_path_binding_variable_length_with_where(self):
        """Test path binding with WHERE clause."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            WHERE x.name = 'C'
            RETURN p
            """
        )

        assert len(results) == 1
        assert results[0]["p"].length() == 2


class TestPathBindingLongPaths:
    """Test path binding with longer fixed-length paths."""

    def test_three_hop_path_binding(self):
        """Test path binding with 3-hop fixed pattern."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")
        d = gf.create_node(["Person"], name="D")

        gf.create_relationship(a, b, "R1")
        gf.create_relationship(b, c, "R2")
        gf.create_relationship(c, d, "R3")

        results = gf.execute("MATCH p = (a)-[:R1]->(b)-[:R2]->(c)-[:R3]->(d) RETURN p")

        assert len(results) == 1
        path = results[0]["p"]
        assert path.length() == 3
        assert len(path.nodes) == 4
        assert len(path.relationships) == 3

    def test_mixed_relationship_types(self):
        """Test path with different relationship types."""
        gf = GraphForge()

        person = gf.create_node(["Person"], name="Alice")
        company = gf.create_node(["Company"], name="TechCorp")
        city = gf.create_node(["City"], name="NYC")

        gf.create_relationship(person, company, "WORKS_AT")
        gf.create_relationship(company, city, "LOCATED_IN")

        results = gf.execute(
            "MATCH p = (person:Person)-[:WORKS_AT]->(company)-[:LOCATED_IN]->(city) RETURN p"
        )

        assert len(results) == 1
        path = results[0]["p"]
        assert path.length() == 2
        assert path.relationships[0].type == "WORKS_AT"
        assert path.relationships[1].type == "LOCATED_IN"


class TestPathBindingEdgeCases:
    """Test edge cases for path binding."""

    def test_path_binding_single_node(self):
        """Test path binding with single node pattern."""
        gf = GraphForge()

        gf.create_node(["Person"], name="Alice")

        results = gf.execute("MATCH p = (a:Person) RETURN p")

        assert len(results) == 1
        path = results[0]["p"]
        assert isinstance(path, CypherPath)
        assert path.length() == 0
        assert len(path.nodes) == 1
        assert len(path.relationships) == 0

    def test_path_with_no_results(self):
        """Test path binding query that matches nothing."""
        gf = GraphForge()

        gf.create_node(["Person"], name="Alice")

        results = gf.execute("MATCH p = (a:Person)-[:KNOWS]->(b) RETURN p")

        assert len(results) == 0

    def test_path_binding_anonymous_nodes(self):
        """Test path binding with anonymous node patterns."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute("MATCH p = ()-[:KNOWS]->() RETURN p")

        assert len(results) == 1
        assert isinstance(results[0]["p"], CypherPath)

    def test_path_equality(self):
        """Test that identical paths are equal."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            """
            MATCH p1 = (a:Person {name: 'Alice'})-[:KNOWS]->(b),
                  p2 = (a)-[:KNOWS]->(b)
            RETURN p1, p2
            """
        )

        assert len(results) == 1
        p1 = results[0]["p1"]
        p2 = results[0]["p2"]

        # Paths should be equal (same nodes and relationships)
        result = p1.equals(p2)
        assert result.value is True

    def test_mixed_binding_and_non_binding(self):
        """Test query with both path-bound and non-bound patterns."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        c = gf.create_node(["Person"], name="Charlie")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(a, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a:Person {name: 'Alice'})-[:KNOWS]->(b),
                  (a)-[:KNOWS]->(c)
            WHERE b.name <> c.name
            RETURN p, b.name, c.name
            """
        )

        assert len(results) == 2
        for result in results:
            assert isinstance(result["p"], CypherPath)
