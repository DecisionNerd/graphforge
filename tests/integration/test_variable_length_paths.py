"""Integration tests for variable-length path patterns."""

from graphforge import GraphForge


class TestVariableLengthBasic:
    """Test basic variable-length path functionality."""

    def test_simple_variable_length_unbounded(self):
        """Test unbounded variable-length pattern: *"""
        gf = GraphForge()

        # Create a chain: A -> B -> C
        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        # Match variable-length paths from A
        results = gf.execute("""
            MATCH (p:Person {name: 'A'})-[:KNOWS*]->(f)
            RETURN f.name AS name
        """)

        # Should find B and C
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"B", "C"}

    def test_variable_length_with_min_max(self):
        """Test variable-length with min and max: *1..2"""
        gf = GraphForge()

        # Create a longer chain: A -> B -> C -> D
        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")
        d = gf.create_node(["Person"], name="D")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")
        gf.create_relationship(c, d, "KNOWS")

        # Match paths of length 1..2 from A
        results = gf.execute("""
            MATCH (p:Person {name: 'A'})-[:KNOWS*1..2]->(f)
            RETURN f.name AS name
        """)

        # Should find B (1 hop) and C (2 hops), but not D (3 hops)
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"B", "C"}
