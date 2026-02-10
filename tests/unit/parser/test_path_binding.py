"""Unit tests for path binding syntax in parser."""

import pytest

from graphforge.parser.parser import parse_cypher
from graphforge.ast.clause import MatchClause, OptionalMatchClause, CreateClause
from graphforge.ast.pattern import NodePattern, RelationshipPattern, Direction


class TestPathBindingParsing:
    """Test parsing of path binding syntax: p = (pattern)."""

    def test_parse_simple_path_binding(self):
        """Test parsing simple path binding: p = (a)-[:R]->(b)"""
        query = "MATCH p = (a)-[:KNOWS]->(b) RETURN p"
        ast = parse_cypher(query)

        # Get MATCH clause from clauses list
        match = ast.clauses[0]
        assert isinstance(match, MatchClause)
        patterns = match.patterns
        assert len(patterns) == 1

        # Check that pattern has path variable
        pattern = patterns[0]
        assert isinstance(pattern, dict)
        assert "path_variable" in pattern
        assert "parts" in pattern
        assert pattern["path_variable"] == "p"

        # Check pattern parts
        parts = pattern["parts"]
        assert len(parts) == 3  # node, rel, node
        assert isinstance(parts[0], NodePattern)
        assert parts[0].variable == "a"
        assert isinstance(parts[1], RelationshipPattern)
        assert parts[1].types == ["KNOWS"]
        assert isinstance(parts[2], NodePattern)
        assert parts[2].variable == "b"

    def test_parse_path_binding_variable_length(self):
        """Test parsing path binding with variable-length pattern."""
        query = "MATCH path = (a)-[:KNOWS*1..3]->(b) RETURN path"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        patterns = match.patterns
        assert len(patterns) == 1

        pattern = patterns[0]
        assert pattern["path_variable"] == "path"

        parts = pattern["parts"]
        rel = parts[1]
        assert isinstance(rel, RelationshipPattern)
        assert rel.min_hops == 1
        assert rel.max_hops == 3

    def test_parse_path_binding_single_node(self):
        """Test parsing path binding with single node: p = (n)"""
        query = "MATCH p = (n:Person) RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        parts = pattern["parts"]
        assert len(parts) == 1
        assert isinstance(parts[0], NodePattern)
        assert parts[0].labels == ["Person"]

    def test_parse_path_binding_long_path(self):
        """Test parsing path binding with longer path: p = (a)-[:R1]->(b)-[:R2]->(c)"""
        query = "MATCH p = (a)-[:R1]->(b)-[:R2]->(c) RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        parts = pattern["parts"]
        assert len(parts) == 5  # node, rel, node, rel, node
        assert all(isinstance(parts[i], NodePattern) for i in [0, 2, 4])
        assert all(isinstance(parts[i], RelationshipPattern) for i in [1, 3])

    def test_parse_pattern_without_binding(self):
        """Test parsing pattern without path binding: (a)-[:R]->(b)"""
        query = "MATCH (a)-[:KNOWS]->(b) RETURN a, b"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] is None
        assert "parts" in pattern

        parts = pattern["parts"]
        assert len(parts) == 3

    def test_parse_multiple_patterns_mixed_binding(self):
        """Test parsing multiple patterns, some with binding, some without."""
        query = "MATCH p = (a)-[:R1]->(b), (c)-[:R2]->(d) RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        patterns = match.patterns
        assert len(patterns) == 2

        # First pattern has binding
        assert patterns[0]["path_variable"] == "p"

        # Second pattern has no binding
        assert patterns[1]["path_variable"] is None

    def test_parse_path_binding_with_labels_and_properties(self):
        """Test path binding with labels and properties."""
        query = "MATCH p = (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person) RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        parts = pattern["parts"]
        # First node
        assert parts[0].labels == ["Person"]
        assert "name" in parts[0].properties

        # Relationship
        assert parts[1].types == ["KNOWS"]
        assert "since" in parts[1].properties

        # Second node
        assert parts[2].labels == ["Person"]

    def test_parse_path_binding_undirected(self):
        """Test path binding with undirected relationship."""
        query = "MATCH p = (a)-[:KNOWS]-(b) RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        parts = pattern["parts"]
        rel = parts[1]
        assert rel.direction == Direction.UNDIRECTED

    def test_parse_path_binding_left_direction(self):
        """Test path binding with left-directed relationship."""
        query = "MATCH p = (a)<-[:KNOWS]-(b) RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        parts = pattern["parts"]
        rel = parts[1]
        assert rel.direction == Direction.IN

    def test_parse_path_binding_anonymous_nodes(self):
        """Test path binding with anonymous nodes."""
        query = "MATCH p = ()-[:KNOWS]->() RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        parts = pattern["parts"]
        assert parts[0].variable is None
        assert parts[2].variable is None

    def test_parse_path_binding_in_optional_match(self):
        """Test path binding in OPTIONAL MATCH."""
        query = "OPTIONAL MATCH p = (a)-[:KNOWS]->(b) RETURN p"
        ast = parse_cypher(query)

        # Find OptionalMatchClause in clauses
        opt_match = None
        for clause in ast.clauses:
            if isinstance(clause, OptionalMatchClause):
                opt_match = clause
                break

        assert opt_match is not None
        pattern = opt_match.patterns[0]
        assert pattern["path_variable"] == "p"

    def test_parse_path_binding_in_create(self):
        """Test path binding in CREATE clause."""
        query = "CREATE p = (a:Person)-[:KNOWS]->(b:Person) RETURN p"
        ast = parse_cypher(query)

        # Find CreateClause in clauses
        create = None
        for clause in ast.clauses:
            if isinstance(clause, CreateClause):
                create = clause
                break

        assert create is not None
        pattern = create.patterns[0]
        assert pattern["path_variable"] == "p"


class TestPathBindingEdgeCases:
    """Test edge cases for path binding."""

    def test_path_variable_name_validation(self):
        """Test that various path variable names work."""
        valid_names = ["p", "path", "myPath", "path123", "_path"]

        for name in valid_names:
            query = f"MATCH {name} = (a)-[:R]->(b) RETURN {name}"
            ast = parse_cypher(query)
            match = ast.clauses[0]
            pattern = match.patterns[0]
            assert pattern["path_variable"] == name

    def test_path_binding_with_where(self):
        """Test path binding works with WHERE clause."""
        query = "MATCH p = (a)-[:KNOWS*1..3]->(b) WHERE a.name = 'Alice' RETURN p"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        # Check WHERE clause exists
        from graphforge.ast.clause import WhereClause
        has_where = any(isinstance(c, WhereClause) for c in ast.clauses)
        assert has_where

    def test_multiple_path_bindings(self):
        """Test multiple path bindings in same query."""
        query = "MATCH p1 = (a)-[:R1]->(b), p2 = (c)-[:R2]->(d) RETURN p1, p2"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        patterns = match.patterns
        assert len(patterns) == 2
        assert patterns[0]["path_variable"] == "p1"
        assert patterns[1]["path_variable"] == "p2"

    def test_path_binding_with_relationship_variable(self):
        """Test path binding when relationship also has variable."""
        query = "MATCH p = (a)-[r:KNOWS]->(b) RETURN p, r"
        ast = parse_cypher(query)

        match = ast.clauses[0]
        pattern = match.patterns[0]
        assert pattern["path_variable"] == "p"

        parts = pattern["parts"]
        rel = parts[1]
        assert rel.variable == "r"  # Relationship variable preserved
