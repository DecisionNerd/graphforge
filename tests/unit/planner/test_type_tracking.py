"""Test variable type tracking across clause boundaries."""

import pytest

from graphforge import GraphForge


class TestVariableTypeTracking:
    """Test variable type tracking across clause boundaries."""

    def test_scalar_used_as_node_fails(self):
        """WITH scalar value used as node should fail."""
        query = "WITH 123 AS n MATCH (n) RETURN n"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)
        assert "n" in str(exc_info.value)

    def test_relationship_used_as_node_fails(self):
        """Relationship variable used as node should fail."""
        query = "MATCH ()-[r]-() MATCH (r) RETURN r"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_path_used_as_node_fails(self):
        """Path variable used as node should fail."""
        query = "MATCH p = ()-[]-() MATCH (p) RETURN p"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_node_variable_reused_as_node_succeeds(self):
        """Node variable reused as node should succeed."""
        query = "MATCH (n) MATCH (n) RETURN n"
        gf = GraphForge()
        # Should not raise
        gf.execute(query)

    def test_with_node_variable_passes_through(self):
        """Node variable passed through WITH should remain node type."""
        query = "MATCH (n) WITH n MATCH (n)-[:KNOWS]->(m) RETURN n, m"
        gf = GraphForge()
        # Should not raise
        gf.execute(query)

    def test_with_property_access_creates_scalar(self):
        """Property access in WITH creates scalar variable."""
        query = "MATCH (n) WITH n.name AS name MATCH (name) RETURN name"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_scalar_used_as_relationship_fails(self):
        """WITH scalar value used as relationship should fail."""
        query = "WITH 'test' AS r MATCH ()-[r]-() RETURN r"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_node_used_as_relationship_fails(self):
        """Node variable used as relationship should fail."""
        query = "MATCH (n) MATCH ()-[n]-() RETURN n"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_create_with_scalar_node_fails(self):
        """CREATE with scalar variable used as node should fail."""
        query = "WITH 123 AS n CREATE (n:Test) RETURN n"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_create_binds_node_type(self):
        """CREATE should bind node type for subsequent clauses."""
        query = "CREATE (n:Person) WITH n MATCH (n) RETURN n"
        gf = GraphForge()
        # Should not raise
        gf.execute(query)

    def test_merge_with_scalar_node_fails(self):
        """MERGE with scalar variable used as node should fail."""
        query = "WITH 456 AS n MERGE (n:Test) RETURN n"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_merge_binds_node_type(self):
        """MERGE should bind node type for subsequent clauses."""
        query = "MERGE (n:Person {id: 1}) WITH n MATCH (n) RETURN n"
        gf = GraphForge()
        # Should not raise
        gf.execute(query)

    def test_with_function_call_creates_scalar(self):
        """Function call in WITH creates scalar variable."""
        query = "MATCH (n) WITH count(n) AS cnt MATCH (cnt) RETURN cnt"

        with pytest.raises(SyntaxError) as exc_info:
            gf = GraphForge()
            gf.execute(query)

        assert "VariableTypeConflict" in str(exc_info.value)

    def test_path_variable_reused_as_path_succeeds(self):
        """Path variable can be reused in compatible contexts."""
        # Note: This test is more conceptual as paths are typically not reused
        # in patterns, but validates the type system works correctly
        query = "MATCH p = ()-[]-() WITH p RETURN p"
        gf = GraphForge()
        # Should not raise
        gf.execute(query)

    def test_relationship_reused_as_relationship_succeeds(self):
        """Relationship variable reused as relationship should succeed."""
        query = "MATCH ()-[r]-() WITH r MATCH ()-[r]-() RETURN r"
        gf = GraphForge()
        # Should not raise (though may not match at runtime)
        gf.execute(query)
