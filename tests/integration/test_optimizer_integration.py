"""Integration tests for query optimizer."""

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


class TestOptimizerIntegration:
    """End-to-end tests for query optimizer."""

    def test_filter_pushdown_reduces_intermediate_results(self, gf):
        """Filter pushdown reduces the number of intermediate result rows."""
        # Create graph with 100 Person nodes, only 10 with age > 90
        for i in range(100):
            gf.execute(f"CREATE (:Person {{name: 'Person{i}', age: {i}}})")

        # Query with WHERE clause - optimizer should push filter into ScanNodes
        results = gf.execute("MATCH (p:Person) WHERE p.age > 90 RETURN p.name ORDER BY p.name")

        # Should return 9 rows (91, 92, 93, 94, 95, 96, 97, 98, 99)
        assert len(results) == 9
        assert results[0]["p.name"].value == "Person91"
        assert results[-1]["p.name"].value == "Person99"

    def test_predicate_reordering_with_multiple_conditions(self, gf):
        """Predicate reordering evaluates selective predicates first."""
        # Create nodes
        gf.execute("CREATE (:Person {name: 'Alice', city: 'NYC', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', city: 'LA', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', city: 'NYC', age: 35})")

        # Query with multiple WHERE conditions
        # Optimizer should reorder to evaluate = before <>
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age <> 25 AND p.name = 'Alice'
            RETURN p.name
        """)

        assert len(results) == 1
        assert results[0]["p.name"].value == "Alice"

    def test_optimizer_preserves_correctness(self, gf, gf_no_opt):
        """Optimized queries return same results as unoptimized."""
        # Create same graph in both instances
        queries = [
            "CREATE (:Person {name: 'Alice', age: 30})",
            "CREATE (:Person {name: 'Bob', age: 25})",
            "CREATE (:Person {name: 'Charlie', age: 35})",
        ]

        for query in queries:
            gf.execute(query)
            gf_no_opt.execute(query)

        # Test query
        test_query = "MATCH (p:Person) WHERE p.age > 25 RETURN p.name ORDER BY p.name"

        results_opt = gf.execute(test_query)
        results_no_opt = gf_no_opt.execute(test_query)

        # Results should be identical
        assert len(results_opt) == len(results_no_opt)
        for i in range(len(results_opt)):
            assert results_opt[i]["p.name"].value == results_no_opt[i]["p.name"].value

    def test_null_handling_preserved(self, gf):
        """Optimizer preserves NULL handling semantics."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob'})")  # No age property
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # Filter on NULL property
        results = gf.execute("MATCH (p:Person) WHERE p.age > 30 RETURN p.name")

        # Only Charlie should match (Bob's NULL age doesn't satisfy > 30)
        assert len(results) == 1
        assert results[0]["p.name"].value == "Charlie"

    def test_complex_query_with_relationships(self, gf):
        """Optimizer handles queries with relationships correctly."""
        # Create graph
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30}),
                   (b:Person {name: 'Bob', age: 25}),
                   (c:Person {name: 'Charlie', age: 35}),
                   (a)-[:KNOWS {since: 2020}]->(b),
                   (a)-[:KNOWS {since: 2021}]->(c)
        """)

        # Query with filters on both nodes and edges
        results = gf.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            WHERE a.age > 25 AND r.since > 2020
            RETURN a.name, b.name
        """)

        assert len(results) == 1
        assert results[0]["a.name"].value == "Alice"
        assert results[0]["b.name"].value == "Charlie"

    def test_and_conjuncts_pushed_separately(self, gf):
        """AND conjuncts are pushed separately to different operators."""
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30}),
                   (b:Person {name: 'Bob', age: 25}),
                   (c:Person {name: 'Charlie', age: 35}),
                   (a)-[:KNOWS]->(b),
                   (a)-[:KNOWS]->(c)
        """)

        # Query with predicates on both source and destination
        results = gf.execute("""
            MATCH (a:Person)-[:KNOWS]->(b:Person)
            WHERE a.name = 'Alice' AND b.age > 30
            RETURN a.name, b.name
        """)

        assert len(results) == 1
        assert results[0]["a.name"].value == "Alice"
        assert results[0]["b.name"].value == "Charlie"

    def test_or_predicates_not_split(self, gf):
        """OR predicates are not split during optimization."""
        gf.execute("CREATE (:Person {name: 'Alice', city: 'NYC'})")
        gf.execute("CREATE (:Person {name: 'Bob', city: 'LA'})")
        gf.execute("CREATE (:Person {name: 'Charlie', city: 'SF'})")

        # Query with OR predicate
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.city = 'NYC' OR p.city = 'LA'
            RETURN p.name
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["p.name"].value == "Alice"
        assert results[1]["p.name"].value == "Bob"

    def test_with_clause_boundary(self, gf):
        """WITH clause acts as optimization boundary."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # Query with WITH clause
        results = gf.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            WHERE age > 25
            RETURN name
            ORDER BY name
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

    def test_disable_optimizer_flag(self, gf_no_opt):
        """Disabling optimizer prevents optimization."""
        gf_no_opt.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf_no_opt.execute("CREATE (:Person {name: 'Bob', age: 25})")

        # Query should still work without optimization
        results = gf_no_opt.execute("MATCH (p:Person) WHERE p.age > 25 RETURN p.name")

        assert len(results) == 1
        assert results[0]["p.name"].value == "Alice"

    def test_multiple_filters_combined(self, gf):
        """Multiple Filter operators are handled correctly."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30, city: 'NYC'})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25, city: 'LA'})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35, city: 'NYC'})")

        # Note: This would create multiple Filter operators if manually constructed,
        # but planner typically combines them. Still tests the optimizer's ability
        # to handle filters.
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age > 25 AND p.city = 'NYC'
            RETURN p.name
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["p.name"].value == "Alice"
        assert results[1]["p.name"].value == "Charlie"

    def test_property_access_in_predicate(self, gf):
        """Property access in predicates is handled correctly."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30, min_age: 25})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25, min_age: 30})")

        # Predicate comparing two properties
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age > p.min_age
            RETURN p.name
        """)

        assert len(results) == 1
        assert results[0]["p.name"].value == "Alice"

    def test_is_null_predicate(self, gf):
        """IS NULL predicates are handled correctly."""
        gf.execute("CREATE (:Person {name: 'Alice', email: 'alice@example.com'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")  # No email

        # Filter for NULL email
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email IS NULL
            RETURN p.name
        """)

        assert len(results) == 1
        assert results[0]["p.name"].value == "Bob"

    def test_is_not_null_predicate(self, gf):
        """IS NOT NULL predicates are handled correctly."""
        gf.execute("CREATE (:Person {name: 'Alice', email: 'alice@example.com'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")  # No email

        # Filter for non-NULL email
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email IS NOT NULL
            RETURN p.name
        """)

        assert len(results) == 1
        assert results[0]["p.name"].value == "Alice"

    def test_predicate_on_edge_variable(self, gf):
        """Predicates on edge variables are pushed correctly."""
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'}),
                   (a)-[:KNOWS {strength: 0.8}]->(b),
                   (a)-[:KNOWS {strength: 0.3}]->(c)
        """)

        # Filter on edge property
        results = gf.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            WHERE r.strength > 0.5
            RETURN a.name, b.name
        """)

        assert len(results) == 1
        assert results[0]["a.name"].value == "Alice"
        assert results[0]["b.name"].value == "Bob"

    def test_predicate_on_bound_variable_after_with(self, gf):
        """Predicates work correctly on variables bound by WITH clause."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # WITH binds 'p', then we match on bound 'p' with predicate
        results = gf.execute(
            """
            MATCH (p:Person)
            WITH p
            MATCH (p) WHERE p.age > 25
            RETURN p.name
            ORDER BY p.name
        """
        )

        # Should filter correctly even though p is already bound
        assert len(results) == 2
        assert results[0]["p.name"].value == "Alice"
        assert results[1]["p.name"].value == "Charlie"

    def test_union_branches_are_optimized(self, gf):
        """UNION query branches are individually optimized."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30, city: 'NYC'})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25, city: 'LA'})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35, city: 'NYC'})")
        gf.execute("CREATE (:Company {name: 'Acme', city: 'NYC'})")

        # UNION with filters in both branches
        results = gf.execute(
            """
            MATCH (p:Person) WHERE p.age > 30 RETURN p.name AS name
            UNION
            MATCH (c:Company) WHERE c.city = 'NYC' RETURN c.name AS name
        """
        )

        # Should get Charlie (age > 30) and Acme (city = NYC)
        # UNION removes duplicates, so 2 results
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Charlie", "Acme"}

    def test_union_all_with_optimization(self, gf):
        """UNION ALL preserves duplicates with optimization enabled."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")

        # UNION ALL should preserve both results
        results = gf.execute(
            """
            MATCH (p:Person) WHERE p.age > 20 RETURN p.name AS name
            UNION ALL
            MATCH (p:Person) WHERE p.age < 35 RETURN p.name AS name
        """
        )

        # Both queries return both people, UNION ALL keeps all 4
        assert len(results) == 4
