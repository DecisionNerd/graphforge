"""Integration tests for wildcard (*) execution in RETURN and WITH clauses."""

import pytest

from graphforge.api import GraphForge
from graphforge.types.values import CypherInt, CypherString


class TestWildcardExecution:
    """Test execution of * wildcard in queries."""

    @pytest.fixture
    def graph(self):
        """Create a graph with test data."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (b:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (c:Person {name: 'Charlie', age: 35})")
        return gf

    def test_return_wildcard_all_variables(self, graph):
        """Test RETURN * returns all bound variables."""
        results = graph.execute("MATCH (p:Person) RETURN *")

        # Should return all matched nodes
        assert len(results) == 3
        # Each result should have 'p' variable
        for result in results:
            assert "p" in result
            assert result["p"].labels == {"Person"}

    def test_with_wildcard_passthrough(self, graph):
        """Test WITH * passes all variables through."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *
            RETURN p.name AS name
        """)

        # Should pass through all 3 people
        assert len(results) == 3
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_with_wildcard_and_filter(self, graph):
        """Test WITH * WHERE filters correctly."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *
            WHERE p.age > 25
            RETURN p.name AS name
        """)

        # Should filter to Alice and Charlie
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Charlie"}

    def test_with_wildcard_and_additional_column(self, graph):
        """Test WITH * plus additional expressions."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *, p.age * 2 AS double_age
            RETURN p.name AS name, double_age
        """)

        # Should have all 3 people with doubled ages
        assert len(results) == 3
        for result in results:
            assert "name" in result
            assert "double_age" in result
            # Verify doubling logic
            if result["name"].value == "Alice":
                assert result["double_age"].value == 60
            elif result["name"].value == "Bob":
                assert result["double_age"].value == 50
            elif result["name"].value == "Charlie":
                assert result["double_age"].value == 70

    def test_create_with_wildcard(self, graph):
        """Test CREATE followed by WITH *."""
        results = graph.execute("""
            CREATE (x:Test {value: 42})
            WITH *
            RETURN x.value AS value
        """)

        assert len(results) == 1
        assert results[0]["value"].value == 42

    def test_with_wildcard_order_by(self, graph):
        """Test WITH * ORDER BY."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *
            ORDER BY p.age
            RETURN p.name AS name, p.age AS age
        """)

        # Should be ordered by age: Bob (25), Alice (30), Charlie (35)
        assert len(results) == 3
        assert results[0]["name"].value == "Bob"
        assert results[1]["name"].value == "Alice"
        assert results[2]["name"].value == "Charlie"

    def test_with_wildcard_limit(self, graph):
        """Test WITH * LIMIT."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *
            LIMIT 2
            RETURN p.name AS name
        """)

        # Should limit to 2 results
        assert len(results) == 2

    def test_multiple_with_wildcards(self, graph):
        """Test multiple WITH * clauses in sequence."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *
            WHERE p.age >= 30
            WITH *
            ORDER BY p.age DESC
            RETURN p.name AS name
        """)

        # Should filter and order correctly
        assert len(results) == 2
        # Charlie (35) should come before Alice (30)
        assert results[0]["name"].value == "Charlie"
        assert results[1]["name"].value == "Alice"

    def test_with_wildcard_preserves_all_variables(self, graph):
        """Test WITH * preserves multiple bound variables."""
        results = graph.execute("""
            MATCH (p1:Person), (p2:Person)
            WHERE p1.age < p2.age
            WITH *
            RETURN p1.name AS name1, p2.name AS name2
        """)

        # Should have all valid pairs where age1 < age2
        # Bob < Alice, Bob < Charlie, Alice < Charlie = 3 pairs
        assert len(results) == 3

    def test_with_wildcard_empty_context(self):
        """Test WITH * with no prior variables."""
        gf = GraphForge()
        # WITH * at query start should work but pass empty context
        results = gf.execute("WITH * RETURN 1 AS x")
        assert len(results) == 1
        assert results[0]["x"].value == 1

    def test_return_wildcard_with_relationship(self):
        """Test RETURN * includes both nodes and relationships."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")

        results = gf.execute("MATCH (a)-[r]->(b) RETURN *")

        assert len(results) == 1
        # Should have a, r, and b all bound
        result = results[0]
        assert "a" in result
        assert "r" in result
        assert "b" in result

    def test_with_wildcard_skip(self, graph):
        """Test WITH * SKIP."""
        results = graph.execute("""
            MATCH (p:Person)
            WITH *
            ORDER BY p.age
            SKIP 1
            RETURN p.name AS name
        """)

        # Should skip first (Bob) and return Alice and Charlie
        assert len(results) == 2
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Charlie"}
