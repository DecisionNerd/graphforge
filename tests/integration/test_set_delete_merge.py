"""Integration tests for SET, DELETE, and MERGE clauses.

Tests the ability to update, delete, and merge nodes using Cypher syntax.
"""

from graphforge import GraphForge


class TestSetClause:
    """Tests for SET clause."""

    def test_set_single_property(self):
        """SET a single property on a node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 25})")
        gf.execute("MATCH (n:Person) SET n.age = 30")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30

    def test_set_multiple_properties(self):
        """SET multiple properties on a node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 25})")
        gf.execute("MATCH (n:Person) SET n.age = 30, n.city = 'NYC'")

        results = gf.execute("MATCH (p:Person) RETURN p.age AS age, p.city AS city")
        assert results[0]["age"].value == 30
        assert results[0]["city"].value == "NYC"

    def test_set_with_where(self):
        """SET property on specific nodes."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice', age: 25})")
        gf.execute("CREATE (b:Person {name: 'Bob', age: 25})")
        gf.execute("MATCH (n:Person) WHERE n.name = 'Alice' SET n.age = 30")

        results = gf.execute("MATCH (p:Person) WHERE p.name = 'Alice' RETURN p.age AS age")
        assert results[0]["age"].value == 30

        results = gf.execute("MATCH (p:Person) WHERE p.name = 'Bob' RETURN p.age AS age")
        assert results[0]["age"].value == 25

    def test_set_on_relationship(self):
        """SET property on a relationship."""
        gf = GraphForge()
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[r:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})"
        )
        gf.execute("MATCH (a)-[r:KNOWS]->(b) SET r.since = 2021")

        results = gf.execute("MATCH (a)-[r:KNOWS]->(b) RETURN r.since AS since")
        assert results[0]["since"].value == 2021


class TestDeleteClause:
    """Tests for DELETE clause."""

    def test_delete_single_node(self):
        """DELETE a single node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice'})")
        gf.execute("CREATE (n:Person {name: 'Bob'})")

        gf.execute("MATCH (n:Person) WHERE n.name = 'Alice' DELETE n")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_delete_all_nodes(self):
        """DELETE all nodes."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Person {name: 'Bob'})")
        gf.execute("CREATE (c:Person {name: 'Charlie'})")

        gf.execute("MATCH (n:Person) DELETE n")

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 0

    def test_delete_relationship(self):
        """DELETE a relationship."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})")

        gf.execute("MATCH (a)-[r:KNOWS]->(b) DELETE r")

        # Nodes should still exist
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 2

        # But relationship should be gone
        results = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(*) AS count")
        assert results[0]["count"].value == 0

    def test_delete_node_and_relationships(self):
        """DELETE a node and its relationships."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r1:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r2:LIKES]->(c:Person {name: 'Charlie'})")

        # Delete Alice (should also delete connected edges)
        gf.execute("MATCH (n:Person) WHERE n.name = 'Alice' DELETE n")

        # Alice should be gone
        results = gf.execute("MATCH (p:Person) WHERE p.name = 'Alice' RETURN count(*) AS count")
        assert results[0]["count"].value == 0

        # Bob and Charlie should remain
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 2

        # Relationships should be gone
        results = gf.execute("MATCH ()-[r]->() RETURN count(*) AS count")
        assert results[0]["count"].value == 0


class TestMergeClause:
    """Tests for MERGE clause."""

    def test_merge_creates_new_node(self):
        """MERGE creates a new node if it doesn't exist."""
        gf = GraphForge()
        gf.execute("MERGE (n:Person {name: 'Alice'})")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_merge_matches_existing_node(self):
        """MERGE matches an existing node if it exists."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice'})")
        gf.execute("MERGE (n:Person {name: 'Alice'})")

        # Should still only have one node
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

    def test_merge_creates_if_different_property(self):
        """MERGE creates a new node if properties differ."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30})")
        gf.execute("MERGE (n:Person {name: 'Alice', age: 25})")

        # Should have two nodes (different ages)
        results = gf.execute("MATCH (p:Person) WHERE p.name = 'Alice' RETURN count(*) AS count")
        assert results[0]["count"].value == 2

    def test_merge_with_multiple_properties(self):
        """MERGE with multiple properties."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30, city: 'NYC'})")
        gf.execute("MERGE (n:Person {name: 'Alice', age: 30, city: 'NYC'})")

        # Should match existing node
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

    def test_merge_with_return(self):
        """MERGE with RETURN clause."""
        gf = GraphForge()
        results = gf.execute("MERGE (n:Person {name: 'Alice'}) RETURN n.name AS name")

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_merge_idempotent(self):
        """MERGE is idempotent."""
        gf = GraphForge()

        # Run MERGE multiple times
        gf.execute("MERGE (n:Person {name: 'Alice'})")
        gf.execute("MERGE (n:Person {name: 'Alice'})")
        gf.execute("MERGE (n:Person {name: 'Alice'})")

        # Should still only have one node
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1


class TestSetDeleteMergeCombinations:
    """Tests combining SET, DELETE, and MERGE."""

    def test_merge_then_set(self):
        """MERGE a node then SET its properties."""
        gf = GraphForge()
        gf.execute("MERGE (n:Person {name: 'Alice'})")
        gf.execute("MATCH (n:Person {name: 'Alice'}) SET n.age = 30")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30

    def test_set_then_delete(self):
        """SET properties then DELETE the node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 25})")
        gf.execute("MATCH (n:Person) SET n.age = 30")
        gf.execute("MATCH (n:Person) DELETE n")

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 0


class TestPersistenceWithMutations:
    """Tests for mutations with persistence."""

    def test_set_persists(self):
        """SET changes persist across sessions."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: CREATE and SET
            gf1 = GraphForge(db_path)
            gf1.execute("CREATE (n:Person {name: 'Alice', age: 25})")
            gf1.execute("MATCH (n:Person) SET n.age = 30")
            gf1.close()

            # Session 2: Verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.age AS age")
            assert results[0]["age"].value == 30
            gf2.close()

    def test_delete_persists(self):
        """DELETE changes persist across sessions."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: CREATE and DELETE
            gf1 = GraphForge(db_path)
            gf1.execute("CREATE (a:Person {name: 'Alice'})")
            gf1.execute("CREATE (b:Person {name: 'Bob'})")
            gf1.execute("MATCH (n:Person) WHERE n.name = 'Alice' DELETE n")
            gf1.close()

            # Session 2: Verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Bob"
            gf2.close()

    def test_merge_persists(self):
        """MERGE changes persist across sessions."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: MERGE
            gf1 = GraphForge(db_path)
            gf1.execute("MERGE (n:Person {name: 'Alice'})")
            gf1.close()

            # Session 2: MERGE again (should match)
            gf2 = GraphForge(db_path)
            gf2.execute("MERGE (n:Person {name: 'Alice'})")
            results = gf2.execute("MATCH (p:Person) RETURN count(*) AS count")
            assert results[0]["count"].value == 1
            gf2.close()


class TestTransactionsWithMutations:
    """Tests for mutations with transactions."""

    def test_set_rollback(self):
        """SET can be rolled back."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 25})")

        gf.begin()
        gf.execute("MATCH (n:Person) SET n.age = 30")
        gf.rollback()

        results = gf.execute("MATCH (p:Person) RETURN p.age AS age")
        assert results[0]["age"].value == 25

    def test_delete_rollback(self):
        """DELETE can be rolled back."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice'})")

        gf.begin()
        gf.execute("MATCH (n:Person) DELETE n")
        gf.rollback()

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

    def test_merge_rollback(self):
        """MERGE can be rolled back."""
        gf = GraphForge()

        gf.begin()
        gf.execute("MERGE (n:Person {name: 'Alice'})")
        gf.rollback()

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 0
