"""Integration tests for DELETE with NULL-bound variables."""

from graphforge import GraphForge


class TestDeleteNull:
    """Test DELETE behavior with NULL values from OPTIONAL MATCH via WITH clause."""

    def test_delete_null_via_with_clause(self):
        """DELETE NULL carried through WITH should be silently skipped."""
        gf = GraphForge()

        # Create a person with no friends
        gf.execute("CREATE (:Person {name: 'Alice'})")

        # OPTIONAL MATCH returns NULL for friend, WITH carries it, then match and delete
        # This should NOT error - NULL is silently skipped
        gf.execute("""
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[:KNOWS]->(friend)
            WITH friend
            MATCH (x:Person)
            DELETE friend
        """)

        # Alice should still exist
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_delete_null_and_valid_node_together(self):
        """DELETE with both NULL and valid node reference."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        # Match Alice (no friends, NULL) and Bob to delete
        # Both in DELETE but only Bob should be deleted
        gf.execute("""
            MATCH (alice:Person {name: 'Alice'})
            OPTIONAL MATCH (alice)-[:KNOWS]->(friend)
            WITH alice, friend
            MATCH (bob:Person {name: 'Bob'})
            DELETE friend, bob
        """)

        # Only Alice should remain
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_detach_delete_null_via_with(self):
        """DETACH DELETE NULL should also skip NULL values."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})-[:KNOWS]->(:Person {name: 'Charlie'})")

        # Get NULL from Alice's non-existent friend, then try to DETACH DELETE it
        gf.execute("""
            MATCH (alice:Person {name: 'Alice'})
            OPTIONAL MATCH (alice)-[:KNOWS]->(friend)
            WITH friend
            MATCH (bob:Person {name: 'Bob'})
            DETACH DELETE friend, bob
        """)

        # Alice and Charlie should remain
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY name")
        assert len(result) == 2
        assert result[0]["name"].value == "Alice"
        assert result[1]["name"].value == "Charlie"
