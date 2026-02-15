"""Comprehensive edge case tests for MERGE behavior.

This test suite focuses on edge cases that can break MERGE semantics:
- NULL property handling (NULL never matches NULL per openCypher)
- Multi-property matching (3+ properties with various combinations)
- Property type mismatches
- Mixed NULL and non-NULL properties

These tests ensure MERGE correctly implements openCypher specification for
pattern matching and node creation.
"""

from graphforge import GraphForge


class TestNullPropertyHandling:
    """Test NULL property handling in MERGE patterns.

    Per openCypher spec, NULL in property comparisons returns NULL (not True),
    which means pattern match should fail and node should be created.
    """

    def test_merge_null_property_never_matches_null(self):
        """Core NULL semantics: NULL never matches NULL."""
        gf = GraphForge()

        # First MERGE creates node with NULL property
        gf.execute("""
            CREATE (p:Person {name: 'Alice', age: NULL})
        """)

        # MERGE with NULL should not match existing node, should create new one
        results = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: NULL})
            RETURN p
        """)

        assert len(results) == 1

        # Total count should be 2 (original + newly created)
        count_result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_null_pattern_creates_node(self):
        """NULL in pattern always creates node, never matches."""
        gf = GraphForge()

        # Create node with actual age value
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")

        # MERGE with NULL age should NOT match the node with age=25
        results = gf.execute("""
            MERGE (p:Person {name: 'Bob', age: NULL})
            RETURN p.age AS age
        """)

        assert len(results) == 1
        # The new node has NULL age
        assert results[0]["age"].value is None

        # Should have 2 nodes total
        count_result = gf.execute("MATCH (p:Person {name: 'Bob'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_null_node_property_no_match(self):
        """NULL in node property doesn't match non-NULL pattern."""
        gf = GraphForge()

        # Create node with NULL age
        gf.execute("CREATE (:Person {name: 'Charlie', age: NULL})")

        # MERGE with non-NULL age should NOT match
        results = gf.execute("""
            MERGE (p:Person {name: 'Charlie', age: 30})
            RETURN p.age AS age
        """)

        assert len(results) == 1
        # The new node has age=30
        assert results[0]["age"].value == 30

        # Should have 2 nodes
        count_result = gf.execute("MATCH (p:Person {name: 'Charlie'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_mixed_null_non_null_properties(self):
        """Mix of NULL and non-NULL properties."""
        gf = GraphForge()

        # Create node with name='Diana', age=NULL, city='NYC'
        gf.execute("""
            CREATE (:Person {name: 'Diana', age: NULL, city: 'NYC'})
        """)

        # MERGE with same name and city, but NULL age should NOT match
        results = gf.execute("""
            MERGE (p:Person {name: 'Diana', age: NULL, city: 'NYC'})
            RETURN p
        """)

        assert len(results) == 1

        # Should have 2 nodes
        count_result = gf.execute("MATCH (p:Person {name: 'Diana'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_null_with_on_create(self):
        """NULL with ON CREATE SET."""
        gf = GraphForge()

        # First MERGE creates node with NULL, then sets property
        results = gf.execute("""
            MERGE (p:Person {name: 'Eve', status: NULL})
            ON CREATE SET p.created = true
            RETURN p.created AS created
        """)

        assert len(results) == 1
        assert results[0]["created"].value is True

        # Second MERGE should also create (NULL doesn't match NULL)
        results2 = gf.execute("""
            MERGE (p:Person {name: 'Eve', status: NULL})
            ON CREATE SET p.created = true
            RETURN p.created AS created
        """)

        assert len(results2) == 1
        assert results2[0]["created"].value is True

        # Should have 2 nodes
        count_result = gf.execute("MATCH (p:Person {name: 'Eve'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2


class TestMultiPropertyMatching:
    """Test MERGE with multiple properties (3+ properties)."""

    def test_merge_three_properties_exact_match(self):
        """Three properties all match exactly."""
        gf = GraphForge()

        # Create node with 3 properties
        gf.execute("""
            CREATE (:Person {name: 'Alice', age: 30, city: 'NYC'})
        """)

        # MERGE with same 3 properties should match
        results = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: 30, city: 'NYC'})
            RETURN p
        """)

        assert len(results) == 1

        # Should still have only 1 node
        count_result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 1

    def test_merge_three_properties_partial_mismatch(self):
        """Three properties where one differs - should create new node."""
        gf = GraphForge()

        # Create node with age=30
        gf.execute("""
            CREATE (:Person {name: 'Bob', age: 30, city: 'NYC'})
        """)

        # MERGE with age=31 should NOT match
        results = gf.execute("""
            MERGE (p:Person {name: 'Bob', age: 31, city: 'NYC'})
            RETURN p.age AS age
        """)

        assert len(results) == 1
        assert results[0]["age"].value == 31

        # Should have 2 nodes
        count_result = gf.execute("MATCH (p:Person {name: 'Bob'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_five_properties(self):
        """Five properties all must match."""
        gf = GraphForge()

        # Create node with 5 properties
        gf.execute("""
            CREATE (:Person {
                name: 'Charlie',
                age: 25,
                city: 'SF',
                country: 'USA',
                active: true
            })
        """)

        # MERGE with same 5 properties should match
        results = gf.execute("""
            MERGE (p:Person {
                name: 'Charlie',
                age: 25,
                city: 'SF',
                country: 'USA',
                active: true
            })
            RETURN p
        """)

        assert len(results) == 1

        # Should still have only 1 node
        count_result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 1

    def test_merge_property_type_mismatch_int_vs_string(self):
        """Integer 1 should NOT match string '1'."""
        gf = GraphForge()

        # Create node with integer age
        gf.execute("CREATE (:Person {name: 'Diana', age: 1})")

        # MERGE with string '1' should NOT match
        results = gf.execute("""
            MERGE (p:Person {name: 'Diana', age: '1'})
            RETURN p.age AS age
        """)

        assert len(results) == 1
        # New node has string age
        assert results[0]["age"].value == "1"

        # Should have 2 nodes
        count_result = gf.execute("MATCH (p:Person {name: 'Diana'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_property_type_mismatch_int_vs_float(self):
        """Integer 10 SHOULD match float 10.0 (numeric equivalence)."""
        gf = GraphForge()

        # Create node with integer age
        gf.execute("CREATE (:Person {name: 'Eve', age: 10})")

        # MERGE with float 10.0 should match (numeric types are equivalent)
        results = gf.execute("""
            MERGE (p:Person {name: 'Eve', age: 10.0})
            RETURN p.age AS age
        """)

        assert len(results) == 1
        # Should match existing node
        assert results[0]["age"].value == 10

        # Should still have only 1 node
        count_result = gf.execute("MATCH (p:Person {name: 'Eve'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 1

    def test_merge_property_subset_missing_key(self):
        """Pattern has property key that node doesn't have - should not match."""
        gf = GraphForge()

        # Create node with only name
        gf.execute("CREATE (:Person {name: 'Frank'})")

        # MERGE with name and age should NOT match (node doesn't have age)
        results = gf.execute("""
            MERGE (p:Person {name: 'Frank', age: 30})
            RETURN p.age AS age
        """)

        assert len(results) == 1
        # New node has age
        assert results[0]["age"].value == 30

        # Should have 2 nodes
        count_result = gf.execute("MATCH (p:Person {name: 'Frank'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_node_has_extra_properties(self):
        """Node has more properties than pattern - should still match on pattern properties."""
        gf = GraphForge()

        # Create node with 3 properties
        gf.execute("""
            CREATE (:Person {name: 'Grace', age: 30, city: 'LA'})
        """)

        # MERGE with only name and age should match (extra properties ignored)
        results = gf.execute("""
            MERGE (p:Person {name: 'Grace', age: 30})
            RETURN p.city AS city
        """)

        assert len(results) == 1
        # Should match existing node with city
        assert results[0]["city"].value == "LA"

        # Should still have only 1 node
        count_result = gf.execute("MATCH (p:Person {name: 'Grace'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 1


class TestEdgeCasesWithOnCreate:
    """Test edge cases combined with ON CREATE SET."""

    def test_merge_null_with_on_create_complex(self):
        """NULL behavior with ON CREATE SET and multiple properties."""
        gf = GraphForge()

        # Create node with NULL status
        gf.execute("""
            CREATE (:User {username: 'alice', status: NULL, role: 'admin'})
        """)

        # MERGE with NULL status should NOT match, should create new node
        results = gf.execute("""
            MERGE (u:User {username: 'alice', status: NULL, role: 'admin'})
            ON CREATE SET u.created_at = 'now'
            RETURN u.created_at AS created_at
        """)

        assert len(results) == 1
        # New node should have created_at set
        assert results[0]["created_at"].value == "now"

        # Should have 2 nodes
        count_result = gf.execute("MATCH (u:User {username: 'alice'}) RETURN count(u) AS count")
        assert count_result[0]["count"].value == 2


class TestMergeCorrectness:
    """Test that fixes don't break normal MERGE behavior."""

    def test_merge_idempotency_without_null(self):
        """Verify normal MERGE still works (no NULL properties)."""
        gf = GraphForge()

        # First MERGE creates node
        results1 = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: 30})
            RETURN p
        """)

        assert len(results1) == 1

        # Second MERGE should match existing node
        results2 = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: 30})
            RETURN p
        """)

        assert len(results2) == 1

        # Should still have only 1 node
        count_result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 1

    def test_merge_complex_scenario(self):
        """Combined scenario: NULL + multi-property + type matching."""
        gf = GraphForge()

        # Create various nodes
        gf.execute("CREATE (:Person {name: 'Alice', age: 30, city: 'NYC'})")
        gf.execute("CREATE (:Person {name: 'Bob', age: NULL, city: 'SF'})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 25})")

        # MERGE that should match Alice
        results1 = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: 30, city: 'NYC'})
            RETURN p.name AS name
        """)
        assert len(results1) == 1
        assert results1[0]["name"].value == "Alice"

        # MERGE with NULL should NOT match Bob, creates new node
        results2 = gf.execute("""
            MERGE (p:Person {name: 'Bob', age: NULL, city: 'SF'})
            RETURN p
        """)
        assert len(results2) == 1

        # MERGE with different city should NOT match Charlie, creates new node
        results3 = gf.execute("""
            MERGE (p:Person {name: 'Charlie', age: 25, city: 'LA'})
            RETURN p.city AS city
        """)
        assert len(results3) == 1
        assert results3[0]["city"].value == "LA"

        # Final count: Alice (1), Bob (2 - original + new), Charlie (2 - original + new) = 5
        count_result = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 5
