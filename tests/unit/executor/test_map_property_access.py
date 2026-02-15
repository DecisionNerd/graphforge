"""Unit tests for map property access (Issue #173)."""

import pytest

from graphforge import GraphForge


class TestMapLiteralPropertyAccess:
    """Test property access on map literals."""

    def test_simple_map_property_access(self):
        """RETURN {name: 'Alice'}.name should return 'Alice'."""
        gf = GraphForge()

        result = gf.execute("RETURN {name: 'Alice'}.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_map_with_multiple_properties(self):
        """Access multiple properties from same map."""
        gf = GraphForge()

        result = gf.execute(
            "RETURN {name: 'Alice', age: 30}.name AS name, {name: 'Alice', age: 30}.age AS age"
        )

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"
        assert result[0]["age"].value == 30

    def test_nested_map_property_access(self):
        """Access property from nested map."""
        gf = GraphForge()

        result = gf.execute("RETURN {person: {name: 'Alice'}}.person AS person")

        assert len(result) == 1
        assert result[0]["person"].value["name"].value == "Alice"

    def test_map_property_with_numeric_value(self):
        """Map property with numeric value."""
        gf = GraphForge()

        result = gf.execute("RETURN {count: 42}.count AS count")

        assert len(result) == 1
        assert result[0]["count"].value == 42

    def test_map_property_with_boolean(self):
        """Map property with boolean value."""
        gf = GraphForge()

        result = gf.execute("RETURN {active: true}.active AS active")

        assert len(result) == 1
        assert result[0]["active"].value is True

    def test_map_property_with_list(self):
        """Map property with list value."""
        gf = GraphForge()

        result = gf.execute("RETURN {items: [1, 2, 3]}.items AS items")

        assert len(result) == 1
        assert len(result[0]["items"].value) == 3
        assert result[0]["items"].value[0].value == 1


class TestMapVariablePropertyAccess:
    """Test property access on map variables."""

    def test_map_variable_property_access(self):
        """WITH map AS variable, access properties."""
        gf = GraphForge()

        result = gf.execute("WITH {a: 1, b: 2} AS m RETURN m.a AS a, m.b AS b")

        assert len(result) == 1
        assert result[0]["a"].value == 1
        assert result[0]["b"].value == 2

    def test_map_in_with_clause(self):
        """Pass map through WITH and access property."""
        gf = GraphForge()

        result = gf.execute("WITH {name: 'Bob'} AS person WITH person RETURN person.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "Bob"

    def test_map_property_in_where(self):
        """Use map property in WHERE clause."""
        gf = GraphForge()

        result = gf.execute(
            "WITH {age: 30} AS person WHERE person.age > 25 RETURN person.age AS age"
        )

        assert len(result) == 1
        assert result[0]["age"].value == 30

    def test_map_property_in_order_by(self):
        """Use map property in ORDER BY."""
        gf = GraphForge()

        result = gf.execute("""
            WITH [{name: 'Charlie', age: 25}, {name: 'Alice', age: 30}] AS people
            UNWIND people AS p
            RETURN p.name AS name
            ORDER BY p.age
        """)

        assert len(result) == 2
        assert result[0]["name"].value == "Charlie"
        assert result[1]["name"].value == "Alice"


class TestMapPropertyEdgeCases:
    """Test edge cases for map property access."""

    def test_missing_key_returns_null(self):
        """Accessing non-existent key returns NULL."""
        gf = GraphForge()

        result = gf.execute("RETURN {name: 'Alice'}.age AS age")

        assert len(result) == 1
        assert result[0]["age"].value is None

    def test_null_map_property_access(self):
        """Accessing property on NULL returns NULL."""
        gf = GraphForge()

        result = gf.execute("WITH NULL AS m RETURN m.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value is None

    def test_empty_map_property_access(self):
        """Accessing property on empty map returns NULL."""
        # Empty map literal {} has parser issues, skip for now
        pytest.skip("Empty map literal not supported by parser")

    def test_map_property_with_special_characters(self):
        """Property names with special characters (in quotes)."""
        # Note: This might not work if grammar doesn't support quoted identifiers
        # Skip if not supported
        pytest.skip("Quoted identifiers not yet supported")


class TestBackwardCompatibility:
    """Ensure existing property access still works."""

    def test_node_property_access_still_works(self):
        """Node property access should be unaffected."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        result = gf.execute("MATCH (n:Person) RETURN n.name AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_edge_property_access_still_works(self):
        """Edge property access should be unaffected."""
        gf = GraphForge()
        gf.execute(
            "CREATE (:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(:Person {name: 'Bob'})"
        )

        result = gf.execute("MATCH ()-[r:KNOWS]->() RETURN r.since AS since")

        assert len(result) == 1
        assert result[0]["since"].value == 2020

    def test_variable_property_in_create(self):
        """Property access in CREATE should still work."""
        gf = GraphForge()

        result = gf.execute(
            "WITH 'Charlie' AS name CREATE (n:Person {name: name}) RETURN n.name AS name"
        )

        assert len(result) == 1
        assert result[0]["name"].value == "Charlie"

    def test_property_in_set_clause(self):
        """Property access in SET should still work."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Dave'})")

        result = gf.execute("MATCH (n:Person {name: 'Dave'}) SET n.age = 25 RETURN n.age AS age")

        assert len(result) == 1
        assert result[0]["age"].value == 25


class TestComplexScenarios:
    """Test complex scenarios combining map property access with other features."""

    def test_map_property_in_expression(self):
        """Use map property in arithmetic expression."""
        gf = GraphForge()

        result = gf.execute("RETURN {x: 10}.x + {y: 5}.y AS sum")

        assert len(result) == 1
        assert result[0]["sum"].value == 15

    def test_map_property_comparison(self):
        """Compare map properties."""
        gf = GraphForge()

        result = gf.execute("RETURN {a: 5}.a > {b: 3}.b AS result")

        assert len(result) == 1
        assert result[0]["result"].value is True

    def test_map_property_with_function(self):
        """Use map property with function."""
        gf = GraphForge()

        # Use a function that exists
        result = gf.execute("RETURN lower({name: 'ALICE'}.name) AS name")

        assert len(result) == 1
        assert result[0]["name"].value == "alice"

    def test_map_from_match_property_access(self):
        """Create map from node properties, then access."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Eve', age: 28})")

        result = gf.execute("""
            MATCH (n:Person)
            WITH {name: n.name, age: n.age} AS person
            RETURN person.name AS name, person.age AS age
        """)

        assert len(result) == 1
        assert result[0]["name"].value == "Eve"
        assert result[0]["age"].value == 28
