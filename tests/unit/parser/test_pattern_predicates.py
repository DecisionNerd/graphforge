"""Unit tests for pattern predicate parsing (WHERE inside patterns)."""

from graphforge.ast.expression import BinaryOp
from graphforge.ast.pattern import Direction, RelationshipPattern
from graphforge.parser.parser import parse_cypher


class TestPatternPredicateParsing:
    """Tests for parsing WHERE clauses inside relationship patterns."""

    def test_parse_pattern_with_simple_predicate(self):
        """Parse relationship pattern with simple property comparison."""
        query = "MATCH (a)-[r:KNOWS WHERE r.since > 2020]->(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]  # Middle element is relationship

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.variable == "r"
        assert rel_pattern.types == ["KNOWS"]
        assert rel_pattern.direction == Direction.OUT

        # Check predicate is parsed
        assert rel_pattern.predicate is not None
        assert isinstance(rel_pattern.predicate, BinaryOp)
        assert rel_pattern.predicate.op == ">"

    def test_parse_pattern_without_predicate(self):
        """Pattern without predicate should have None predicate."""
        query = "MATCH (a)-[r:KNOWS]->(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.predicate is None

    def test_parse_undirected_pattern_with_predicate(self):
        """Undirected pattern can have predicate."""
        query = "MATCH (a)-[r:KNOWS WHERE r.weight > 0.5]-(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.direction == Direction.UNDIRECTED
        assert rel_pattern.predicate is not None

    def test_parse_incoming_pattern_with_predicate(self):
        """Incoming pattern can have predicate."""
        query = "MATCH (a)<-[r:KNOWS WHERE r.active = true]-(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.direction == Direction.IN
        assert rel_pattern.predicate is not None

    def test_parse_pattern_with_complex_predicate(self):
        """Pattern with complex AND predicate."""
        query = "MATCH (a)-[r:KNOWS WHERE r.since > 2020 AND r.active = true]->(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.predicate is not None
        assert isinstance(rel_pattern.predicate, BinaryOp)
        assert rel_pattern.predicate.op == "AND"

    def test_parse_variable_length_with_predicate(self):
        """Variable-length pattern can have predicate."""
        query = "MATCH (a)-[r:KNOWS*1..3 WHERE r.weight > 0.5]->(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.min_hops == 1
        assert rel_pattern.max_hops == 3
        assert rel_pattern.predicate is not None

    def test_parse_pattern_with_properties_and_predicate(self):
        """Pattern can have both properties map and WHERE predicate."""
        query = "MATCH (a)-[r:KNOWS {status: 'active'} WHERE r.since > 2020]->(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert "status" in rel_pattern.properties
        assert rel_pattern.predicate is not None

    def test_parse_anonymous_pattern_with_predicate(self):
        """Anonymous relationship can have predicate."""
        query = "MATCH (a)-[:KNOWS WHERE since > 2020]->(b) RETURN a"
        ast = parse_cypher(query)

        match_clause = ast.clauses[0]
        pattern = match_clause.patterns[0]
        parts = pattern["parts"]
        rel_pattern = parts[1]

        assert isinstance(rel_pattern, RelationshipPattern)
        assert rel_pattern.variable is None
        assert rel_pattern.predicate is not None
