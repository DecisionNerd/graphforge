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


@pytest.mark.integration
class TestExpressionToStringCoverage:
    """Test coverage for _expression_to_string() helper."""

    def test_literal_values_as_column_names(self):
        """Test that literal values get properly formatted as column names."""
        gf = GraphForge()

        # Test various literal types
        results = gf.execute("""
            RETURN
                null,
                true,
                false,
                42,
                3.14,
                'hello',
                [1, 2, 3],
                {name: 'Alice', age: 30}
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have descriptive column names for literals
        assert "null" in keys
        assert "true" in keys
        assert "false" in keys
        assert "42" in keys
        assert "3.14" in keys
        assert "'hello'" in keys
        assert any("[" in k for k in keys)  # List literal
        assert any("{" in k for k in keys)  # Map literal

    def test_binary_operations_as_column_names(self):
        """Test that binary operations get formatted as column names."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {age: 30})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.age + 5, p.age * 2, p.age > 25
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have parenthesized expressions
        assert any("+" in k and "(" in k for k in keys)
        assert any("*" in k and "(" in k for k in keys)
        assert any(">" in k and "(" in k for k in keys)

    def test_unary_operations_as_column_names(self):
        """Test that unary operations get formatted as column names."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {age: 30, active: true})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN NOT p.active, -p.age, p.age IS NULL, p.age IS NOT NULL
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have unary operation names
        assert any("NOT" in k for k in keys)
        assert any("-" in k for k in keys)
        assert any("IS NULL" in k for k in keys)
        assert any("IS NOT NULL" in k for k in keys)

    def test_distinct_function_as_column_name(self):
        """Test that DISTINCT functions get formatted correctly."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {age: 30})")
        gf.execute("CREATE (:Person {age: 30})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN count(DISTINCT p.age)
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have DISTINCT in the column name
        assert any("DISTINCT" in k for k in keys)

    def test_list_and_map_literals_with_nulls_and_bools(self):
        """Test list/map literals containing null and bool values."""
        gf = GraphForge()

        # Test list with null and bool items
        results = gf.execute("""
            RETURN [null, true, false, 1, 'test'] AS list_col,
                   {a: null, b: true, c: false, d: 42} AS map_col
        """)

        assert len(results) == 1
        keys = list(results[0].keys())

        # Should have formatted column names
        assert "list_col" in keys
        assert "map_col" in keys

        # Verify values were processed correctly
        list_val = results[0]["list_col"]
        map_val = results[0]["map_col"]
        assert len(list_val.value) == 5
        assert len(map_val.value) == 4
