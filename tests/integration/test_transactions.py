"""Integration tests for transaction support.

Tests ACID transaction semantics with begin/commit/rollback.
"""

from pathlib import Path
import tempfile

import pytest

from graphforge import GraphForge


class TestBasicTransactions:
    """Tests for basic transaction operations."""

    def test_begin_commit_in_memory(self):
        """Begin and commit a transaction in memory."""
        gf = GraphForge()

        gf.begin()
        gf.create_node(["Person"], name="Alice")
        gf.commit()

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_begin_rollback_in_memory(self):
        """Begin and rollback a transaction in memory."""
        gf = GraphForge()

        # Create initial node
        gf.create_node(["Person"], name="Alice")

        # Start transaction and add another node
        gf.begin()
        gf.create_node(["Person"], name="Bob")

        # Bob should exist before rollback
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
        assert len(results) == 2

        # Rollback
        gf.rollback()

        # Only Alice should remain
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_begin_commit_persistent(self):
        """Begin and commit a transaction with persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            gf = GraphForge(db_path)
            gf.begin()
            gf.create_node(["Person"], name="Alice")
            gf.commit()
            gf.close()

            # Reload and verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"
            gf2.close()

    def test_begin_rollback_persistent(self):
        """Begin and rollback a transaction with persistence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: Create Alice
            gf1 = GraphForge(db_path)
            gf1.create_node(["Person"], name="Alice")
            gf1.close()

            # Session 2: Try to add Bob but rollback
            gf2 = GraphForge(db_path)
            gf2.begin()
            gf2.create_node(["Person"], name="Bob")
            gf2.rollback()
            gf2.close()

            # Session 3: Verify only Alice exists
            gf3 = GraphForge(db_path)
            results = gf3.execute("MATCH (p:Person) RETURN p.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"
            gf3.close()


class TestMultipleOperations:
    """Tests for transactions with multiple operations."""

    def test_rollback_multiple_nodes(self):
        """Rollback transaction with multiple node creations."""
        gf = GraphForge()

        # Initial state
        gf.create_node(["Person"], name="Alice")

        # Transaction with multiple adds
        gf.begin()
        gf.create_node(["Person"], name="Bob")
        gf.create_node(["Person"], name="Charlie")
        gf.create_node(["Person"], name="Dave")
        gf.rollback()

        # Should only have Alice
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_commit_multiple_nodes(self):
        """Commit transaction with multiple node creations."""
        gf = GraphForge()

        gf.begin()
        gf.create_node(["Person"], name="Alice")
        gf.create_node(["Person"], name="Bob")
        gf.create_node(["Person"], name="Charlie")
        gf.commit()

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 3

    def test_rollback_nodes_and_relationships(self):
        """Rollback transaction with nodes and relationships."""
        gf = GraphForge()

        # Initial state
        alice = gf.create_node(["Person"], name="Alice")

        # Transaction
        gf.begin()
        bob = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(alice, bob, "KNOWS", since=2020)
        gf.rollback()

        # Bob and relationship should be gone
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

        results = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(*) AS count")
        assert results[0]["count"].value == 0


class TestTransactionErrors:
    """Tests for transaction error handling."""

    def test_commit_without_begin_raises_error(self):
        """Committing without begin() raises error."""
        gf = GraphForge()

        with pytest.raises(RuntimeError, match="Not in a transaction"):
            gf.commit()

    def test_rollback_without_begin_raises_error(self):
        """Rolling back without begin() raises error."""
        gf = GraphForge()

        with pytest.raises(RuntimeError, match="Not in a transaction"):
            gf.rollback()

    def test_nested_begin_raises_error(self):
        """Nested begin() raises error."""
        gf = GraphForge()

        gf.begin()
        with pytest.raises(RuntimeError, match="Already in a transaction"):
            gf.begin()

        # Cleanup
        gf.rollback()

    def test_begin_after_commit_works(self):
        """Can begin new transaction after commit."""
        gf = GraphForge()

        gf.begin()
        gf.create_node(["Person"], name="Alice")
        gf.commit()

        # Should be able to start new transaction
        gf.begin()
        gf.create_node(["Person"], name="Bob")
        gf.commit()

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 2

    def test_begin_after_rollback_works(self):
        """Can begin new transaction after rollback."""
        gf = GraphForge()

        gf.begin()
        gf.create_node(["Person"], name="Alice")
        gf.rollback()

        # Should be able to start new transaction
        gf.begin()
        gf.create_node(["Person"], name="Bob")
        gf.commit()

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"


class TestAutoCommit:
    """Tests for auto-commit behavior."""

    def test_close_auto_commits_transaction(self):
        """close() automatically commits pending transaction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            gf1 = GraphForge(db_path)
            gf1.begin()
            gf1.create_node(["Person"], name="Alice")
            gf1.close()  # Should auto-commit

            # Verify committed
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"
            gf2.close()

    def test_operations_without_transaction_persist(self):
        """Operations outside transactions still work with close()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            gf1 = GraphForge(db_path)
            gf1.create_node(["Person"], name="Alice")  # No explicit transaction
            gf1.close()

            # Verify persisted
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"
            gf2.close()


class TestComplexTransactions:
    """Tests for complex transaction scenarios."""

    def test_multiple_transactions_sequential(self):
        """Multiple sequential transactions work correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            gf = GraphForge(db_path)

            # Transaction 1
            gf.begin()
            gf.create_node(["Person"], name="Alice")
            gf.commit()

            # Transaction 2
            gf.begin()
            gf.create_node(["Person"], name="Bob")
            gf.commit()

            # Transaction 3 (rollback)
            gf.begin()
            gf.create_node(["Person"], name="Charlie")
            gf.rollback()

            gf.close()

            # Verify: Alice and Bob, no Charlie
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
            assert len(results) == 2
            names = [r["name"].value for r in results]
            assert names == ["Alice", "Bob"]
            gf2.close()

    def test_rollback_preserves_pre_transaction_state(self):
        """Rollback restores state from before transaction began."""
        gf = GraphForge()

        # Initial state: 3 nodes
        gf.create_node(["Person"], name="Alice", age=30)
        gf.create_node(["Person"], name="Bob", age=25)
        gf.create_node(["Person"], name="Charlie", age=35)

        # Transaction: try to add 2 more
        gf.begin()
        gf.create_node(["Person"], name="Dave", age=40)
        gf.create_node(["Person"], name="Eve", age=28)

        # Verify all 5 exist
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 5

        # Rollback
        gf.rollback()

        # Should be back to 3
        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 3

        # Verify original nodes still have their properties
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name = 'Alice'
            RETURN p.age AS age
        """)
        assert results[0]["age"].value == 30

    def test_queries_within_transaction(self):
        """Queries see uncommitted changes within transaction."""
        gf = GraphForge()

        gf.create_node(["Person"], name="Alice")

        gf.begin()
        gf.create_node(["Person"], name="Bob")

        # Query within transaction should see Bob
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
        assert len(results) == 2
        names = [r["name"].value for r in results]
        assert names == ["Alice", "Bob"]

        gf.rollback()

        # Query after rollback should not see Bob
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
