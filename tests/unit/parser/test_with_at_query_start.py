"""Unit tests for WITH clause at query start (Issue #172)."""

import pytest

from graphforge import GraphForge
from graphforge.parser.parser import parse_cypher


class TestWithAtQueryStart:
    """Test WITH clause as the first clause in a query."""

    def test_with_simple_literal_return(self):
        """Test: WITH 1 AS x RETURN x."""
        query = "WITH 1 AS x RETURN x"
        ast = parse_cypher(query)

        # Should parse as a query with WITH clause
        assert ast is not None
        # Structure: with_query -> MultiPartQuery with with_clauses and final_part
        # OR it might be structured differently - let's inspect

    def test_with_list_literal_return(self):
        """Test: WITH [1, 2, 3] AS list RETURN list."""
        query = "WITH [1, 2, 3] AS list RETURN list"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_multiple_variables(self):
        """Test: WITH 1 AS x, 2 AS y RETURN x + y."""
        query = "WITH 1 AS x, 2 AS y RETURN x + y"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_map_literal(self):
        """Test: WITH {name: 'Alice', age: 30} AS person RETURN person."""
        query = "WITH {name: 'Alice', age: 30} AS person RETURN person"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_then_match(self):
        """Test: WITH 'Alice' AS name MATCH (n:Person {name: name}) RETURN n."""
        query = "WITH 'Alice' AS name MATCH (n:Person {name: name}) RETURN n"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_then_create(self):
        """Test: WITH 'Bob' AS name CREATE (n:Person {name: name}) RETURN n."""
        query = "WITH 'Bob' AS name CREATE (n:Person {name: name}) RETURN n"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_chaining(self):
        """Test: WITH 1 AS x WITH x + 1 AS y RETURN y."""
        query = "WITH 1 AS x WITH x + 1 AS y RETURN y"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_where_clause(self):
        """Test: WITH 5 AS x WHERE x > 0 RETURN x."""
        query = "WITH 5 AS x WHERE x > 0 RETURN x"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_order_by(self):
        """Test: WITH [3, 1, 2] AS nums UNWIND nums AS n RETURN n ORDER BY n."""
        query = "WITH [3, 1, 2] AS nums UNWIND nums AS n RETURN n ORDER BY n"
        ast = parse_cypher(query)

        assert ast is not None

    def test_with_limit(self):
        """Test: WITH [1, 2, 3, 4, 5] AS nums UNWIND nums AS n RETURN n LIMIT 3."""
        query = "WITH [1, 2, 3, 4, 5] AS nums UNWIND nums AS n RETURN n LIMIT 3"
        ast = parse_cypher(query)

        assert ast is not None


class TestWithAtQueryStartExecution:
    """Integration-style tests that actually execute queries."""

    def test_execution_simple_literal(self):
        """Test execution: WITH 1 AS x RETURN x."""
        gf = GraphForge()
        result = gf.execute("WITH 1 AS x RETURN x")

        assert len(result) == 1
        assert result[0]["x"].value == 1

    def test_execution_list_literal(self):
        """Test execution: WITH [1, 2, 3] AS list RETURN list."""
        gf = GraphForge()
        result = gf.execute("WITH [1, 2, 3] AS list RETURN list")

        assert len(result) == 1
        # Lists contain CypherValue objects, not raw Python values
        assert len(result[0]["list"].value) == 3
        assert result[0]["list"].value[0].value == 1
        assert result[0]["list"].value[1].value == 2
        assert result[0]["list"].value[2].value == 3

    def test_execution_multiple_variables(self):
        """Test execution: WITH 1 AS x, 2 AS y RETURN x + y AS sum."""
        gf = GraphForge()
        result = gf.execute("WITH 1 AS x, 2 AS y RETURN x + y AS sum")

        assert len(result) == 1
        assert result[0]["sum"].value == 3

    def test_execution_with_match(self):
        """Test execution: WITH 'Alice' AS name MATCH (n:Person {name: name}) RETURN n."""
        gf = GraphForge()
        # Create test data
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        # Query with WITH at start
        result = gf.execute(
            "WITH 'Alice' AS name MATCH (n:Person {name: name}) RETURN n.name AS name"
        )

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_execution_with_create(self):
        """Test execution: WITH 'Charlie' AS name CREATE (n:Person {name: name}) RETURN n."""
        gf = GraphForge()
        result = gf.execute(
            "WITH 'Charlie' AS name CREATE (n:Person {name: name}) RETURN n.name AS name"
        )

        assert len(result) == 1
        assert result[0]["name"].value == "Charlie"

        # Verify it was created
        verify = gf.execute("MATCH (n:Person {name: 'Charlie'}) RETURN n")
        assert len(verify) == 1

    def test_execution_with_chaining(self):
        """Test execution: WITH 1 AS x WITH x + 1 AS y RETURN y."""
        gf = GraphForge()
        result = gf.execute("WITH 1 AS x WITH x + 1 AS y RETURN y")

        assert len(result) == 1
        assert result[0]["y"].value == 2

    def test_execution_with_unwind(self):
        """Test execution: WITH [1, 2, 3] AS nums UNWIND nums AS n RETURN n."""
        gf = GraphForge()
        result = gf.execute("WITH [1, 2, 3] AS nums UNWIND nums AS n RETURN n")

        assert len(result) == 3
        assert result[0]["n"].value == 1
        assert result[1]["n"].value == 2
        assert result[2]["n"].value == 3

    def test_execution_with_where(self):
        """Test execution: WITH 5 AS threshold MATCH (n:Person) WHERE n.age > threshold RETURN n."""
        gf = GraphForge()
        # Create test data
        gf.execute("CREATE (:Person {name: 'Alice', age: 25})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 35})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 45})")

        # Query with WITH at start
        result = gf.execute(
            "WITH 30 AS threshold MATCH (n:Person) WHERE n.age > threshold RETURN n.name AS name ORDER BY n.name"
        )

        assert len(result) == 2
        assert result[0]["name"].value == "Bob"
        assert result[1]["name"].value == "Charlie"

    def test_execution_complex_expression(self):
        """Test execution: WITH {name: 'Alice', filters: [25, 30, 35]} AS params ..."""
        gf = GraphForge()
        result = gf.execute("""
            WITH {name: 'Alice', min_age: 25} AS params
            RETURN params.name AS name, params.min_age AS age
        """)

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"
        assert result[0]["age"].value == 25
