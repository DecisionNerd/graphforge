"""Integration tests for column naming with complex expressions."""

import pytest

from graphforge import GraphForge


@pytest.mark.integration
class TestColumnNaming:
    """Test column naming for expressions without aliases."""

    def test_unique_column_names_for_case_expressions(self):
        """Test that multiple CASE expressions get unique column names."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")

        # Multiple CASE expressions without aliases should have unique names
        results = gf.execute("""
            MATCH (p:Person)
            RETURN
                CASE WHEN p.age > 25 THEN 'old' ELSE 'young' END,
                CASE WHEN p.age < 50 THEN 'middle' ELSE 'senior' END
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have 2 unique column names
        assert len(keys) == 2
        assert len(set(keys)) == 2, f"Duplicate column names found: {keys}"

        # Names should include indices for uniqueness
        assert "CASE ... END_0" in keys
        assert "CASE ... END_1" in keys

    def test_unique_column_names_for_list_comprehensions(self):
        """Test that multiple list comprehensions get unique column names."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', scores: [1, 2, 3]})")

        # Multiple list comprehensions without aliases should have unique names
        results = gf.execute("""
            MATCH (p:Person)
            RETURN
                [x IN p.scores WHERE x > 1 | x * 2],
                [x IN p.scores WHERE x < 3 | x + 10]
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have 2 unique column names
        assert len(keys) == 2
        assert len(set(keys)) == 2, f"Duplicate column names found: {keys}"

        # Names should include indices for uniqueness
        assert "[...]_0" in keys
        assert "[...]_1" in keys

    def test_mixed_complex_expressions(self):
        """Test unique names for mixed complex expression types."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30, scores: [1, 2, 3]})")

        # Mix of different complex expression types
        results = gf.execute("""
            MATCH (p:Person)
            RETURN
                CASE WHEN p.age > 25 THEN 'old' END,
                [x IN p.scores WHERE x > 1 | x * 2],
                ANY(x IN p.scores WHERE x > 2)
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have 3 unique column names
        assert len(keys) == 3
        assert len(set(keys)) == 3, f"Duplicate column names found: {keys}"

    def test_simple_expressions_unchanged(self):
        """Test that simple expressions still get descriptive names."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name, p.age, labels(p)
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Simple expressions should have descriptive names
        assert "p.name" in keys
        assert "p.age" in keys
        assert "labels(p)" in keys
