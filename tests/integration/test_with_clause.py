"""Integration tests for WITH clause.

The WITH clause enables query chaining, allowing you to:
- Pass results from one part of a query to another
- Filter intermediate results with WHERE
- Aggregate before continuing the query
- Order and limit intermediate results
"""

import pytest

from graphforge import GraphForge


class TestWithBasics:
    """Test basic WITH clause functionality."""

    def test_with_simple_projection(self, tmp_path):
        """WITH should pass through selected variables."""
        db = GraphForge(tmp_path / "test.db")

        # Create test data
        db.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        db.execute("CREATE (p:Person {name: 'Bob', age: 25})")

        # Query with WITH
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            RETURN name, age
            ORDER BY name
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[1]["name"].value == "Bob"
        assert results[1]["age"].value == 25

        db.close()

    def test_with_renaming_variables(self, tmp_path):
        """WITH should allow renaming variables."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice'})")

        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS person_name
            RETURN person_name
        """)

        assert len(results) == 1
        assert results[0]["person_name"].value == "Alice"

        db.close()

    def test_with_limits_available_variables(self, tmp_path):
        """WITH should only pass through specified variables."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice', age: 30, city: 'NYC'})")

        # Only pass name and age through WITH
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            RETURN name, age
        """)

        assert len(results) == 1
        assert "name" in results[0]
        assert "age" in results[0]
        assert len(results[0]) == 2  # Only name and age

        db.close()


class TestWithFiltering:
    """Test WITH clause with WHERE filtering."""

    def test_with_where_filter(self, tmp_path):
        """WITH should support WHERE filtering on intermediate results."""
        db = GraphForge(tmp_path / "test.db")

        # Create test data
        db.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        db.execute("CREATE (p:Person {name: 'Bob', age: 25})")
        db.execute("CREATE (p:Person {name: 'Charlie', age: 35})")

        # Filter after WITH
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            WHERE age > 28
            RETURN name, age
            ORDER BY name
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

        db.close()

    def test_with_where_on_computed_value(self, tmp_path):
        """WITH should allow filtering on computed values."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice', score: 95})")
        db.execute("CREATE (p:Person {name: 'Bob', score: 75})")
        db.execute("CREATE (p:Person {name: 'Charlie', score: 85})")

        # Compute value, then filter
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.score AS score
            WHERE score >= 85
            RETURN name, score
            ORDER BY score DESC
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[0]["score"].value == 95
        assert results[1]["name"].value == "Charlie"
        assert results[1]["score"].value == 85

        db.close()


class TestWithAggregation:
    """Test WITH clause with aggregation."""

    def test_with_count_aggregation(self, tmp_path):
        """WITH should support count aggregation."""
        db = GraphForge(tmp_path / "test.db")

        # Create test data
        db.execute("CREATE (a:Person {name: 'Alice', city: 'NYC'})")
        db.execute("CREATE (b:Person {name: 'Bob', city: 'NYC'})")
        db.execute("CREATE (c:Person {name: 'Charlie', city: 'LA'})")

        # Aggregate by city
        results = db.execute("""
            MATCH (p:Person)
            WITH p.city AS city, count(*) AS population
            RETURN city, population
            ORDER BY population DESC
        """)

        assert len(results) == 2
        assert results[0]["city"].value == "NYC"
        assert results[0]["population"].value == 2
        assert results[1]["city"].value == "LA"
        assert results[1]["population"].value == 1

        db.close()

    def test_with_filter_after_aggregation(self, tmp_path):
        """WITH should allow filtering aggregated results."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (a:Person {city: 'NYC'})")
        db.execute("CREATE (b:Person {city: 'NYC'})")
        db.execute("CREATE (c:Person {city: 'LA'})")
        db.execute("CREATE (d:Person {city: 'SF'})")

        # Aggregate then filter
        results = db.execute("""
            MATCH (p:Person)
            WITH p.city AS city, count(*) AS count
            WHERE count > 1
            RETURN city, count
        """)

        assert len(results) == 1
        assert results[0]["city"].value == "NYC"
        assert results[0]["count"].value == 2

        db.close()


class TestWithOrdering:
    """Test WITH clause with ORDER BY."""

    def test_with_order_by(self, tmp_path):
        """WITH should support ORDER BY."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Charlie', age: 35})")
        db.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        db.execute("CREATE (p:Person {name: 'Bob', age: 25})")

        # Order intermediate results
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            ORDER BY age DESC
            RETURN name, age
        """)

        assert len(results) == 3
        assert results[0]["name"].value == "Charlie"
        assert results[1]["name"].value == "Alice"
        assert results[2]["name"].value == "Bob"

        db.close()

    def test_with_order_by_then_limit(self, tmp_path):
        """WITH should support ORDER BY with LIMIT."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice', score: 95})")
        db.execute("CREATE (p:Person {name: 'Bob', score: 75})")
        db.execute("CREATE (p:Person {name: 'Charlie', score: 85})")
        db.execute("CREATE (p:Person {name: 'Diana', score: 90})")

        # Get top 2 by score
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.score AS score
            ORDER BY score DESC
            LIMIT 2
            RETURN name, score
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[0]["score"].value == 95
        assert results[1]["name"].value == "Diana"
        assert results[1]["score"].value == 90

        db.close()


class TestWithPagination:
    """Test WITH clause with SKIP and LIMIT."""

    def test_with_limit(self, tmp_path):
        """WITH should support LIMIT."""
        db = GraphForge(tmp_path / "test.db")

        for i in range(5):
            db.execute(f"CREATE (p:Person {{id: {i}}})")

        results = db.execute("""
            MATCH (p:Person)
            WITH p.id AS id
            ORDER BY id
            LIMIT 3
            RETURN id
        """)

        assert len(results) == 3

        db.close()

    def test_with_skip(self, tmp_path):
        """WITH should support SKIP."""
        db = GraphForge(tmp_path / "test.db")

        for i in range(5):
            db.execute(f"CREATE (p:Person {{id: {i}}})")

        results = db.execute("""
            MATCH (p:Person)
            WITH p.id AS id
            ORDER BY id
            SKIP 2
            RETURN id
        """)

        assert len(results) == 3
        assert results[0]["id"].value == 2

        db.close()

    def test_with_skip_and_limit(self, tmp_path):
        """WITH should support both SKIP and LIMIT for pagination."""
        db = GraphForge(tmp_path / "test.db")

        for i in range(10):
            db.execute(f"CREATE (p:Person {{id: {i}}})")

        # Get page 2 (items 5-7, 3 per page)
        results = db.execute("""
            MATCH (p:Person)
            WITH p.id AS id
            ORDER BY id
            SKIP 3
            LIMIT 3
            RETURN id
        """)

        assert len(results) == 3
        assert results[0]["id"].value == 3
        assert results[1]["id"].value == 4
        assert results[2]["id"].value == 5

        db.close()


class TestWithChaining:
    """Test multi-part queries with multiple WITH clauses."""

    def test_multiple_with_clauses(self, tmp_path):
        """Should support multiple WITH clauses for complex pipelines."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice', age: 30, score: 95})")
        db.execute("CREATE (p:Person {name: 'Bob', age: 25, score: 75})")
        db.execute("CREATE (p:Person {name: 'Charlie', age: 35, score: 85})")

        # Multi-stage pipeline
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age, p.score AS score
            WHERE age > 28
            WITH name, score
            WHERE score > 80
            RETURN name, score
            ORDER BY score DESC
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

        db.close()

    def test_with_between_match_clauses(self, tmp_path):
        """WITH should work between multiple MATCH clauses."""
        db = GraphForge(tmp_path / "test.db")

        # Create people and cities
        db.execute("CREATE (alice:Person {name: 'Alice'})")
        db.execute("CREATE (bob:Person {name: 'Bob'})")
        db.execute("CREATE (nyc:City {name: 'NYC'})")
        db.execute("""
            MATCH (alice:Person {name: 'Alice'})
            MATCH (nyc:City {name: 'NYC'})
            CREATE (alice)-[:LIVES_IN]->(nyc)
        """)

        # Match, pass through WITH, match again
        results = db.execute("""
            MATCH (p:Person)
            WITH p
            MATCH (p)-[:LIVES_IN]->(c:City)
            RETURN p.name AS person, c.name AS city
        """)

        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["city"].value == "NYC"

        db.close()


class TestWithEdgeCases:
    """Test edge cases and error conditions."""

    def test_with_empty_result_set(self, tmp_path):
        """WITH should handle empty result sets."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice', age: 30})")

        # Filter that matches nothing
        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            WHERE age > 100
            RETURN name, age
        """)

        assert len(results) == 0

        db.close()

    def test_with_preserves_null_values(self, tmp_path):
        """WITH should preserve null property values."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {name: 'Alice'})")  # No age property

        results = db.execute("""
            MATCH (p:Person)
            WITH p.name AS name, p.age AS age
            RETURN name, age
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        # age should be null/None
        assert results[0]["age"].value is None

        db.close()

    def test_with_distinct_functionality(self, tmp_path):
        """WITH should support DISTINCT for deduplication."""
        db = GraphForge(tmp_path / "test.db")

        db.execute("CREATE (p:Person {city: 'NYC'})")
        db.execute("CREATE (p:Person {city: 'NYC'})")
        db.execute("CREATE (p:Person {city: 'LA'})")

        # Get distinct cities
        results = db.execute("""
            MATCH (p:Person)
            WITH DISTINCT p.city AS city
            RETURN city
            ORDER BY city
        """)

        assert len(results) == 2
        assert results[0]["city"].value == "LA"
        assert results[1]["city"].value == "NYC"

        db.close()
