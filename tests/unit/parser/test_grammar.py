"""Tests for Cypher grammar parsing.

Tests that the Lark grammar can parse valid Cypher queries.
"""

from pathlib import Path

from lark import Lark
import pytest


@pytest.fixture
def grammar():
    """Load the Cypher grammar."""
    grammar_path = (
        Path(__file__).parent.parent.parent.parent / "src" / "graphforge" / "parser" / "cypher.lark"
    )
    with open(grammar_path) as f:
        return Lark(f.read(), start="query")


@pytest.mark.unit
class TestGrammarBasics:
    """Basic grammar parsing tests."""

    def test_simple_match_return(self, grammar):
        """Parse: MATCH (n) RETURN n"""
        tree = grammar.parse("MATCH (n) RETURN n")
        assert tree is not None

    def test_match_with_label(self, grammar):
        """Parse: MATCH (n:Person) RETURN n"""
        tree = grammar.parse("MATCH (n:Person) RETURN n")
        assert tree is not None

    def test_match_with_properties(self, grammar):
        """Parse: MATCH (n:Person {name: "Alice"}) RETURN n"""
        tree = grammar.parse('MATCH (n:Person {name: "Alice"}) RETURN n')
        assert tree is not None

    def test_match_where_return(self, grammar):
        """Parse: MATCH (n) WHERE n.age > 30 RETURN n"""
        tree = grammar.parse("MATCH (n) WHERE n.age > 30 RETURN n")
        assert tree is not None

    def test_match_return_limit(self, grammar):
        """Parse: MATCH (n) RETURN n LIMIT 10"""
        tree = grammar.parse("MATCH (n) RETURN n LIMIT 10")
        assert tree is not None

    def test_match_return_skip_limit(self, grammar):
        """Parse: MATCH (n) RETURN n SKIP 5 LIMIT 10"""
        tree = grammar.parse("MATCH (n) RETURN n SKIP 5 LIMIT 10")
        assert tree is not None


@pytest.mark.unit
class TestGrammarPatterns:
    """Pattern matching grammar tests."""

    def test_node_multiple_labels(self, grammar):
        """Parse: MATCH (n:Person:Employee) RETURN n"""
        tree = grammar.parse("MATCH (n:Person:Employee) RETURN n")
        assert tree is not None

    def test_relationship_outgoing(self, grammar):
        """Parse: MATCH (a)-[r:KNOWS]->(b) RETURN a, b"""
        tree = grammar.parse("MATCH (a)-[r:KNOWS]->(b) RETURN a, b")
        assert tree is not None

    def test_relationship_incoming(self, grammar):
        """Parse: MATCH (a)<-[r:KNOWS]-(b) RETURN a"""
        tree = grammar.parse("MATCH (a)<-[r:KNOWS]-(b) RETURN a")
        assert tree is not None

    def test_relationship_undirected(self, grammar):
        """Parse: MATCH (a)-[r:KNOWS]-(b) RETURN a"""
        tree = grammar.parse("MATCH (a)-[r:KNOWS]-(b) RETURN a")
        assert tree is not None

    def test_anonymous_node(self, grammar):
        """Parse: MATCH (:Person) RETURN 1"""
        tree = grammar.parse("MATCH (:Person) RETURN 1")
        assert tree is not None

    def test_anonymous_relationship(self, grammar):
        """Parse: MATCH (a)-[:KNOWS]->(b) RETURN a"""
        tree = grammar.parse("MATCH (a)-[:KNOWS]->(b) RETURN a")
        assert tree is not None


@pytest.mark.unit
class TestGrammarExpressions:
    """Expression grammar tests."""

    def test_property_access(self, grammar):
        """Parse property access in RETURN."""
        tree = grammar.parse("MATCH (n) RETURN n.name")
        assert tree is not None

    def test_comparison_operators(self, grammar):
        """Parse various comparison operators."""
        queries = [
            "MATCH (n) WHERE n.age > 30 RETURN n",
            "MATCH (n) WHERE n.age < 30 RETURN n",
            "MATCH (n) WHERE n.age >= 30 RETURN n",
            "MATCH (n) WHERE n.age <= 30 RETURN n",
            "MATCH (n) WHERE n.age = 30 RETURN n",
            "MATCH (n) WHERE n.age <> 30 RETURN n",
        ]
        for query in queries:
            tree = grammar.parse(query)
            assert tree is not None

    def test_logical_and(self, grammar):
        """Parse: MATCH (n) WHERE n.age > 30 AND n.age < 50 RETURN n"""
        tree = grammar.parse("MATCH (n) WHERE n.age > 30 AND n.age < 50 RETURN n")
        assert tree is not None

    def test_logical_or(self, grammar):
        """Parse: MATCH (n) WHERE n.age < 20 OR n.age > 60 RETURN n"""
        tree = grammar.parse("MATCH (n) WHERE n.age < 20 OR n.age > 60 RETURN n")
        assert tree is not None

    def test_parenthesized_expression(self, grammar):
        """Parse: MATCH (n) WHERE (n.age > 30) RETURN n"""
        tree = grammar.parse("MATCH (n) WHERE (n.age > 30) RETURN n")
        assert tree is not None


@pytest.mark.unit
class TestGrammarLiterals:
    """Literal value grammar tests."""

    def test_integer_literal(self, grammar):
        """Parse integer literals."""
        tree = grammar.parse("MATCH (n {age: 42}) RETURN n")
        assert tree is not None

    def test_string_literal_double_quotes(self, grammar):
        """Parse string with double quotes."""
        tree = grammar.parse('MATCH (n {name: "Alice"}) RETURN n')
        assert tree is not None

    def test_string_literal_single_quotes(self, grammar):
        """Parse string with single quotes."""
        tree = grammar.parse("MATCH (n {name: 'Alice'}) RETURN n")
        assert tree is not None

    def test_boolean_true(self, grammar):
        """Parse boolean true."""
        tree = grammar.parse("MATCH (n {active: true}) RETURN n")
        assert tree is not None

    def test_boolean_false(self, grammar):
        """Parse boolean false."""
        tree = grammar.parse("MATCH (n {active: false}) RETURN n")
        assert tree is not None

    def test_null_literal(self, grammar):
        """Parse null."""
        tree = grammar.parse("MATCH (n {value: null}) RETURN n")
        assert tree is not None


@pytest.mark.unit
class TestGrammarCaseInsensitive:
    """Test case insensitivity of keywords."""

    def test_lowercase_keywords(self, grammar):
        """Keywords work in lowercase."""
        tree = grammar.parse("match (n) where n.age > 30 return n limit 10")
        assert tree is not None

    def test_mixed_case_keywords(self, grammar):
        """Keywords work in mixed case."""
        tree = grammar.parse("Match (n) Where n.age > 30 Return n Limit 10")
        assert tree is not None
