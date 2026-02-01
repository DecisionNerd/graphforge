"""End-to-end integration tests for GraphForge query execution.

These tests verify the complete pipeline: parse -> plan -> execute.
"""

import pytest

from graphforge import GraphForge
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import CypherInt, CypherString


@pytest.fixture
def empty_graph():
    """Empty GraphForge instance."""
    return GraphForge()


@pytest.fixture
def simple_graph():
    """GraphForge instance with a simple graph."""
    gf = GraphForge()

    # Add nodes
    alice = NodeRef(
        id=1,
        labels=frozenset(["Person"]),
        properties={"name": CypherString("Alice"), "age": CypherInt(30)},
    )
    bob = NodeRef(
        id=2,
        labels=frozenset(["Person"]),
        properties={"name": CypherString("Bob"), "age": CypherInt(25)},
    )
    charlie = NodeRef(
        id=3,
        labels=frozenset(["Person"]),
        properties={"name": CypherString("Charlie"), "age": CypherInt(35)},
    )

    gf.graph.add_node(alice)
    gf.graph.add_node(bob)
    gf.graph.add_node(charlie)

    # Add edges
    knows1 = EdgeRef(id=1, type="KNOWS", src=alice, dst=bob, properties={"since": CypherInt(2020)})
    knows2 = EdgeRef(
        id=2, type="KNOWS", src=bob, dst=charlie, properties={"since": CypherInt(2021)}
    )

    gf.graph.add_edge(knows1)
    gf.graph.add_edge(knows2)

    return gf


class TestBasicQueries:
    """Test basic MATCH and RETURN queries."""

    def test_match_all_nodes(self, simple_graph):
        """Test matching all nodes."""
        results = simple_graph.execute("MATCH (n) RETURN n")
        assert len(results) == 3
        # All results should have a node
        for row in results:
            assert "col_0" in row
            node = row["col_0"]
            assert isinstance(node, NodeRef)

    def test_match_nodes_by_label(self, simple_graph):
        """Test matching nodes by label."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n")
        assert len(results) == 3
        for row in results:
            node = row["col_0"]
            assert "Person" in node.labels

    def test_match_with_limit(self, simple_graph):
        """Test MATCH with LIMIT clause."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n LIMIT 2")
        assert len(results) == 2

    def test_match_with_skip(self, simple_graph):
        """Test MATCH with SKIP clause."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n SKIP 1")
        assert len(results) == 2

    def test_match_with_skip_and_limit(self, simple_graph):
        """Test MATCH with both SKIP and LIMIT."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n SKIP 1 LIMIT 1")
        assert len(results) == 1

    def test_empty_result(self, simple_graph):
        """Test query that returns no results."""
        results = simple_graph.execute("MATCH (n:NonExistent) RETURN n")
        assert len(results) == 0


class TestWhereClause:
    """Test queries with WHERE clause filtering."""

    def test_where_property_equals(self, simple_graph):
        """Test WHERE with property equality."""
        results = simple_graph.execute("MATCH (n:Person) WHERE n.name = 'Alice' RETURN n")
        assert len(results) == 1
        node = results[0]["col_0"]
        assert node.properties["name"].value == "Alice"

    def test_where_property_greater_than(self, simple_graph):
        """Test WHERE with greater than comparison."""
        results = simple_graph.execute("MATCH (n:Person) WHERE n.age > 30 RETURN n")
        assert len(results) == 1
        node = results[0]["col_0"]
        assert node.properties["age"].value == 35

    def test_where_property_less_than(self, simple_graph):
        """Test WHERE with less than comparison."""
        results = simple_graph.execute("MATCH (n:Person) WHERE n.age < 30 RETURN n")
        assert len(results) == 1
        node = results[0]["col_0"]
        assert node.properties["age"].value == 25

    def test_where_and_condition(self, simple_graph):
        """Test WHERE with AND operator."""
        results = simple_graph.execute("MATCH (n:Person) WHERE n.age > 20 AND n.age < 30 RETURN n")
        assert len(results) == 1
        node = results[0]["col_0"]
        assert node.properties["age"].value == 25


class TestRelationshipQueries:
    """Test queries with relationship patterns."""

    def test_match_relationship_out(self, simple_graph):
        """Test matching outgoing relationships."""
        results = simple_graph.execute("MATCH (a:Person)-[r:KNOWS]->(b:Person) RETURN a, r, b")
        assert len(results) == 2

        # Check first result
        row = results[0]
        assert "col_0" in row  # a
        assert "col_1" in row  # r
        assert "col_2" in row  # b

        src = row["col_0"]
        edge = row["col_1"]
        dst = row["col_2"]

        assert isinstance(src, NodeRef)
        assert isinstance(edge, EdgeRef)
        assert isinstance(dst, NodeRef)
        assert edge.type == "KNOWS"

    def test_match_relationship_with_where(self, simple_graph):
        """Test relationship pattern with WHERE clause."""
        results = simple_graph.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) WHERE a.name = 'Alice' RETURN b"
        )
        assert len(results) == 1
        node = results[0]["col_0"]
        assert node.properties["name"].value == "Bob"

    def test_match_relationship_property_filter(self, simple_graph):
        """Test filtering on relationship properties."""
        results = simple_graph.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) WHERE r.since > 2020 RETURN a, b"
        )
        assert len(results) == 1
        src = results[0]["col_0"]
        dst = results[0]["col_1"]
        assert src.properties["name"].value == "Bob"
        assert dst.properties["name"].value == "Charlie"


class TestEmptyGraph:
    """Test queries on empty graphs."""

    def test_match_empty_graph(self, empty_graph):
        """Test MATCH on empty graph returns no results."""
        results = empty_graph.execute("MATCH (n) RETURN n")
        assert len(results) == 0

    def test_match_with_label_empty_graph(self, empty_graph):
        """Test MATCH with label on empty graph."""
        results = empty_graph.execute("MATCH (n:Person) RETURN n")
        assert len(results) == 0


class TestOrderBy:
    """Test ORDER BY clause."""

    def test_order_by_single_property_asc(self, simple_graph):
        """Test ORDER BY with single property ASC."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY n.age")
        assert len(results) == 3
        # Should be ordered by age: Bob (25), Alice (30), Charlie (35)
        assert results[0]["name"].value == "Bob"
        assert results[1]["name"].value == "Alice"
        assert results[2]["name"].value == "Charlie"

    def test_order_by_single_property_desc(self, simple_graph):
        """Test ORDER BY with single property DESC."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY n.age DESC")
        assert len(results) == 3
        # Should be ordered by age DESC: Charlie (35), Alice (30), Bob (25)
        assert results[0]["name"].value == "Charlie"
        assert results[1]["name"].value == "Alice"
        assert results[2]["name"].value == "Bob"

    def test_order_by_multiple_properties(self, simple_graph):
        """Test ORDER BY with multiple properties."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n ORDER BY n.age DESC, n.name ASC")
        assert len(results) == 3
        # First by age DESC, then by name ASC
        assert results[0]["col_0"].properties["name"].value == "Charlie"
        assert results[1]["col_0"].properties["name"].value == "Alice"
        assert results[2]["col_0"].properties["name"].value == "Bob"

    def test_order_by_with_where(self, simple_graph):
        """Test ORDER BY with WHERE clause."""
        results = simple_graph.execute(
            "MATCH (n:Person) WHERE n.age > 25 RETURN n.name AS name ORDER BY n.age"
        )
        assert len(results) == 2
        # Alice (30), Charlie (35)
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

    def test_order_by_with_limit(self, simple_graph):
        """Test ORDER BY with LIMIT."""
        results = simple_graph.execute(
            "MATCH (n:Person) RETURN n.name AS name ORDER BY n.age DESC LIMIT 2"
        )
        assert len(results) == 2
        # Top 2 by age: Charlie, Alice
        assert results[0]["name"].value == "Charlie"
        assert results[1]["name"].value == "Alice"

    def test_order_by_with_skip_limit(self, simple_graph):
        """Test ORDER BY with SKIP and LIMIT."""
        results = simple_graph.execute(
            "MATCH (n:Person) RETURN n.name AS name ORDER BY n.age SKIP 1 LIMIT 1"
        )
        assert len(results) == 1
        # Skip Bob (25), get Alice (30)
        assert results[0]["name"].value == "Alice"


class TestAggregationFunctions:
    """Test aggregation functions."""

    def test_count_star(self, simple_graph):
        """Test COUNT(*) returns total row count."""
        results = simple_graph.execute("MATCH (n:Person) RETURN COUNT(*) AS count")
        assert len(results) == 1
        assert results[0]["count"].value == 3

    def test_count_variable(self, simple_graph):
        """Test COUNT(n) counts nodes."""
        results = simple_graph.execute("MATCH (n:Person) RETURN COUNT(n) AS count")
        assert len(results) == 1
        assert results[0]["count"].value == 3

    def test_sum_function(self, simple_graph):
        """Test SUM aggregation."""
        results = simple_graph.execute("MATCH (n:Person) RETURN SUM(n.age) AS total_age")
        assert len(results) == 1
        # 25 + 30 + 35 = 90
        assert results[0]["total_age"].value == 90

    def test_avg_function(self, simple_graph):
        """Test AVG aggregation."""
        results = simple_graph.execute("MATCH (n:Person) RETURN AVG(n.age) AS avg_age")
        assert len(results) == 1
        # (25 + 30 + 35) / 3 = 30.0
        assert results[0]["avg_age"].value == 30.0

    def test_min_function(self, simple_graph):
        """Test MIN aggregation."""
        results = simple_graph.execute("MATCH (n:Person) RETURN MIN(n.age) AS min_age")
        assert len(results) == 1
        assert results[0]["min_age"].value == 25

    def test_max_function(self, simple_graph):
        """Test MAX aggregation."""
        results = simple_graph.execute("MATCH (n:Person) RETURN MAX(n.age) AS max_age")
        assert len(results) == 1
        assert results[0]["max_age"].value == 35

    def test_grouping_with_count(self, simple_graph):
        """Test grouping with COUNT - count relationships per person."""
        # Alice has 1 outgoing, Bob has 1 outgoing, Charlie has 0
        results = simple_graph.execute("MATCH (n:Person) RETURN n.name AS name, COUNT(*) AS cnt")
        # Each person gets one row (grouped by name)
        assert len(results) == 3

        # Check results (order may vary)
        names = {r["name"].value for r in results}
        assert names == {"Alice", "Bob", "Charlie"}

    def test_grouping_with_sum(self, simple_graph):
        """Test grouping with SUM."""
        # For this test, let's count edges per source node
        results = simple_graph.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) "
            "RETURN a.name AS source, COUNT(r) AS relationship_count"
        )
        assert len(results) == 2  # Alice and Bob have outgoing relationships

        result_dict = {r["source"].value: r["relationship_count"].value for r in results}
        assert result_dict["Alice"] == 1
        assert result_dict["Bob"] == 1

    def test_count_with_where(self, simple_graph):
        """Test COUNT with WHERE clause."""
        results = simple_graph.execute("MATCH (n:Person) WHERE n.age > 25 RETURN COUNT(n) AS count")
        assert len(results) == 1
        assert results[0]["count"].value == 2  # Alice and Charlie

    def test_multiple_aggregates(self, simple_graph):
        """Test multiple aggregation functions in one query."""
        results = simple_graph.execute(
            "MATCH (n:Person) RETURN COUNT(n) AS count, SUM(n.age) AS total, AVG(n.age) AS avg"
        )
        assert len(results) == 1
        assert results[0]["count"].value == 3
        assert results[0]["total"].value == 90
        assert results[0]["avg"].value == 30.0


class TestReturnAliasing:
    """Test RETURN clause with aliases."""

    def test_return_variable_with_alias(self, simple_graph):
        """Test RETURN variable with alias."""
        results = simple_graph.execute("MATCH (n:Person) RETURN n AS person LIMIT 1")
        assert len(results) == 1
        assert "person" in results[0]
        assert isinstance(results[0]["person"], NodeRef)

    def test_return_property_with_alias(self, simple_graph):
        """Test RETURN property with alias."""
        results = simple_graph.execute(
            "MATCH (n:Person) WHERE n.name = 'Alice' RETURN n.name AS name, n.age AS age"
        )
        assert len(results) == 1
        assert "name" in results[0]
        assert "age" in results[0]
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30

    def test_return_mixed_aliases(self, simple_graph):
        """Test RETURN with mixed aliased and non-aliased items."""
        results = simple_graph.execute(
            "MATCH (n:Person) WHERE n.name = 'Bob' RETURN n.name AS name, n.age LIMIT 1"
        )
        assert len(results) == 1
        # First item has alias
        assert "name" in results[0]
        assert results[0]["name"].value == "Bob"
        # Second item has default column name
        assert "col_1" in results[0]
        assert results[0]["col_1"].value == 25

    def test_return_relationship_with_aliases(self, simple_graph):
        """Test RETURN relationship items with aliases."""
        results = simple_graph.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) "
            "WHERE a.name = 'Alice' "
            "RETURN a.name AS source, b.name AS target, r.since AS year"
        )
        assert len(results) == 1
        assert "source" in results[0]
        assert "target" in results[0]
        assert "year" in results[0]
        assert results[0]["source"].value == "Alice"
        assert results[0]["target"].value == "Bob"
        assert results[0]["year"].value == 2020
