"""Integration tests for OPTIONAL MATCH clause."""

from graphforge import GraphForge


class TestOptionalMatchBasic:
    """Test basic OPTIONAL MATCH functionality."""

    def test_optional_match_with_no_matches(self):
        """Test OPTIONAL MATCH when pattern doesn't match (returns NULL)."""
        gf = GraphForge()

        # Create a person with no friends
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        # OPTIONAL MATCH should return Alice with friend=NULL
        results = gf.execute("""
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[:KNOWS]->(f)
            RETURN p.name AS person, f AS friend
        """)

        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["friend"].value is None  # NULL

    def test_optional_match_with_matches(self):
        """Test OPTIONAL MATCH when pattern does match."""
        gf = GraphForge()

        # Create people with friendship (separate statements)
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )

        # OPTIONAL MATCH should return Alice with friend=Bob
        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            OPTIONAL MATCH (p)-[:KNOWS]->(f)
            RETURN p.name AS person, f.name AS friend
        """)

        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["friend"].value == "Bob"

    def test_optional_match_mixed_matches(self):
        """Test OPTIONAL MATCH with some matches and some non-matches."""
        gf = GraphForge()

        # Create people, only one has a friend (separate statements)
        gf.execute("CREATE (alice:Person {name: 'Alice'})")
        gf.execute("CREATE (bob:Person {name: 'Bob'})")
        gf.execute("CREATE (charlie:Person {name: 'Charlie'})")
        gf.execute(
            "MATCH (alice:Person {name: 'Alice'}), (bob:Person {name: 'Bob'}) CREATE (alice)-[:KNOWS]->(bob)"
        )

        # OPTIONAL MATCH should return all people, with NULL for those without friends
        results = gf.execute("""
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[:KNOWS]->(f)
            RETURN p.name AS person, f.name AS friend
            ORDER BY p.name
        """)

        assert len(results) == 3

        # Alice has a friend (Bob)
        assert results[0]["person"].value == "Alice"
        assert results[0]["friend"].value == "Bob"

        # Bob has no friends
        assert results[1]["person"].value == "Bob"
        assert results[1]["friend"].value is None  # NULL

        # Charlie has no friends
        assert results[2]["person"].value == "Charlie"
        assert results[2]["friend"].value is None  # NULL

    def test_optional_match_multiple_relationships(self):
        """Test OPTIONAL MATCH with multiple relationships from same node."""
        gf = GraphForge()

        # Create person with two friends (separate statements)
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)"
        )

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            OPTIONAL MATCH (p)-[:KNOWS]->(f)
            RETURN p.name AS person, f.name AS friend
            ORDER BY friend
        """)

        assert len(results) == 2
        assert results[0]["person"].value == "Alice"
        assert results[0]["friend"].value == "Bob"
        assert results[1]["person"].value == "Alice"
        assert results[1]["friend"].value == "Charlie"


class TestOptionalMatchNullHandling:
    """Test NULL propagation in OPTIONAL MATCH."""

    def test_optional_match_null_in_where(self):
        """Test that NULL from OPTIONAL MATCH works in WHERE clauses."""
        gf = GraphForge()

        # Create people (separate statements)
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:KNOWS]->(c)"
        )

        # Get people who don't have friends (NULL from OPTIONAL MATCH)
        results = gf.execute("""
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[:KNOWS]->(f)
            WHERE f IS NULL
            RETURN p.name AS person
        """)

        assert len(results) == 1
        assert results[0]["person"].value == "Alice"

    def test_optional_match_null_in_aggregation(self):
        """Test that NULL from OPTIONAL MATCH is excluded from aggregation."""
        gf = GraphForge()

        # Create people (separate statements)
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )

        # Count friends (should exclude NULL)
        results = gf.execute("""
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[:KNOWS]->(f)
            RETURN COUNT(f) AS friendCount
        """)

        assert len(results) == 1
        assert results[0]["friendCount"].value == 1  # Only Bob, NULL excluded
