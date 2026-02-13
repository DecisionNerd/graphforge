"""Integration tests for OPTIONAL MATCH followed by DELETE."""

from graphforge import GraphForge


class TestOptionalMatchDelete:
    """Test DELETE after OPTIONAL MATCH - natural query syntax."""

    def test_optional_match_delete_with_null(self):
        """OPTIONAL MATCH that returns NULL, followed by DELETE."""
        gf = GraphForge()

        # Create a person with no friends
        gf.execute("CREATE (:Person {name: 'Alice'})")

        # OPTIONAL MATCH returns NULL for friend, DELETE should skip NULL
        gf.execute(
            """
            OPTIONAL MATCH (p:Person)-[:KNOWS]->(friend)
            DELETE friend
        """
        )

        # Alice should still exist (friend was NULL)
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_optional_match_delete_with_match(self):
        """OPTIONAL MATCH that finds matches, followed by DELETE."""
        gf = GraphForge()

        # Create person with friend
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        # OPTIONAL MATCH finds Bob, DETACH DELETE removes him and relationship
        gf.execute(
            """
            OPTIONAL MATCH (p:Person {name: 'Alice'})-[:KNOWS]->(friend)
            DETACH DELETE friend
        """
        )

        # Only Alice should remain
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_match_optional_match_delete(self):
        """MATCH followed by OPTIONAL MATCH and DELETE."""
        gf = GraphForge()

        # Create two people, one with friend
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})-[:KNOWS]->(:Person {name: 'Charlie'})")

        # Match all people, optionally match their friends, detach delete friends
        gf.execute(
            """
            MATCH (p:Person)
            OPTIONAL MATCH (p)-[:KNOWS]->(friend)
            DETACH DELETE friend
        """
        )

        # Alice and Bob remain, Charlie deleted
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY name")
        assert len(result) == 2
        assert result[0]["name"].value == "Alice"
        assert result[1]["name"].value == "Bob"

    def test_optional_match_detach_delete(self):
        """OPTIONAL MATCH followed by DETACH DELETE."""
        gf = GraphForge()

        # Create person with friend
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        # Delete Bob with DETACH DELETE
        gf.execute(
            """
            OPTIONAL MATCH (p:Person {name: 'Bob'})
            DETACH DELETE p
        """
        )

        # Only Alice should remain
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_optional_match_where_delete(self):
        """OPTIONAL MATCH with WHERE followed by DELETE."""
        gf = GraphForge()

        # Create people with different ages
        gf.execute("CREATE (:Person {name: 'Alice', age: 25})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 35})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 45})")

        # Delete people over 30
        gf.execute(
            """
            OPTIONAL MATCH (p:Person)
            WHERE p.age > 30
            DELETE p
        """
        )

        # Only Alice should remain
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_optional_match_delete_multiple_variables(self):
        """OPTIONAL MATCH pattern with DELETE on multiple variables."""
        gf = GraphForge()

        # Create simple pattern
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")

        # Delete both the relationship and Bob
        gf.execute(
            """
            OPTIONAL MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
            DETACH DELETE r, b
        """
        )

        # Only Alice should remain
        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

        # No relationships should remain
        rels = gf.execute("MATCH ()-[r]->() RETURN r")
        assert len(rels) == 0

    def test_optional_match_delete_with_return(self):
        """OPTIONAL MATCH + DELETE + RETURN."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice', age: 25})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 35})")

        # Count people before deletion
        before = gf.execute("MATCH (n:Person) RETURN count(*) AS count")
        assert before[0]["count"].value == 2

        # Delete Bob using OPTIONAL MATCH + DELETE
        gf.execute(
            """
            OPTIONAL MATCH (p:Person {name: 'Bob'})
            DELETE p
        """
        )

        # Verify only Alice remains
        remaining = gf.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(remaining) == 1
        assert remaining[0]["name"].value == "Alice"

    def test_no_workaround_needed_anymore(self):
        """Verify we don't need WITH workaround anymore."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")

        # This now works directly without WITH clause
        gf.execute(
            """
            OPTIONAL MATCH (p:Person)-[:KNOWS]->(friend)
            DELETE friend
        """
        )

        # Alice should still exist
        result = gf.execute("MATCH (n:Person) RETURN n")
        assert len(result) == 1
