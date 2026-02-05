"""Integration tests for id() function with Cypher queries.

Tests end-to-end behavior of the id() function in realistic query scenarios.
"""

import pytest

from graphforge import GraphForge

pytestmark = pytest.mark.integration


class TestIdFunctionIntegration:
    """Integration tests for id() function."""

    def test_id_in_return_clause(self):
        """Test id() in RETURN clause."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, id(p) AS node_id")

        assert len(results) == 2
        # Check that each result has a name and node_id
        for result in results:
            assert "name" in result
            assert "node_id" in result
            assert isinstance(result["node_id"].value, int)
            assert result["node_id"].value >= 0

    def test_id_in_where_clause(self):
        """Test id() in WHERE clause for filtering."""
        gf = GraphForge()
        # Create multiple nodes
        for i in range(5):
            gf.execute(f"CREATE (:Person {{name: 'Person{i}'}})")

        # Get all nodes and find the first ID
        all_results = gf.execute("MATCH (p:Person) RETURN id(p) AS node_id")
        first_id = all_results[0]["node_id"].value

        # Filter by ID
        filtered = gf.execute(f"MATCH (p:Person) WHERE id(p) = {first_id} RETURN p.name AS name")

        assert len(filtered) == 1
        assert filtered[0]["name"].value == "Person0"

    def test_id_comparison_in_where(self):
        """Test id() with comparison operators."""
        gf = GraphForge()
        for i in range(10):
            gf.execute(f"CREATE (:Number {{value: {i}}})")

        # Get minimum ID
        all_results = gf.execute("MATCH (n:Number) RETURN id(n) AS node_id")
        min_id = min(r["node_id"].value for r in all_results)
        threshold_id = min_id + 3

        # Get nodes with ID less than threshold
        filtered = gf.execute(
            f"MATCH (n:Number) WHERE id(n) < {threshold_id} RETURN id(n) AS node_id"
        )

        # Should get nodes with IDs: min_id, min_id+1, min_id+2
        assert len(filtered) == 3
        filtered_ids = [r["node_id"].value for r in filtered]
        assert all(nid < threshold_id for nid in filtered_ids)

    def test_id_with_relationships(self):
        """Test id() with relationships."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")

        results = gf.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) "
            "RETURN a.name AS from_name, b.name AS to_name, id(r) AS rel_id"
        )

        assert len(results) == 1
        assert results[0]["from_name"].value == "Alice"
        assert results[0]["to_name"].value == "Bob"
        assert isinstance(results[0]["rel_id"].value, int)
        assert results[0]["rel_id"].value >= 0

    def test_id_order_by(self):
        """Test id() in ORDER BY clause."""
        gf = GraphForge()
        for i in range(5):
            gf.execute(f"CREATE (:Item {{value: {i}}})")

        results = gf.execute("MATCH (n:Item) RETURN id(n) AS node_id ORDER BY id(n)")

        # Check that results are ordered by ID
        ids = [r["node_id"].value for r in results]
        assert ids == sorted(ids)

    def test_id_with_multiple_labels(self):
        """Test id() works with nodes having multiple labels."""
        gf = GraphForge()
        gf.execute("CREATE (:Person:Employee {name: 'Alice'})")

        results = gf.execute("MATCH (p:Person:Employee) RETURN id(p) AS node_id, p.name AS name")

        assert len(results) == 1
        assert isinstance(results[0]["node_id"].value, int)
        assert results[0]["name"].value == "Alice"

    def test_id_with_no_properties(self):
        """Test id() works with nodes having no properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Empty)")

        results = gf.execute("MATCH (n:Empty) RETURN id(n) AS node_id")

        assert len(results) == 1
        assert isinstance(results[0]["node_id"].value, int)

    def test_id_distinct_for_different_nodes(self):
        """Test that id() returns different values for different nodes."""
        gf = GraphForge()
        gf.execute("CREATE (:A), (:B), (:C)")

        results = gf.execute("MATCH (n) RETURN id(n) AS node_id")

        assert len(results) == 3
        ids = [r["node_id"].value for r in results]
        # All IDs should be distinct
        assert len(set(ids)) == 3

    def test_id_stable_within_session(self):
        """Test that id() returns same value for same node in multiple queries."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        # Query the ID multiple times
        result1 = gf.execute("MATCH (p:Person {name: 'Alice'}) RETURN id(p) AS node_id")
        result2 = gf.execute("MATCH (p:Person {name: 'Alice'}) RETURN id(p) AS node_id")
        result3 = gf.execute("MATCH (p:Person {name: 'Alice'}) RETURN id(p) AS node_id")

        # ID should be the same across queries
        assert result1[0]["node_id"].value == result2[0]["node_id"].value
        assert result2[0]["node_id"].value == result3[0]["node_id"].value
