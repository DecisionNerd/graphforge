"""openCypher TCK Compliance Tests.

These tests validate strict compliance with openCypher semantics.
Each test corresponds to a TCK scenario and validates specific semantic behaviors.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherBool, CypherFloat, CypherInt, CypherNull, CypherString


@pytest.fixture
def gf():
    """Create a fresh GraphForge instance for each test."""
    return GraphForge()


def add_node(gf: GraphForge, node_id: int, labels: list[str], properties: dict):
    """Helper to add a node to the graph."""
    cypher_props = {}
    for key, value in properties.items():
        if isinstance(value, str):
            cypher_props[key] = CypherString(value)
        elif isinstance(value, int):
            cypher_props[key] = CypherInt(value)
        elif isinstance(value, float):
            cypher_props[key] = CypherFloat(value)
        elif isinstance(value, bool):
            cypher_props[key] = CypherBool(value)
        elif value is None:
            cypher_props[key] = CypherNull()
        else:
            cypher_props[key] = value

    node = NodeRef(id=node_id, labels=frozenset(labels), properties=cypher_props)
    gf.graph.add_node(node)
    return node


def add_edge(
    gf: GraphForge, edge_id: int, edge_type: str, src: NodeRef, dst: NodeRef, properties: dict
):
    """Helper to add an edge to the graph."""
    cypher_props = {}
    for key, value in properties.items():
        if isinstance(value, str):
            cypher_props[key] = CypherString(value)
        elif isinstance(value, int):
            cypher_props[key] = CypherInt(value)
        elif isinstance(value, float):
            cypher_props[key] = CypherFloat(value)
        elif isinstance(value, bool):
            cypher_props[key] = CypherBool(value)
        elif value is None:
            cypher_props[key] = CypherNull()
        else:
            cypher_props[key] = value

    edge = EdgeRef(id=edge_id, type=edge_type, src=src, dst=dst, properties=cypher_props)
    gf.graph.add_edge(edge)
    return edge


@pytest.mark.tck
class TestTCKMatch:
    """TCK compliance tests for MATCH patterns."""

    def test_match_all_nodes(self, gf):
        """TCK: Match all nodes in the graph."""
        # Setup
        add_node(gf, 1, [], {"name": "A"})
        add_node(gf, 2, [], {"name": "B"})
        add_node(gf, 3, [], {"name": "C"})

        # Execute
        results = gf.execute("MATCH (n) RETURN n")

        # Verify
        assert len(results) == 3, "Should return exactly 3 nodes"
        names = {r["col_0"].properties["name"].value for r in results}
        assert names == {"A", "B", "C"}, "Should return nodes A, B, and C"

    def test_match_nodes_by_label(self, gf):
        """TCK: Match nodes with a specific label."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice"})
        add_node(gf, 2, ["Person"], {"name": "Bob"})
        add_node(gf, 3, ["Dog"], {"name": "Rex"})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")

        # Verify
        assert len(results) == 2, "Should return exactly 2 Person nodes"
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob"}, "Should return Alice and Bob"

    def test_match_with_where_clause(self, gf):
        """TCK: Match nodes with WHERE clause filtering."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob", "age": 25})
        add_node(gf, 3, ["Person"], {"name": "Charlie", "age": 35})

        # Execute
        results = gf.execute("MATCH (p:Person) WHERE p.age > 30 RETURN p.name AS name")

        # Verify
        assert len(results) == 1, "Should return exactly 1 node"
        assert results[0]["name"].value == "Charlie", "Should return Charlie"

    def test_match_with_limit(self, gf):
        """TCK: LIMIT clause limits result rows."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice"})
        add_node(gf, 2, ["Person"], {"name": "Bob"})
        add_node(gf, 3, ["Person"], {"name": "Charlie"})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name LIMIT 2")

        # Verify
        assert len(results) == 2, "LIMIT 2 should return exactly 2 rows"

    def test_match_with_skip(self, gf):
        """TCK: SKIP clause skips initial rows."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice"})
        add_node(gf, 2, ["Person"], {"name": "Bob"})
        add_node(gf, 3, ["Person"], {"name": "Charlie"})

        # Execute - ORDER BY ensures deterministic order
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name SKIP 1")

        # Verify
        assert len(results) == 2, "SKIP 1 should return 2 rows (total 3 - 1)"
        names = [r["name"].value for r in results]
        assert names == ["Bob", "Charlie"], "Should skip Alice and return Bob, Charlie"


@pytest.mark.tck
class TestTCKAggregation:
    """TCK compliance tests for aggregation functions."""

    def test_count_star(self, gf):
        """TCK: COUNT(*) counts all rows."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice"})
        add_node(gf, 2, ["Person"], {"name": "Bob"})
        add_node(gf, 3, ["Person"], {"name": "Charlie"})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN COUNT(*) AS count")

        # Verify
        assert len(results) == 1, "Aggregation should return 1 row"
        assert results[0]["count"].value == 3, "COUNT(*) should be 3"

    def test_count_expression(self, gf):
        """TCK: COUNT(expr) counts non-NULL values."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob", "age": 25})
        add_node(gf, 3, ["Person"], {"name": "Charlie"})  # No age property

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN COUNT(p.age) AS count")

        # Verify
        assert len(results) == 1, "Aggregation should return 1 row"
        assert results[0]["count"].value == 2, "COUNT(p.age) should be 2 (NULL not counted)"

    def test_sum_aggregation(self, gf):
        """TCK: SUM aggregates numeric values."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob", "age": 25})
        add_node(gf, 3, ["Person"], {"name": "Charlie", "age": 35})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN SUM(p.age) AS total")

        # Verify
        assert len(results) == 1, "Aggregation should return 1 row"
        assert results[0]["total"].value == 90, "SUM should be 90 (30+25+35)"

    def test_avg_aggregation(self, gf):
        """TCK: AVG computes average of numeric values."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob", "age": 25})
        add_node(gf, 3, ["Person"], {"name": "Charlie", "age": 35})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN AVG(p.age) AS average")

        # Verify
        assert len(results) == 1, "Aggregation should return 1 row"
        assert results[0]["average"].value == 30.0, "AVG should be 30.0"

    def test_min_max_aggregation(self, gf):
        """TCK: MIN and MAX find minimum and maximum values."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob", "age": 25})
        add_node(gf, 3, ["Person"], {"name": "Charlie", "age": 35})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN MIN(p.age) AS minimum, MAX(p.age) AS maximum")

        # Verify
        assert len(results) == 1, "Aggregation should return 1 row"
        assert results[0]["minimum"].value == 25, "MIN should be 25"
        assert results[0]["maximum"].value == 35, "MAX should be 35"

    def test_grouping_with_count(self, gf):
        """TCK: Implicit grouping with aggregation."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "city": "NYC"})
        add_node(gf, 2, ["Person"], {"name": "Bob", "city": "NYC"})
        add_node(gf, 3, ["Person"], {"name": "Charlie", "city": "LA"})

        # Execute
        results = gf.execute(
            "MATCH (p:Person) RETURN p.city AS city, COUNT(*) AS count ORDER BY city"
        )

        # Verify
        assert len(results) == 2, "Should return 2 groups (NYC and LA)"
        assert results[0]["city"].value == "LA", "First group should be LA (ORDER BY city)"
        assert results[0]["count"].value == 1, "LA group should have count 1"
        assert results[1]["city"].value == "NYC", "Second group should be NYC"
        assert results[1]["count"].value == 2, "NYC group should have count 2"


@pytest.mark.tck
class TestTCKOrderBy:
    """TCK compliance tests for ORDER BY clause."""

    def test_order_by_asc(self, gf):
        """TCK: ORDER BY sorts in ascending order (default)."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Charlie"})
        add_node(gf, 2, ["Person"], {"name": "Alice"})
        add_node(gf, 3, ["Person"], {"name": "Bob"})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")

        # Verify
        assert len(results) == 3, "Should return 3 rows"
        names = [r["name"].value for r in results]
        assert names == ["Alice", "Bob", "Charlie"], "Should be sorted alphabetically ASC"

    def test_order_by_desc(self, gf):
        """TCK: ORDER BY DESC sorts in descending order."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Charlie", "age": 25})
        add_node(gf, 2, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 3, ["Person"], {"name": "Bob", "age": 35})

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY p.age DESC")

        # Verify
        assert len(results) == 3, "Should return 3 rows"
        names = [r["name"].value for r in results]
        assert names == ["Bob", "Alice", "Charlie"], "Should be sorted by age DESC"

    def test_order_by_multiple_keys(self, gf):
        """TCK: ORDER BY multiple columns."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob", "age": 30})
        add_node(gf, 3, ["Person"], {"name": "Charlie", "age": 25})

        # Execute
        results = gf.execute(
            "MATCH (p:Person) RETURN p.name AS name ORDER BY p.age ASC, p.name ASC"
        )

        # Verify
        assert len(results) == 3, "Should return 3 rows"
        names = [r["name"].value for r in results]
        # First by age (25, 30, 30), then by name for age=30 (Alice, Bob)
        assert names == ["Charlie", "Alice", "Bob"], "Should be sorted by age then name"


@pytest.mark.tck
class TestTCKNullSemantics:
    """TCK compliance tests for NULL handling semantics."""

    def test_null_property_access(self, gf):
        """TCK: Accessing missing property returns NULL."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice"})  # No age property

        # Execute
        results = gf.execute("MATCH (p:Person) RETURN p.age AS age")

        # Verify
        assert len(results) == 1, "Should return 1 row"
        assert isinstance(results[0]["age"], CypherNull), "Missing property should be NULL"

    def test_null_in_comparison(self, gf):
        """TCK: Comparisons with NULL return NULL (not TRUE or FALSE)."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob"})  # No age

        # Execute - WHERE filters out NULLs
        results = gf.execute("MATCH (p:Person) WHERE p.age > 25 RETURN p.name AS name")

        # Verify
        assert len(results) == 1, "NULL comparison should be filtered out by WHERE"
        assert results[0]["name"].value == "Alice", "Should only return Alice"

    def test_count_null_handling(self, gf):
        """TCK: COUNT(*) counts all rows, COUNT(expr) ignores NULLs."""
        # Setup
        add_node(gf, 1, ["Person"], {"name": "Alice", "age": 30})
        add_node(gf, 2, ["Person"], {"name": "Bob"})  # No age

        # Execute
        results = gf.execute(
            "MATCH (p:Person) RETURN COUNT(*) AS all_count, COUNT(p.age) AS age_count"
        )

        # Verify
        assert len(results) == 1, "Should return 1 row"
        assert results[0]["all_count"].value == 2, "COUNT(*) should count all rows"
        assert results[0]["age_count"].value == 1, "COUNT(p.age) should ignore NULLs"
