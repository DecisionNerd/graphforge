"""Integration tests for exists() and isEmpty() predicate functions."""

import pytest

from graphforge import GraphForge


class TestExistsFunction:
    """Test exists() predicate function."""

    def test_exists_property_present(self):
        """exists() returns true when property is present."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        result = gf.execute("""
            MATCH (p:Person)
            WHERE exists(p.age)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_exists_property_missing(self):
        """exists() returns false when property is missing."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        result = gf.execute("""
            MATCH (p:Person)
            WHERE exists(p.age)
            RETURN p.name AS name
        """)
        assert len(result) == 0

    def test_exists_property_null(self):
        """exists() returns false when property is explicitly NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: NULL})")
        result = gf.execute("""
            MATCH (p:Person)
            WHERE exists(p.age)
            RETURN p.name AS name
        """)
        assert len(result) == 0

    def test_exists_in_return(self):
        """exists() used in RETURN clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', email: 'alice@example.com'}),
                   (:Person {name: 'Bob'})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name, exists(p.email) AS has_email
            ORDER BY name
        """)
        assert len(result) == 2
        assert result[0]["name"].value == "Alice"
        assert result[0]["has_email"].value is True
        assert result[1]["name"].value == "Bob"
        assert result[1]["has_email"].value is False

    def test_exists_multiple_properties(self):
        """exists() with multiple property checks."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', email: 'alice@example.com', phone: '555-1234'}),
                   (:Person {name: 'Bob', email: 'bob@example.com'}),
                   (:Person {name: 'Carol'})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE exists(p.email) AND exists(p.phone)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_exists_with_relationships(self):
        """exists() on relationship properties."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'}),
                   (a)-[:KNOWS]->(c:Person {name: 'Carol'})
        """)
        result = gf.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            WHERE a.name = 'Alice' AND exists(r.since)
            RETURN b.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Bob"

    def test_exists_negation(self):
        """NOT exists() to find missing properties."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', email: 'alice@example.com'}),
                   (:Person {name: 'Bob'})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE NOT exists(p.email)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Bob"

    def test_exists_with_variable(self):
        """exists() with variable (non-property) expression."""
        gf = GraphForge()
        result = gf.execute("""
            WITH NULL AS value
            RETURN exists(value) AS result
        """)
        assert result[0]["result"].value is False

        result = gf.execute("""
            WITH 42 AS value
            RETURN exists(value) AS result
        """)
        assert result[0]["result"].value is True

    def test_exists_in_with_clause(self):
        """exists() used in WITH clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', age: 30}),
                   (:Person {name: 'Bob'})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WITH p, exists(p.age) AS has_age
            WHERE has_age = true
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"


class TestIsEmptyFunction:
    """Test isEmpty() predicate function."""

    def test_is_empty_empty_list(self):
        """isEmpty() returns true for empty list."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty([]) AS result")
        assert result[0]["result"].value is True

    def test_is_empty_non_empty_list(self):
        """isEmpty() returns false for non-empty list."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty([1, 2, 3]) AS result")
        assert result[0]["result"].value is False

    def test_is_empty_empty_string(self):
        """isEmpty() returns true for empty string."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty('') AS result")
        assert result[0]["result"].value is True

    def test_is_empty_non_empty_string(self):
        """isEmpty() returns false for non-empty string."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty('hello') AS result")
        assert result[0]["result"].value is False

    def test_is_empty_non_empty_map(self):
        """isEmpty() returns false for non-empty map."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty({key: 'value'}) AS result")
        assert result[0]["result"].value is False

    def test_is_empty_null_returns_null(self):
        """isEmpty(NULL) returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty(NULL) AS result")
        assert result[0]["result"].value is None

    def test_is_empty_in_where_clause(self):
        """isEmpty() used in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', tags: ['developer', 'manager']}),
                   (:Person {name: 'Bob', tags: []}),
                   (:Person {name: 'Carol', tags: ['designer']})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE isEmpty(p.tags)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Bob"

    def test_is_empty_with_property_list(self):
        """isEmpty() on property that is a list."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Task {title: 'Task1', comments: []}),
                   (:Task {title: 'Task2', comments: ['Good work']})
        """)
        result = gf.execute("""
            MATCH (t:Task)
            WHERE NOT isEmpty(t.comments)
            RETURN t.title AS title
        """)
        assert len(result) == 1
        assert result[0]["title"].value == "Task2"

    def test_is_empty_single_element_list(self):
        """isEmpty() returns false for single element list."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty([1]) AS result")
        assert result[0]["result"].value is False

    def test_is_empty_whitespace_string(self):
        """isEmpty() returns false for whitespace-only string."""
        gf = GraphForge()
        result = gf.execute("RETURN isEmpty('   ') AS result")
        # Whitespace is not empty
        assert result[0]["result"].value is False

    def test_is_empty_type_error_for_number(self):
        """isEmpty() raises TypeError for numeric input."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="ISEMPTY expects list, string, or map"):
            gf.execute("RETURN isEmpty(42) AS result")

    def test_is_empty_in_return_with_condition(self):
        """isEmpty() in RETURN with conditional logic."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', skills: ['Python', 'SQL']}),
                   (:Person {name: 'Bob', skills: []})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE WHEN isEmpty(p.skills)
                        THEN 'No skills listed'
                        ELSE 'Has skills'
                   END AS status
            ORDER BY name
        """)
        assert len(result) == 2
        assert result[0]["name"].value == "Alice"
        assert result[0]["status"].value == "Has skills"
        assert result[1]["name"].value == "Bob"
        assert result[1]["status"].value == "No skills listed"


class TestExistsIsEmptyCombined:
    """Test exists() and isEmpty() used together."""

    def test_exists_and_is_empty_combined(self):
        """Use both exists() and isEmpty() in same query."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', email: 'alice@example.com', tags: ['dev']}),
                   (:Person {name: 'Bob', email: 'bob@example.com', tags: []}),
                   (:Person {name: 'Carol', tags: ['manager']})
        """)
        result = gf.execute("""
            MATCH (p:Person)
            WHERE exists(p.email) AND NOT isEmpty(p.tags)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"

    def test_exists_check_before_is_empty(self):
        """Check property exists before checking if empty."""
        gf = GraphForge()
        gf.execute("""
            CREATE (:Person {name: 'Alice', hobbies: ['reading']}),
                   (:Person {name: 'Bob', hobbies: []}),
                   (:Person {name: 'Carol'})
        """)
        # Only check isEmpty if property exists
        result = gf.execute("""
            MATCH (p:Person)
            WHERE exists(p.hobbies) AND NOT isEmpty(p.hobbies)
            RETURN p.name AS name
        """)
        assert len(result) == 1
        assert result[0]["name"].value == "Alice"
