"""Integration tests for label disjunction (:Label1|Label2)."""

import pytest

from graphforge.api import GraphForge


@pytest.fixture
def gf():
    """Provide a fresh GraphForge instance for each test."""
    return GraphForge()


@pytest.mark.integration
class TestLabelDisjunctionBasic:
    """Tests for basic label disjunction functionality."""

    def test_disjunction_matches_first_label(self, gf):
        """Label disjunction matches nodes with first label."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Company {name: 'Acme'})")

        result = gf.execute("MATCH (n:Person|Company) RETURN n.name AS name ORDER BY name")

        assert len(result) == 2
        assert result[0]["name"].value == "Acme"
        assert result[1]["name"].value == "Alice"

    def test_disjunction_matches_second_label(self, gf):
        """Label disjunction matches nodes with second label."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Company {name: 'Acme'})")
        gf.execute("CREATE (:Product {name: 'Widget'})")

        result = gf.execute("MATCH (n:Person|Company) RETURN count(*) AS count")

        assert result[0]["count"].value == 2

    def test_disjunction_with_three_labels(self, gf):
        """Label disjunction with three labels."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Company {name: 'Acme'})")
        gf.execute("CREATE (:Product {name: 'Widget'})")

        result = gf.execute("MATCH (n:Person|Company|Product) RETURN count(*) AS count")

        assert result[0]["count"].value == 3

    def test_disjunction_no_matches(self, gf):
        """Label disjunction with no matching nodes."""
        gf.execute("CREATE (:Person {name: 'Alice'})")

        result = gf.execute("MATCH (n:Company|Product) RETURN n")

        assert len(result) == 0


@pytest.mark.integration
class TestLabelDisjunctionWithConjunction:
    """Tests for label disjunction combined with conjunction."""

    def test_conjunction_within_group(self, gf):
        """Conjunction within a label group (must have both labels)."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person:Employee {name: 'Bob'})")
        gf.execute("CREATE (:Company {name: 'Acme'})")

        result = gf.execute("MATCH (n:Person:Employee) RETURN n.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "Bob"

    def test_disjunction_of_conjunctions(self, gf):
        """Disjunction of conjunction groups."""
        gf.execute("CREATE (:Person:Employee {name: 'Bob'})")
        gf.execute("CREATE (:Company:Startup {name: 'TechCo'})")
        gf.execute("CREATE (:Person {name: 'Alice'})")

        result = gf.execute(
            "MATCH (n:Person:Employee|Company:Startup) RETURN n.name AS name ORDER BY name"
        )

        assert len(result) == 2
        assert result[0]["name"].value == "Bob"
        assert result[1]["name"].value == "TechCo"


@pytest.mark.integration
class TestLabelDisjunctionInPatterns:
    """Tests for label disjunction in different pattern contexts."""

    def test_disjunction_in_relationship_pattern(self, gf):
        """Label disjunction in relationship patterns."""
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Company {name: 'Acme'})")
        gf.execute("CREATE (c:Product {name: 'Widget'})")
        gf.execute("MATCH (a:Person), (b:Company) CREATE (a)-[:WORKS_FOR]->(b)")
        gf.execute("MATCH (a:Person), (c:Product) CREATE (a)-[:LIKES]->(c)")

        result = gf.execute("""
            MATCH (a:Person)-[r]->(b:Company|Product)
            RETURN b.name AS name
            ORDER BY name
        """)

        assert len(result) == 2
        assert result[0]["name"].value == "Acme"
        assert result[1]["name"].value == "Widget"

    def test_disjunction_in_multiple_patterns(self, gf):
        """Label disjunction in multiple MATCH patterns."""
        gf.execute("CREATE (a:Person {name: 'Alice'})")
        gf.execute("CREATE (b:Company {name: 'Acme'})")
        gf.execute("CREATE (c:Product {name: 'Widget'})")

        result = gf.execute("""
            MATCH (a:Person|Company), (b:Product|Company)
            RETURN count(*) AS count
        """)

        # Person x (Product, Company) = 2
        # Company x (Product, Company) = 2
        # Total = 4
        assert result[0]["count"].value == 4

    def test_disjunction_in_where_clause(self, gf):
        """Label disjunction works correctly with WHERE clause."""
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Company {name: 'Acme', age: 5})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")

        result = gf.execute("""
            MATCH (n:Person|Company)
            WHERE n.age > 20
            RETURN n.name AS name
            ORDER BY name
        """)

        assert len(result) == 2
        assert result[0]["name"].value == "Alice"
        assert result[1]["name"].value == "Bob"


@pytest.mark.integration
class TestLabelDisjunctionEdgeCases:
    """Edge case tests for label disjunction."""

    def test_single_label_as_disjunction(self, gf):
        """Single label (no pipe) still works."""
        gf.execute("CREATE (:Person {name: 'Alice'})")

        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_disjunction_with_node_having_both_labels(self, gf):
        """Node with both labels matches disjunction once."""
        gf.execute("CREATE (:Person:Company {name: 'Alice'})")

        result = gf.execute("MATCH (n:Person|Company) RETURN n.name AS name")

        # Should match once even though it has both labels
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_disjunction_with_properties(self, gf):
        """Label disjunction with inline properties."""
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Company {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")

        result = gf.execute("MATCH (n:Person|Company {name: 'Alice'}) RETURN n")

        assert len(result) == 2

    def test_create_rejects_disjunctive_labels(self, gf):
        """CREATE should reject disjunctive labels with clear error message."""
        with pytest.raises(ValueError, match="Disjunctive labels.*not allowed in CREATE"):
            gf.execute("CREATE (:Person|Company {name: 'Alice'})")
