"""Integration tests for SQLite backend persistence.

Tests for SQLite backend loading, saving, and edge cases.
"""

from pathlib import Path
import tempfile

from graphforge import GraphForge


class TestSQLitePersistence:
    """Tests for SQLite backend persistence."""

    def test_sqlite_persists_nodes_across_sessions(self):
        """Nodes persist across GraphForge sessions."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create nodes
            gf1 = GraphForge(db_path)
            gf1.execute("CREATE (n:Person {name: 'Alice', age: 30})")
            gf1.execute("CREATE (n:Person {name: 'Bob', age: 25})")
            gf1.close()

            # Session 2: Load and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("""
                MATCH (n:Person)
                RETURN n.name AS name, n.age AS age
                ORDER BY name
            """)
            assert len(results) == 2
            assert results[0]["name"].value == "Alice"
            assert results[0]["age"].value == 30
            assert results[1]["name"].value == "Bob"
            assert results[1]["age"].value == 25
            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()

    def test_sqlite_persists_relationships_across_sessions(self):
        """Relationships persist across GraphForge sessions."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create relationships
            gf1 = GraphForge(db_path)
            gf1.execute("""
                CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})
            """)
            gf1.close()

            # Session 2: Load and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("""
                MATCH (a)-[r:KNOWS]->(b)
                RETURN a.name AS source, b.name AS target, r.since AS since
            """)
            assert len(results) == 1
            assert results[0]["source"].value == "Alice"
            assert results[0]["target"].value == "Bob"
            assert results[0]["since"].value == 2020
            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()

    def test_sqlite_loads_incoming_relationships(self):
        """SQLite correctly loads incoming relationship adjacency."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create directed relationships
            gf1 = GraphForge(db_path)
            gf1.execute("""
                CREATE (a:Person {name: 'Alice'}),
                       (b:Person {name: 'Bob'}),
                       (c:Person {name: 'Charlie'}),
                       (a)-[:KNOWS]->(b),
                       (c)-[:KNOWS]->(b)
            """)
            gf1.close()

            # Session 2: Query incoming relationships
            gf2 = GraphForge(db_path)
            results = gf2.execute("""
                MATCH (a)<-[:KNOWS]-(b)
                WHERE a.name = 'Bob'
                RETURN b.name AS source
                ORDER BY source
            """)
            assert len(results) == 2
            sources = [r["source"].value for r in results]
            assert sources == ["Alice", "Charlie"]
            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()

    def test_sqlite_loads_outgoing_relationships(self):
        """SQLite correctly loads outgoing relationship adjacency."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create directed relationships
            gf1 = GraphForge(db_path)
            gf1.execute("""
                CREATE (a:Person {name: 'Alice'}),
                       (b:Person {name: 'Bob'}),
                       (c:Person {name: 'Charlie'}),
                       (a)-[:KNOWS]->(b),
                       (a)-[:KNOWS]->(c)
            """)
            gf1.close()

            # Session 2: Query outgoing relationships
            gf2 = GraphForge(db_path)
            results = gf2.execute("""
                MATCH (a)-[:KNOWS]->(b)
                WHERE a.name = 'Alice'
                RETURN b.name AS target
                ORDER BY target
            """)
            assert len(results) == 2
            targets = [r["target"].value for r in results]
            assert targets == ["Bob", "Charlie"]
            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()

    def test_sqlite_handles_complex_graph_persistence(self):
        """SQLite handles complex graph with multiple node/edge types."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create complex graph
            gf1 = GraphForge(db_path)
            gf1.execute("""
                CREATE (a:Person:Employee {name: 'Alice', dept: 'Engineering'}),
                       (b:Person {name: 'Bob'}),
                       (c:Company {name: 'Acme Corp'}),
                       (a)-[:WORKS_AT]->(c),
                       (b)-[:KNOWS]->(a),
                       (a)-[:MANAGES]->(b)
            """)
            gf1.close()

            # Session 2: Verify complex queries
            gf2 = GraphForge(db_path)

            # Check multi-label nodes
            results = gf2.execute("MATCH (n:Person:Employee) RETURN n.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"

            # Check different relationship types exist
            results = gf2.execute("MATCH (a)-[r:KNOWS]->(b) RETURN a, b")
            assert len(results) == 1

            results = gf2.execute("MATCH (a)-[r:MANAGES]->(b) RETURN a, b")
            assert len(results) == 1

            results = gf2.execute("MATCH (a)-[r:WORKS_AT]->(b) RETURN a, b")
            assert len(results) == 1

            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()

    def test_sqlite_persists_after_modifications(self):
        """SQLite persists data after CREATE, SET, DELETE operations."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create and modify
            gf1 = GraphForge(db_path)
            gf1.execute("CREATE (n:Person {name: 'Alice', age: 30})")
            gf1.execute("CREATE (n:Person {name: 'Bob', age: 25})")
            gf1.execute("MATCH (n:Person) WHERE n.name = 'Alice' SET n.verified = true")
            gf1.execute("MATCH (n:Person) WHERE n.name = 'Bob' DELETE n")
            gf1.close()

            # Session 2: Verify modifications persisted
            gf2 = GraphForge(db_path)

            # Alice should exist with verified property
            results = gf2.execute("""
                MATCH (n:Person {name: 'Alice'})
                RETURN n.verified AS verified
            """)
            assert len(results) == 1
            assert results[0]["verified"].value is True

            # Bob should be deleted
            results = gf2.execute("MATCH (n:Person {name: 'Bob'}) RETURN n")
            assert len(results) == 0

            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()

    def test_sqlite_handles_empty_graph_load(self):
        """SQLite handles loading an empty graph."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            db_path = tmp.name

        try:
            # Session 1: Create database but no data
            gf1 = GraphForge(db_path)
            gf1.close()

            # Session 2: Load empty graph
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (n) RETURN n")
            assert len(results) == 0
            gf2.close()
        finally:
            if Path(db_path).exists():
                Path(db_path).unlink()
