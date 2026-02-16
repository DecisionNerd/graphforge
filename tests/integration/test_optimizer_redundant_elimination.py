"""Integration tests for redundant traversal elimination optimization."""

import pytest

from graphforge import GraphForge


@pytest.fixture
def gf():
    """Fixture providing a fresh GraphForge instance with optimizer enabled."""
    instance = GraphForge(enable_optimizer=True)
    yield instance
    # Cleanup: close the instance if it has backend
    if hasattr(instance, "backend") and instance.backend is not None:
        instance.close()


@pytest.fixture
def gf_no_opt():
    """Fixture providing a fresh GraphForge instance with optimizer disabled."""
    instance = GraphForge(enable_optimizer=False)
    yield instance
    # Cleanup: close the instance if it has backend
    if hasattr(instance, "backend") and instance.backend is not None:
        instance.close()


class TestRedundantEliminationIntegration:
    """End-to-end tests for redundant traversal elimination."""

    def test_redundant_match_elimination(self, gf):
        """Query with duplicate MATCH clauses is optimized."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        # Query with duplicate MATCH (semantically redundant)
        query = """
        MATCH (a:Person)
        MATCH (a:Person)
        RETURN a.name AS name
        """

        results = gf.execute(query)

        # Should return same results as non-redundant query
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob"}

    def test_redundant_relationship_match(self, gf):
        """Query with duplicate relationship patterns is optimized."""
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)"
        )

        # Query with duplicate relationship expansion
        query = """
        MATCH (a:Person)
        MATCH (a)-[:KNOWS]->(b)
        MATCH (a)-[:KNOWS]->(c)
        RETURN a.name AS name, b.name AS friend1, c.name AS friend2
        ORDER BY friend1, friend2
        """

        results = gf.execute(query)

        # Should find all combinations
        assert len(results) == 4
        # Alice knows Bob and Charlie, so we get 2x2 = 4 combinations
        assert results[0]["name"].value == "Alice"

    def test_optimizer_preserves_correctness_with_redundancy(self, gf, gf_no_opt):
        """Optimized queries with redundant patterns return same results as unoptimized."""
        # Create same graph in both instances
        for instance in [gf, gf_no_opt]:
            instance.execute("CREATE (:Person {name: 'Alice', age: 30})")
            instance.execute("CREATE (:Person {name: 'Bob', age: 25})")
            instance.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # Query with redundant MATCH
        test_query = """
        MATCH (p:Person)
        MATCH (p:Person)
        WHERE p.age > 25
        RETURN p.name
        ORDER BY p.name
        """

        results_opt = gf.execute(test_query)
        results_no_opt = gf_no_opt.execute(test_query)

        # Results should be identical
        assert len(results_opt) == len(results_no_opt)
        assert len(results_opt) == 2
        for i in range(len(results_opt)):
            assert results_opt[i]["p.name"].value == results_no_opt[i]["p.name"].value

    def test_with_clause_prevents_elimination(self, gf):
        """WITH clause creates boundary that prevents redundancy elimination."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        # Query with MATCH before and after WITH
        query = """
        MATCH (p:Person)
        WITH p.name AS name
        MATCH (q:Person)
        RETURN name, q.name AS other
        ORDER BY name, other
        """

        results = gf.execute(query)

        # Should produce cartesian product: 2 names x 2 persons = 4 rows
        assert len(results) == 4
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Alice"

    def test_different_labels_not_eliminated(self, gf):
        """Patterns with different labels are not eliminated."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Company {name: 'ACME Corp'})")

        query = """
        MATCH (a:Person)
        MATCH (b:Company)
        RETURN a.name AS person, b.name AS company
        """

        results = gf.execute(query)

        # Should return cartesian product
        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["company"].value == "ACME Corp"

    def test_complex_query_with_multiple_redundancies(self, gf):
        """Complex query with multiple redundant patterns is optimized."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Company {name: 'ACME'})")

        query = """
        MATCH (p:Person)
        MATCH (p:Person)
        WHERE p.age > 20
        MATCH (c:Company)
        MATCH (c:Company)
        RETURN p.name AS person, c.name AS company
        ORDER BY person
        """

        results = gf.execute(query)

        # Should have 2 persons x 1 company = 2 results
        assert len(results) == 2
        assert results[0]["person"].value == "Alice"
        assert results[0]["company"].value == "ACME"
        assert results[1]["person"].value == "Bob"
        assert results[1]["company"].value == "ACME"

    def test_redundancy_with_predicates(self, gf):
        """Redundant patterns with same predicates are eliminated."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # Query with duplicate predicates (after filter pushdown, should have same signature)
        query = """
        MATCH (p:Person)
        WHERE p.age > 28
        WITH p
        MATCH (q:Person)
        WHERE q.age > 30
        RETURN p.name AS young, q.name AS old
        ORDER BY young, old
        """

        results = gf.execute(query)

        # Alice (30) and Charlie (35) match first condition
        # Charlie (35) matches second condition
        # Should get: (Alice, Charlie), (Charlie, Charlie)
        assert len(results) == 2

    def test_variable_length_path_redundancy(self, gf):
        """Redundant variable-length path patterns are eliminated."""
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:KNOWS]->(c)"
        )

        query = """
        MATCH (a:Person {name: 'Alice'})-[r*1..2]->(b)
        MATCH (a:Person {name: 'Alice'})-[r*1..2]->(b)
        RETURN b.name AS reachable
        ORDER BY reachable
        """

        results = gf.execute(query)

        # Should find Bob (1 hop) and Charlie (2 hops)
        # With redundant elimination, second MATCH is removed so we get 2 results
        # Without elimination, we'd get 4 results (cartesian product)
        assert len(results) == 2
        names = {r["reachable"].value for r in results}
        assert names == {"Bob", "Charlie"}

    def test_no_false_eliminations(self, gf):
        """Different patterns with same variable are not incorrectly eliminated."""
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:LIKES]->(b)"
        )

        # Different relationship types should NOT be eliminated
        query = """
        MATCH (a:Person {name: 'Alice'})-[:KNOWS]->(b)
        MATCH (a)-[:LIKES]->(c)
        RETURN b.name AS knows, c.name AS likes
        """

        results = gf.execute(query)

        # Should find both relationships
        assert len(results) == 1
        assert results[0]["knows"].value == "Bob"
        assert results[0]["likes"].value == "Bob"

    def test_empty_graph_redundancy(self, gf):
        """Redundant patterns work correctly on empty graph."""
        # Query with redundant MATCH on empty graph
        query = """
        MATCH (a:Person)
        MATCH (a:Person)
        RETURN a.name AS name
        """

        results = gf.execute(query)

        # Should return empty results
        assert len(results) == 0

    def test_single_node_redundancy(self, gf):
        """Redundant patterns work correctly with single node."""
        gf.execute("CREATE (:Person {name: 'Alice'})")

        query = """
        MATCH (a:Person)
        MATCH (a:Person)
        MATCH (a:Person)
        RETURN a.name AS name
        """

        results = gf.execute(query)

        # Should return single node once
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
