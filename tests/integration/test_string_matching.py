"""Integration tests for string matching operators (issue #28).

Tests for STARTS WITH, ENDS WITH, and CONTAINS operators.
"""

from graphforge import GraphForge
from graphforge.types.values import CypherNull


class TestStartsWith:
    """Tests for STARTS WITH operator."""

    def test_starts_with_matching_prefix(self):
        """STARTS WITH with matching prefix."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'Al'
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_starts_with_non_matching_prefix(self):
        """STARTS WITH with non-matching prefix."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'Bo'
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_starts_with_case_sensitive(self):
        """STARTS WITH is case-sensitive."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'al'
            RETURN p.name AS name
        """)

        # Should not match due to case difference
        assert len(results) == 0

    def test_starts_with_empty_string(self):
        """STARTS WITH empty string matches all."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH ''
            RETURN p.name AS name
        """)

        # Empty prefix matches all strings
        assert len(results) == 1

    def test_starts_with_full_string(self):
        """STARTS WITH the full string."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'Alice'
            RETURN p.name AS name
        """)

        assert len(results) == 1


class TestEndsWith:
    """Tests for ENDS WITH operator."""

    def test_ends_with_matching_suffix(self):
        """ENDS WITH with matching suffix."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {email: 'alice@example.com'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email ENDS WITH '.com'
            RETURN p.email AS email
        """)

        assert len(results) == 1
        assert results[0]["email"].value == "alice@example.com"

    def test_ends_with_non_matching_suffix(self):
        """ENDS WITH with non-matching suffix."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {email: 'alice@example.com'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email ENDS WITH '.org'
            RETURN p.email AS email
        """)

        assert len(results) == 0

    def test_ends_with_case_sensitive(self):
        """ENDS WITH is case-sensitive."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {email: 'alice@example.COM'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email ENDS WITH '.com'
            RETURN p.email AS email
        """)

        # Should not match due to case difference
        assert len(results) == 0

    def test_ends_with_empty_string(self):
        """ENDS WITH empty string matches all."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {email: 'alice@example.com'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email ENDS WITH ''
            RETURN p.email AS email
        """)

        assert len(results) == 1

    def test_ends_with_full_string(self):
        """ENDS WITH the full string."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {email: 'alice@example.com'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email ENDS WITH 'alice@example.com'
            RETURN p.email AS email
        """)

        assert len(results) == 1


class TestContains:
    """Tests for CONTAINS operator."""

    def test_contains_matching_substring(self):
        """CONTAINS with matching substring."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {description: 'software engineer'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.description CONTAINS 'engineer'
            RETURN p.description AS desc
        """)

        assert len(results) == 1
        assert results[0]["desc"].value == "software engineer"

    def test_contains_non_matching_substring(self):
        """CONTAINS with non-matching substring."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {description: 'software engineer'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.description CONTAINS 'doctor'
            RETURN p.description AS desc
        """)

        assert len(results) == 0

    def test_contains_case_sensitive(self):
        """CONTAINS is case-sensitive."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {description: 'Software Engineer'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.description CONTAINS 'software'
            RETURN p.description AS desc
        """)

        # Should not match due to case difference
        assert len(results) == 0

    def test_contains_empty_string(self):
        """CONTAINS empty string matches all."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {description: 'software engineer'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.description CONTAINS ''
            RETURN p.description AS desc
        """)

        assert len(results) == 1

    def test_contains_full_string(self):
        """CONTAINS the full string."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {description: 'engineer'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.description CONTAINS 'engineer'
            RETURN p.description AS desc
        """)

        assert len(results) == 1


class TestNullHandling:
    """Tests for NULL handling in string matching."""

    def test_starts_with_null_property(self):
        """STARTS WITH with NULL property."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.middleName STARTS WITH 'M'
            RETURN p.name AS name
        """)

        # NULL property doesn't match
        assert len(results) == 0

    def test_ends_with_null_property(self):
        """ENDS WITH with NULL property."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.email ENDS WITH '.com'
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_contains_null_property(self):
        """CONTAINS with NULL property."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.bio CONTAINS 'engineer'
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_string_match_returns_null_in_return(self):
        """String matching with NULL returns NULL in RETURN."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name, p.email ENDS WITH '.com' AS has_com_email
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert isinstance(results[0]["has_com_email"], CypherNull)


class TestCombinations:
    """Tests for combining string matching with other operators."""

    def test_starts_with_and_ends_with(self):
        """Combine STARTS WITH and ENDS WITH."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice Smith'}),
                   (b:Person {name: 'Alice Jones'}),
                   (c:Person {name: 'Bob Smith'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'Alice' AND p.name ENDS WITH 'Smith'
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice Smith"

    def test_contains_or_contains(self):
        """Multiple CONTAINS with OR."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {bio: 'software engineer'}),
                   (b:Person {bio: 'data scientist'}),
                   (c:Person {bio: 'product manager'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.bio CONTAINS 'engineer' OR p.bio CONTAINS 'scientist'
            RETURN p.bio AS bio
            ORDER BY bio
        """)

        assert len(results) == 2
        assert results[0]["bio"].value == "data scientist"
        assert results[1]["bio"].value == "software engineer"

    def test_not_starts_with(self):
        """Negation with NOT STARTS WITH."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {email: 'alice@spam.com'}),
                   (b:Person {email: 'bob@example.com'}),
                   (c:Person {email: 'charlie@spam.com'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE NOT p.email ENDS WITH '@spam.com'
            RETURN p.email AS email
        """)

        assert len(results) == 1
        assert results[0]["email"].value == "bob@example.com"

    def test_string_match_with_comparison(self):
        """Combine string matching with other comparisons."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30, email: 'alice@example.com'}),
                   (b:Person {name: 'Bob', age: 25, email: 'bob@example.org'}),
                   (c:Person {name: 'Alice', age: 20, email: 'alice2@example.com'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'Alice'
              AND p.age > 25
              AND p.email ENDS WITH '.com'
            RETURN p.name AS name, p.age AS age
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30


class TestMultipleNodes:
    """Tests for string matching across multiple nodes."""

    def test_filter_multiple_nodes(self):
        """Filter multiple nodes with string matching."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice Johnson'}),
                   (b:Person {name: 'Bob Johnson'}),
                   (c:Person {name: 'Alice Williams'}),
                   (d:Person {name: 'David Johnson'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name ENDS WITH 'Johnson'
            RETURN p.name AS name
            ORDER BY name
        """)

        assert len(results) == 3
        assert results[0]["name"].value == "Alice Johnson"
        assert results[1]["name"].value == "Bob Johnson"
        assert results[2]["name"].value == "David Johnson"

    def test_count_matching_nodes(self):
        """Count nodes matching string pattern."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {title: 'Senior Engineer'}),
                   (b:Person {title: 'Junior Engineer'}),
                   (c:Person {title: 'Senior Manager'}),
                   (d:Person {title: 'Engineer'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.title CONTAINS 'Engineer'
            RETURN count(p) AS count
        """)

        assert results[0]["count"].value == 3


class TestEmptyStrings:
    """Tests for empty string handling."""

    def test_empty_string_starts_with_pattern(self):
        """Empty string with STARTS WITH pattern."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: ''})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH 'A'
            RETURN p.name AS name
        """)

        # Empty string doesn't start with 'A'
        assert len(results) == 0

    def test_empty_string_ends_with_pattern(self):
        """Empty string with ENDS WITH pattern."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: ''})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name ENDS WITH 'z'
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_empty_string_contains_pattern(self):
        """Empty string with CONTAINS pattern."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: ''})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name CONTAINS 'x'
            RETURN p.name AS name
        """)

        assert len(results) == 0

    def test_empty_string_with_empty_pattern(self):
        """Empty string with empty pattern matches."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: ''})")

        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.name STARTS WITH ''
            RETURN count(p) AS count
        """)

        # Empty string starts with empty pattern
        assert results[0]["count"].value == 1
