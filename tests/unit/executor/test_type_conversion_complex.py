"""Unit tests for type conversion functions with complex types (v0.4.0)."""

from graphforge.api import GraphForge
from graphforge.types.values import CypherNull


class TestToBooleanComplexTypes:
    """Tests for toBoolean() with complex types."""

    def test_toboolean_empty_list_returns_null(self):
        """toBoolean([]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toBoolean([]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_toboolean_nonempty_list_returns_null(self):
        """toBoolean([true]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toBoolean([true]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_toboolean_list_with_multiple_elements_returns_null(self):
        """toBoolean([1, 2, 3]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toBoolean([1, 2, 3]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_toboolean_map_returns_null(self):
        """toBoolean({key: true}) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toBoolean({key: true}) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_toboolean_node_returns_null(self):
        """toBoolean(node) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        results = gf.execute(
            """
            MATCH (n:Person)
            RETURN toBoolean(n) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_toboolean_relationship_returns_null(self):
        """toBoolean(relationship) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS]->(b:Person)")
        results = gf.execute(
            """
            MATCH ()-[r:KNOWS]->()
            RETURN toBoolean(r) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)


class TestToIntegerComplexTypes:
    """Tests for toInteger() with complex types."""

    def test_tointeger_empty_list_returns_null(self):
        """toInteger([]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toInteger([]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tointeger_single_element_list_returns_null(self):
        """toInteger([5]) returns NULL (not 5)."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toInteger([5]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tointeger_list_with_multiple_elements_returns_null(self):
        """toInteger([1, 2, 3]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toInteger([1, 2, 3]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tointeger_map_returns_null(self):
        """toInteger({value: 42}) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toInteger({value: 42}) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tointeger_node_returns_null(self):
        """toInteger(node) returns NULL (use id(node) instead)."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {id: 123})")
        results = gf.execute(
            """
            MATCH (n:Person)
            RETURN toInteger(n) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tointeger_relationship_returns_null(self):
        """toInteger(relationship) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS {weight: 5}]->(b:Person)")
        results = gf.execute(
            """
            MATCH ()-[r:KNOWS]->()
            RETURN toInteger(r) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)


class TestToFloatComplexTypes:
    """Tests for toFloat() with complex types."""

    def test_tofloat_empty_list_returns_null(self):
        """toFloat([]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toFloat([]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tofloat_single_element_list_returns_null(self):
        """toFloat([3.14]) returns NULL (not 3.14)."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toFloat([3.14]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tofloat_list_with_multiple_elements_returns_null(self):
        """toFloat([1.1, 2.2]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toFloat([1.1, 2.2]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tofloat_map_returns_null(self):
        """toFloat({value: 1.5}) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toFloat({value: 1.5}) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tofloat_node_returns_null(self):
        """toFloat(node) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {score: 98.5})")
        results = gf.execute(
            """
            MATCH (n:Person)
            RETURN toFloat(n) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tofloat_relationship_returns_null(self):
        """toFloat(relationship) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2020.5}]->(b:Person)")
        results = gf.execute(
            """
            MATCH ()-[r:KNOWS]->()
            RETURN toFloat(r) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)


class TestToStringComplexTypes:
    """Tests for toString() with complex types."""

    def test_tostring_empty_list_returns_null(self):
        """toString([]) returns NULL (not '[]')."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toString([]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tostring_nonempty_list_returns_null(self):
        """toString([1, 2, 3]) returns NULL (not '[1, 2, 3]')."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toString([1, 2, 3]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tostring_string_list_returns_null(self):
        """toString(['a', 'b']) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toString(['a', 'b']) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tostring_map_returns_null(self):
        """toString({key: 'value'}) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toString({key: 'value'}) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tostring_node_returns_null(self):
        """toString(node) returns NULL (use properties() instead)."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        results = gf.execute(
            """
            MATCH (n:Person)
            RETURN toString(n) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tostring_relationship_returns_null(self):
        """toString(relationship) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2020}]->(b:Person)")
        results = gf.execute(
            """
            MATCH ()-[r:KNOWS]->()
            RETURN toString(r) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)


class TestEdgeCasesAndNullHandling:
    """Edge cases for type conversion with complex types."""

    def test_toboolean_null_in_list_returns_null(self):
        """toBoolean([null]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toBoolean([null]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tointeger_nested_list_returns_null(self):
        """toInteger([[1, 2], [3, 4]]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toInteger([[1, 2], [3, 4]]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tostring_nested_map_returns_null(self):
        """toString({nested: {key: 'value'}}) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toString({nested: {key: 'value'}}) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)

    def test_tofloat_mixed_type_list_returns_null(self):
        """toFloat([1, 'two', 3.0]) returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN toFloat([1, 'two', 3.0]) AS result
            """
        )
        assert isinstance(results[0]["result"], CypherNull)


class TestConversionConsistency:
    """Test that all conversion functions handle complex types consistently."""

    def test_all_conversions_on_same_list_return_null(self):
        """All conversion functions return NULL for the same list."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            WITH [1, 2, 3] AS mylist
            RETURN
                toBoolean(mylist) AS as_bool,
                toInteger(mylist) AS as_int,
                toFloat(mylist) AS as_float,
                toString(mylist) AS as_str
            """
        )
        assert isinstance(results[0]["as_bool"], CypherNull)
        assert isinstance(results[0]["as_int"], CypherNull)
        assert isinstance(results[0]["as_float"], CypherNull)
        assert isinstance(results[0]["as_str"], CypherNull)

    def test_all_conversions_on_same_map_return_null(self):
        """All conversion functions return NULL for the same map."""
        gf = GraphForge()
        gf.execute("CREATE (:Node)")
        results = gf.execute(
            """
            MATCH (n:Node)
            WITH {key: 'value'} AS mymap
            RETURN
                toBoolean(mymap) AS as_bool,
                toInteger(mymap) AS as_int,
                toFloat(mymap) AS as_float,
                toString(mymap) AS as_str
            """
        )
        assert isinstance(results[0]["as_bool"], CypherNull)
        assert isinstance(results[0]["as_int"], CypherNull)
        assert isinstance(results[0]["as_float"], CypherNull)
        assert isinstance(results[0]["as_str"], CypherNull)

    def test_all_conversions_on_same_node_return_null(self):
        """All conversion functions return NULL for the same node."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        results = gf.execute(
            """
            MATCH (n:Person)
            RETURN
                toBoolean(n) AS as_bool,
                toInteger(n) AS as_int,
                toFloat(n) AS as_float,
                toString(n) AS as_str
            """
        )
        assert isinstance(results[0]["as_bool"], CypherNull)
        assert isinstance(results[0]["as_int"], CypherNull)
        assert isinstance(results[0]["as_float"], CypherNull)
        assert isinstance(results[0]["as_str"], CypherNull)
