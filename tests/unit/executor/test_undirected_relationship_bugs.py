"""Unit tests for undirected relationship matching bugs (issue #126)."""

from graphforge.api import GraphForge


class TestUndirectedSelfLoops:
    """Tests for self-loop handling in undirected patterns."""

    def test_directed_self_loop_count(self):
        """Directed self-loop should match once."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("MATCH (p:Person {name: 'Alice'}) CREATE (p)-[:MANAGES]->(p)")

        results = gf.execute(
            """
            MATCH (x:Person)-[:MANAGES]->(x)
            RETURN count(*) AS cnt
            """
        )
        assert results[0]["cnt"].value == 1

    def test_undirected_self_loop_count(self):
        """Undirected self-loop should match once, not twice."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("MATCH (p:Person {name: 'Alice'}) CREATE (p)-[:MANAGES]->(p)")

        results = gf.execute(
            """
            MATCH (x:Person)-[:MANAGES]-(x)
            RETURN count(*) AS cnt
            """
        )
        # BUG: This currently returns 2 (counted twice), but should be 1
        # A self-loop A->A appears in both outgoing and incoming edges
        # In undirected mode, it should only be counted once
        assert results[0]["cnt"].value == 1

    def test_undirected_self_loop_distinct_edges(self):
        """Undirected self-loop should return one distinct edge."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("MATCH (p:Person {name: 'Alice'}) CREATE (p)-[:LIKES]->(p)")

        results = gf.execute(
            """
            MATCH (a:Person)-[r:LIKES]-(a)
            RETURN count(DISTINCT r) AS cnt
            """
        )
        assert results[0]["cnt"].value == 1

    def test_multiple_self_loops_undirected(self):
        """Multiple self-loops should each be counted once."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("MATCH (p:Person) CREATE (p)-[:TYPE1]->(p)")
        gf.execute("MATCH (p:Person) CREATE (p)-[:TYPE2]->(p)")

        results = gf.execute(
            """
            MATCH (x:Person)-[r]-(x)
            RETURN count(*) AS cnt
            """
        )
        # Should be 2 (one for each type), not 4
        assert results[0]["cnt"].value == 2


class TestUndirectedRegularEdges:
    """Tests for regular (non-self-loop) undirected edges."""

    def test_undirected_simple_pattern(self):
        """Undirected pattern should match in both directions."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        results = gf.execute(
            """
            MATCH (a:Person)-[:KNOWS]-(b:Person)
            RETURN a.name AS a_name, b.name AS b_name
            ORDER BY a_name, b_name
            """
        )
        assert len(results) == 2
        # Should get both (Alice, Bob) and (Bob, Alice)
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"
        assert results[1]["a_name"].value == "Bob"
        assert results[1]["b_name"].value == "Alice"

    def test_undirected_count(self):
        """Undirected count should be 2x directed count for regular edges."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        # Directed count
        directed_results = gf.execute(
            """
            MATCH (a:Person)-[:KNOWS]->(b:Person)
            RETURN count(*) AS cnt
            """
        )
        directed_count = directed_results[0]["cnt"].value

        # Undirected count
        undirected_results = gf.execute(
            """
            MATCH (a:Person)-[:KNOWS]-(b:Person)
            RETURN count(*) AS cnt
            """
        )
        undirected_count = undirected_results[0]["cnt"].value

        # Undirected should be 2x directed (both directions)
        assert undirected_count == 2 * directed_count
        assert undirected_count == 2


class TestMixedSelfLoopAndRegularEdges:
    """Tests for graphs with both self-loops and regular edges."""

    def test_self_loop_plus_regular_edge(self):
        """Graph with both self-loop and regular edge."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})")
        gf.execute("MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS]->(a)")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )

        results = gf.execute(
            """
            MATCH (x:Person)-[:KNOWS]-(y:Person)
            RETURN count(*) AS cnt
            """
        )
        # Should be 3:
        # - Self-loop (Alice, Alice) counted once
        # - Regular edge (Alice, Bob) counted twice (both directions)
        # Total: 1 + 2 = 3
        # BUG: Currently returns 4 (self-loop counted twice)
        assert results[0]["cnt"].value == 3

    def test_self_loop_plus_regular_edge_distinct_patterns(self):
        """Distinct (a,b) pairs for self-loop + regular edge."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})")
        gf.execute("MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS]->(a)")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )

        results = gf.execute(
            """
            MATCH (x:Person)-[:KNOWS]-(y:Person)
            RETURN DISTINCT x.name AS x_name, y.name AS y_name
            ORDER BY x_name, y_name
            """
        )
        # Should be 3 distinct pairs:
        # (Alice, Alice), (Alice, Bob), (Bob, Alice)
        assert len(results) == 3
        assert results[0]["x_name"].value == "Alice"
        assert results[0]["y_name"].value == "Alice"
        assert results[1]["x_name"].value == "Alice"
        assert results[1]["y_name"].value == "Bob"
        assert results[2]["x_name"].value == "Bob"
        assert results[2]["y_name"].value == "Alice"


class TestTriadicPatterns:
    """Tests for friend-of-friend (triadic) patterns."""

    def test_simple_triadic_pattern(self):
        """Simple 2-hop triadic pattern."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}) CREATE (b)-[:KNOWS]->(c:Person {name: 'Charlie'})"
        )

        results = gf.execute(
            """
            MATCH (x:Person)-[:KNOWS]-(y:Person)-[:KNOWS]-(z:Person)
            WHERE x.name = 'Alice' AND z.name = 'Charlie'
            RETURN count(*) AS cnt
            """
        )
        # Alice-Bob-Charlie path exists in undirected mode
        # Should find the path
        assert results[0]["cnt"].value > 0

    def test_triadic_with_name_filter(self):
        """Friend of friend filtered by names."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}) CREATE (b)-[:KNOWS]->(c:Person {name: 'Charlie'})"
        )
        # Note: Alice and Charlie are connected through Bob

        results = gf.execute(
            """
            MATCH (x:Person)-[:KNOWS]-(y:Person)-[:KNOWS]-(z:Person)
            WHERE x.name = 'Alice'
              AND z.name = 'Charlie'
            RETURN count(*) AS cnt
            """
        )
        # Alice-Bob-Charlie path exists in undirected mode
        assert results[0]["cnt"].value > 0

    def test_triadic_distinct_by_name(self):
        """Triadic pattern with distinct endpoint names."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}) CREATE (b)-[:KNOWS]->(c:Person {name: 'Charlie'})"
        )

        results = gf.execute(
            """
            MATCH (x:Person)-[:KNOWS]-(y:Person)-[:KNOWS]-(z:Person)
            WHERE x.name <> z.name
            RETURN DISTINCT x.name AS x_name, z.name AS z_name
            ORDER BY x_name, z_name
            """
        )
        # Should find paths between people with different names
        assert len(results) >= 2
