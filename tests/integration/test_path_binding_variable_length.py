"""Integration tests for path binding with variable-length patterns."""

import pytest

from graphforge import GraphForge
from graphforge.types import CypherPath


class TestPathBindingVariableLength:
    """Test path binding with variable-length patterns."""

    def test_variable_length_path_binding_single_result(self):
        """Test path binding with variable-length pattern returning single path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..1]->(b)
            RETURN p, length(p) AS len
            """
        )

        assert len(results) == 1
        assert isinstance(results[0]["p"], CypherPath)
        assert results[0]["len"].value == 1
        assert len(results[0]["p"].nodes) == 2
        assert len(results[0]["p"].relationships) == 1

    def test_variable_length_path_binding_multiple_results(self):
        """Test path binding with variable-length pattern returning multiple paths."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN x.name AS name, length(p) AS len
            ORDER BY len
            """
        )

        assert len(results) == 2
        # 1-hop: A -> B
        assert results[0]["name"].value == "B"
        assert results[0]["len"].value == 1
        # 2-hop: A -> B -> C
        assert results[1]["name"].value == "C"
        assert results[1]["len"].value == 2

    def test_variable_length_path_with_nodes_function(self):
        """Test nodes() function with variable-length path binding."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN length(p) AS len, size(nodes(p)) AS nodeCount
            ORDER BY len
            """
        )

        assert len(results) == 2
        # 1-hop: 2 nodes
        assert results[0]["len"].value == 1
        assert results[0]["nodeCount"].value == 2
        # 2-hop: 3 nodes
        assert results[1]["len"].value == 2
        assert results[1]["nodeCount"].value == 3

    def test_variable_length_path_with_relationships_function(self):
        """Test relationships() function with variable-length path binding."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN length(p) AS len, size(relationships(p)) AS relCount
            ORDER BY len
            """
        )

        assert len(results) == 2
        # 1-hop: 1 relationship
        assert results[0]["len"].value == 1
        assert results[0]["relCount"].value == 1
        # 2-hop: 2 relationships
        assert results[1]["len"].value == 2
        assert results[1]["relCount"].value == 2

    def test_variable_length_unbounded_path_binding(self):
        """Test path binding with unbounded variable-length pattern."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")
        d = gf.create_node(["Person"], name="D")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")
        gf.create_relationship(c, d, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*2..]->(x)
            RETURN x.name AS name, length(p) AS len
            ORDER BY len
            """
        )

        # Should find paths of length 2 and 3 (min_hops=2)
        assert len(results) == 2
        assert results[0]["name"].value == "C"
        assert results[0]["len"].value == 2
        assert results[1]["name"].value == "D"
        assert results[1]["len"].value == 3

    def test_variable_length_path_binding_with_where(self):
        """Test path binding with variable-length pattern and WHERE clause."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            WHERE length(p) = 2
            RETURN x.name AS name
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "C"

    def test_variable_length_path_undirected(self):
        """Test path binding with undirected variable-length pattern."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'C'})-[:KNOWS*1..2]-(x)
            RETURN x.name AS name, length(p) AS len
            ORDER BY len, name
            """
        )

        # Should find: C-B (1 hop), C-B-A (2 hops)
        assert len(results) == 2
        assert results[0]["name"].value == "B"
        assert results[0]["len"].value == 1
        assert results[1]["name"].value == "A"
        assert results[1]["len"].value == 2

    def test_variable_length_path_reverse_direction(self):
        """Test path binding with reverse direction variable-length pattern."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (x)-[:KNOWS*1..2]->(a {name: 'C'})
            RETURN x.name AS name, length(p) AS len
            ORDER BY len, name
            """
        )

        # Should find: B->C (1 hop), A->B->C (2 hops)
        assert len(results) == 2
        assert results[0]["name"].value == "B"
        assert results[0]["len"].value == 1
        assert results[1]["name"].value == "A"
        assert results[1]["len"].value == 2

    def test_variable_length_min_only(self):
        """Test variable-length pattern with only minimum hops specified."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*2..]->(x)
            RETURN x.name AS name, length(p) AS len
            """
        )

        # Should only find path of length 2 (min_hops=2)
        assert len(results) == 1
        assert results[0]["name"].value == "C"
        assert results[0]["len"].value == 2

    def test_variable_length_max_only(self):
        """Test variable-length pattern with only maximum hops specified."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*..1]->(x)
            RETURN x.name AS name, length(p) AS len
            """
        )

        # Should only find path of length 1 (max_hops=1)
        assert len(results) == 1
        assert results[0]["name"].value == "B"
        assert results[0]["len"].value == 1

    def test_variable_length_cycle_detection(self):
        """Test that variable-length patterns don't create cycles."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")

        # Create cycle: A -> B -> A
        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, a, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..3]->(x)
            RETURN x.name AS name, length(p) AS len
            ORDER BY len
            """
        )

        # Should only find A -> B (length 1)
        # Cycle detection prevents A -> B -> A
        assert len(results) == 1
        assert results[0]["name"].value == "B"
        assert results[0]["len"].value == 1

    @pytest.mark.skip(reason="Grammar doesn't support multiple types with variable-length yet")
    def test_variable_length_multiple_types(self):
        """Test variable-length pattern with multiple relationship types."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "LIKES")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS|LIKES*1..2]->(x)
            RETURN x.name AS name, length(p) AS len
            ORDER BY len, name
            """
        )

        # Should find: A-KNOWS->B (1 hop), A-KNOWS->B-LIKES->C (2 hops)
        assert len(results) == 2
        assert results[0]["name"].value == "B"
        assert results[0]["len"].value == 1
        assert results[1]["name"].value == "C"
        assert results[1]["len"].value == 2
