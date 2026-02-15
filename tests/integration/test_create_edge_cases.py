"""Integration tests for CREATE edge cases (Feature 5).

Tests for list properties, map properties, and mixed numeric types in CREATE.
"""

import pytest

from graphforge import GraphForge


@pytest.fixture
def empty_graph():
    """Create an empty graph for testing."""
    return GraphForge()


@pytest.mark.integration
class TestCreateWithListProperties:
    """Tests for CREATE with list properties."""

    def test_create_with_simple_list(self, empty_graph):
        """CREATE with simple list property."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Alice',
                hobbies: ['reading', 'coding', 'hiking']
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN n.hobbies AS hobbies
        """)

        assert len(results) == 1
        hobbies = results[0]["hobbies"].value
        assert isinstance(hobbies, list)
        assert len(hobbies) == 3
        # Check that values are CypherString objects
        assert all(hasattr(h, "value") for h in hobbies)
        assert [h.value for h in hobbies] == ["reading", "coding", "hiking"]

    def test_create_with_numeric_list(self, empty_graph):
        """CREATE with list of numbers."""
        empty_graph.execute("""
            CREATE (n:Data {
                name: 'measurements',
                values: [1, 2, 3, 4, 5]
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Data {name: 'measurements'})
            RETURN n.values AS values
        """)

        assert len(results) == 1
        values = results[0]["values"].value
        assert isinstance(values, list)
        assert len(values) == 5
        assert [v.value for v in values] == [1, 2, 3, 4, 5]

    def test_create_with_mixed_type_list(self, empty_graph):
        """CREATE with list of mixed types (no booleans due to parser issue)."""
        empty_graph.execute("""
            CREATE (n:Mixed {
                name: 'data',
                items: ['text', 42, 3.14]
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Mixed {name: 'data'})
            RETURN n.items AS items
        """)

        assert len(results) == 1
        items = results[0]["items"].value
        assert isinstance(items, list)
        assert len(items) == 3
        values = [item.value for item in items]
        assert values == ["text", 42, 3.14]

    @pytest.mark.skip(reason="Empty list handling needs investigation")
    def test_create_with_empty_list(self, empty_graph):
        """CREATE with empty list property."""
        empty_graph.execute("""
            CREATE (n:Empty {
                name: 'test',
                items: []
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Empty {name: 'test'})
            RETURN n.items AS items
        """)

        assert len(results) == 1
        items = results[0]["items"].value
        assert isinstance(items, list)
        assert len(items) == 0


@pytest.mark.integration
class TestCreateWithMapProperties:
    """Tests for CREATE with map (nested) properties."""

    def test_create_with_simple_map(self, empty_graph):
        """CREATE with simple map property."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Bob',
                address: {city: 'NYC', zip: 10001}
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN n.address AS address
        """)

        assert len(results) == 1
        address = results[0]["address"].value
        assert isinstance(address, dict)
        assert "city" in address
        assert "zip" in address
        assert address["city"].value == "NYC"
        assert address["zip"].value == 10001

    def test_create_with_nested_map(self, empty_graph):
        """CREATE with nested map property."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Charlie',
                contact: {
                    email: 'charlie@example.com',
                    phone: {
                        home: '555-1234',
                        work: '555-5678'
                    }
                }
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Person {name: 'Charlie'})
            RETURN n.contact AS contact
        """)

        assert len(results) == 1
        contact = results[0]["contact"].value
        assert isinstance(contact, dict)
        assert contact["email"].value == "charlie@example.com"
        assert isinstance(contact["phone"].value, dict)
        assert contact["phone"].value["home"].value == "555-1234"

    def test_create_with_map_containing_list(self, empty_graph):
        """CREATE with map containing list."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Diana',
                profile: {
                    age: 28,
                    skills: ['Python', 'Java', 'Go']
                }
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Person {name: 'Diana'})
            RETURN n.profile AS profile
        """)

        assert len(results) == 1
        profile = results[0]["profile"].value
        assert isinstance(profile, dict)
        assert profile["age"].value == 28
        assert isinstance(profile["skills"].value, list)
        assert len(profile["skills"].value) == 3


@pytest.mark.integration
class TestCreateWithMixedNumericTypes:
    """Tests for CREATE with mixed numeric types."""

    def test_create_with_int_and_float(self, empty_graph):
        """CREATE with both integer and float properties."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Eve',
                age: 30,
                score: 98.5,
                rating: 4.0
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Person {name: 'Eve'})
            RETURN n.age AS age, n.score AS score, n.rating AS rating
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherFloat, CypherInt

        assert isinstance(results[0]["age"], CypherInt)
        assert results[0]["age"].value == 30

        assert isinstance(results[0]["score"], CypherFloat)
        assert abs(results[0]["score"].value - 98.5) < 0.001

        assert isinstance(results[0]["rating"], CypherFloat)
        assert abs(results[0]["rating"].value - 4.0) < 0.001

    def test_create_with_boolean(self, empty_graph):
        """CREATE with boolean property."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Frank',
                active: true,
                verified: false
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Person {name: 'Frank'})
            RETURN n.active AS active, n.verified AS verified
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherBool

        assert isinstance(results[0]["active"], CypherBool)
        assert results[0]["active"].value is True

        assert isinstance(results[0]["verified"], CypherBool)
        assert results[0]["verified"].value is False

    def test_create_with_all_types(self, empty_graph):
        """CREATE with all property types."""
        empty_graph.execute("""
            CREATE (n:Complex {
                str_prop: 'text',
                int_prop: 42,
                float_prop: 3.14,
                bool_prop: true,
                null_prop: null,
                list_prop: [1, 2, 3],
                map_prop: {key: 'value'}
            })
        """)

        results = empty_graph.execute("""
            MATCH (n:Complex)
            RETURN n
        """)

        assert len(results) == 1
        node = results[0]["n"]

        # Verify all types are correct
        from graphforge.types.values import (
            CypherBool,
            CypherFloat,
            CypherInt,
            CypherList,
            CypherMap,
            CypherString,
        )

        assert isinstance(node.properties["str_prop"], CypherString)
        assert isinstance(node.properties["int_prop"], CypherInt)
        assert isinstance(node.properties["float_prop"], CypherFloat)
        assert isinstance(node.properties["bool_prop"], CypherBool)
        # Per openCypher spec, NULL properties are not stored
        assert "null_prop" not in node.properties
        assert isinstance(node.properties["list_prop"], CypherList)
        assert isinstance(node.properties["map_prop"], CypherMap)


@pytest.mark.integration
class TestCreateRelationshipWithComplexProperties:
    """Tests for CREATE relationship with complex properties."""

    def test_create_relationship_with_list_property(self, empty_graph):
        """CREATE relationship with list property."""
        # Use comma-separated patterns in single CREATE
        empty_graph.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (a)-[:KNOWS {
                       since: 2020,
                       contexts: ['work', 'school', 'gym']
                   }]->(b)
        """)

        results = empty_graph.execute("""
            MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
            RETURN r.contexts AS contexts
        """)

        assert len(results) == 1
        contexts = results[0]["contexts"].value
        assert isinstance(contexts, list)
        assert len(contexts) == 3

    def test_create_relationship_with_map_property(self, empty_graph):
        """CREATE relationship with map property."""
        # Use comma-separated patterns in single CREATE
        empty_graph.execute("""
            CREATE (a:Person {name: 'Charlie'}),
                   (b:Person {name: 'Diana'}),
                   (a)-[:WORKED_WITH {
                       project: {
                           name: 'GraphForge',
                           year: 2024
                       }
                   }]->(b)
        """)

        results = empty_graph.execute("""
            MATCH (a:Person {name: 'Charlie'})-[r:WORKED_WITH]->(b:Person {name: 'Diana'})
            RETURN r.project AS project
        """)

        assert len(results) == 1
        project = results[0]["project"].value
        assert isinstance(project, dict)
        assert project["name"].value == "GraphForge"
        assert project["year"].value == 2024


@pytest.mark.integration
class TestCreateNullProperties:
    """Tests for CREATE with NULL property handling (Issue #146)."""

    def test_create_node_with_null_property_not_stored(self, empty_graph):
        """CREATE with NULL property should not store the property."""
        empty_graph.execute("CREATE (n:Node {name: 'Alice', age: null})")
        results = empty_graph.execute("MATCH (n:Node) RETURN n")
        assert len(results) == 1
        node = results[0]["n"]
        # name should exist, age should not
        assert "name" in node.properties
        assert "age" not in node.properties

    def test_create_node_with_all_null_properties(self, empty_graph):
        """CREATE with all NULL properties should create node without properties."""
        empty_graph.execute("CREATE (n:Node {a: null, b: null})")
        results = empty_graph.execute("MATCH (n:Node) RETURN n")
        assert len(results) == 1
        node = results[0]["n"]
        # Node should exist but have no properties
        assert len(node.properties) == 0

    def test_create_node_with_mixed_null_and_values(self, empty_graph):
        """CREATE with mix of NULL and non-NULL properties stores only non-NULL."""
        empty_graph.execute("""
            CREATE (n:Person {
                name: 'Bob',
                age: 30,
                email: null,
                active: true,
                phone: null
            })
        """)
        results = empty_graph.execute("MATCH (n:Person) RETURN n")
        assert len(results) == 1
        node = results[0]["n"]
        # Only non-NULL properties should exist
        assert "name" in node.properties
        assert "age" in node.properties
        assert "active" in node.properties
        assert "email" not in node.properties
        assert "phone" not in node.properties

    def test_create_relationship_with_null_property_not_stored(self, empty_graph):
        """CREATE relationship with NULL property should not store the property."""
        empty_graph.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'}),
                   (a)-[:KNOWS {since: 2020, context: null}]->(b)
        """)
        results = empty_graph.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            RETURN r
        """)
        assert len(results) == 1
        rel = results[0]["r"]
        # since should exist, context should not
        assert "since" in rel.properties
        assert "context" not in rel.properties


@pytest.mark.integration
class TestCreateDuplicateVariables:
    """Tests for CREATE with duplicate variable validation (Issue #146)."""

    def test_create_comma_separated_patterns_rebind_allowed(self, empty_graph):
        """CREATE with comma-separated patterns can rebind variables (different patterns)."""
        # This is valid - comma-separated patterns are independent
        empty_graph.execute("CREATE (a:Person {name: 'Alice'}), (a:Person {name: 'Bob'})")
        results = empty_graph.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY n.name")
        # Both nodes should be created
        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Bob"

    def test_create_self_loop_allowed(self, empty_graph):
        """CREATE self-loop using same variable for both ends is valid."""
        # Self-loops are valid in openCypher
        empty_graph.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(a)")
        results = empty_graph.execute("MATCH (a:Person)-[r:KNOWS]->(a) RETURN a.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_create_duplicate_relationship_variables_raises_error(self, empty_graph):
        """CREATE with same variable for two relationships should raise ValueError."""
        with pytest.raises(ValueError, match="used multiple times for relationships"):
            empty_graph.execute("""
                CREATE (a:Person)-[r:KNOWS]->(b:Person)-[r:LIKES]->(c:Person)
            """)

    def test_create_node_and_relationship_same_variable_raises_error(self, empty_graph):
        """CREATE with same variable for node and relationship should raise ValueError."""
        with pytest.raises(ValueError, match="both node and relationship"):
            empty_graph.execute("CREATE (x:Person)-[x:KNOWS]->(b:Person)")


@pytest.mark.integration
class TestCreateUndefinedVariables:
    """Tests for CREATE with undefined variable detection (Issue #146)."""

    def test_create_node_with_undefined_variable_in_property(self, empty_graph):
        """CREATE with undefined variable in property expression should raise error."""
        with pytest.raises((ValueError, KeyError), match="undefined_var|not bound"):
            empty_graph.execute("CREATE (n:Person {name: undefined_var})")

    def test_create_relationship_with_undefined_variable_in_property(self, empty_graph):
        """CREATE relationship with undefined variable in property should raise error."""
        with pytest.raises((ValueError, KeyError), match="undefined_var|not bound"):
            empty_graph.execute("""
                CREATE (a:Person)-[:KNOWS {since: undefined_var}]->(b:Person)
            """)


@pytest.mark.integration
class TestCreatePropertyExpressions:
    """Tests for CREATE with computed property expressions (Issue #146)."""

    def test_create_node_with_arithmetic_expression(self, empty_graph):
        """CREATE with arithmetic expression in property."""
        empty_graph.execute("CREATE (n:Node {value: 1 + 2})")
        results = empty_graph.execute("MATCH (n:Node) RETURN n.value AS value")
        assert len(results) == 1
        assert results[0]["value"].value == 3

    def test_create_node_with_string_concatenation(self, empty_graph):
        """CREATE with string concatenation in property."""
        empty_graph.execute("CREATE (n:Person {name: 'Alice' + ' ' + 'Smith'})")
        results = empty_graph.execute("MATCH (n:Person) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice Smith"

    def test_create_relationship_with_computed_property(self, empty_graph):
        """CREATE relationship with computed property expression."""
        empty_graph.execute("""
            CREATE (a:Person)-[:KNOWS {strength: 5 * 2}]->(b:Person)
        """)
        results = empty_graph.execute("""
            MATCH ()-[r:KNOWS]->()
            RETURN r.strength AS strength
        """)
        assert len(results) == 1
        assert results[0]["strength"].value == 10
