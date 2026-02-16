"""Integration tests for complex MERGE patterns.

Tests for edge cases in MERGE operations with various patterns.
"""

from graphforge import GraphForge


class TestComplexMergePatterns:
    """Tests for complex MERGE patterns."""

    def test_merge_with_multiple_properties(self):
        """MERGE matching multiple properties."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30})
        """)

        # MERGE should find the existing node
        results = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: 30})
            RETURN p.name AS name, p.age AS age
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30

        # Verify only one node exists
        all_results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert all_results[0]["count"].value == 1

    def test_merge_creates_when_properties_dont_match(self):
        """MERGE creates new node when properties don't match."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30})
        """)

        # MERGE with different properties should create new node
        results = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: 35})
            RETURN p.name AS name, p.age AS age
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 35

        # Verify two nodes exist now
        all_results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert all_results[0]["count"].value == 2

    def test_merge_with_no_properties(self):
        """MERGE with only label, no properties."""
        gf = GraphForge()
        gf.execute("CREATE (a:Item)")

        # MERGE should find the existing node
        results = gf.execute("""
            MERGE (i:Item)
            RETURN i
        """)

        # Should find the existing node
        assert len(results) == 1

        # Verify still only one node
        all_results = gf.execute("MATCH (i:Item) RETURN count(i) AS count")
        assert all_results[0]["count"].value == 1

    def test_merge_relationship_both_nodes_exist(self):
        """MERGE relationship when both nodes already exist."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'})
        """)

        # MERGE relationship between existing nodes
        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)-[r:KNOWS]->(b)
            RETURN r
        """)

        assert len(results) == 1

        # Verify relationship exists
        rel_results = gf.execute("""
            MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
            RETURN r
        """)
        assert len(rel_results) == 1

    def test_merge_relationship_creates_nodes(self):
        """MERGE relationship pattern creates missing nodes."""
        gf = GraphForge()

        # MERGE should create both nodes and relationship
        results = gf.execute("""
            MERGE (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})
            RETURN a.name AS a_name, b.name AS b_name
        """)

        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"

        # Verify nodes and relationship exist
        node_results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert node_results[0]["count"].value == 2

        rel_results = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(r) AS count")
        assert rel_results[0]["count"].value == 1

    def test_merge_with_set_clause(self):
        """MERGE followed by SET to update properties."""
        gf = GraphForge()

        # First MERGE creates node
        gf.execute("""
            MERGE (p:Person {name: 'Alice'})
            SET p.visits = 1
        """)

        # Second MERGE finds it and updates
        gf.execute("""
            MERGE (p:Person {name: 'Alice'})
            SET p.visits = 2
        """)

        results = gf.execute("""
            MATCH (p:Person {name: 'Alice'})
            RETURN p.visits AS visits
        """)

        assert len(results) == 1
        assert results[0]["visits"].value == 2

    def test_merge_multiple_patterns_in_one_clause(self):
        """MERGE multiple patterns in a single clause."""
        gf = GraphForge()

        # MERGE multiple nodes at once
        results = gf.execute("""
            MERGE (a:Person {name: 'Alice'}),
                  (b:Person {name: 'Bob'}),
                  (c:Person {name: 'Charlie'})
            RETURN a.name AS a_name, b.name AS b_name, c.name AS c_name
        """)

        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"
        assert results[0]["c_name"].value == "Charlie"

        # Verify all three exist
        node_results = gf.execute("MATCH (p:Person) RETURN count(p) AS count")
        assert node_results[0]["count"].value == 3

    def test_merge_after_match(self):
        """MERGE after MATCH to conditionally create."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', city: 'NYC'})
        """)

        # Find Alice and merge a friend
        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'})
            MERGE (a)-[r:KNOWS]->(b:Person {name: 'Bob'})
            RETURN a.name AS a_name, b.name AS b_name
        """)

        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"

    def test_merge_with_where_clause(self):
        """MERGE combined with WHERE filtering."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30}),
                   (b:Person {name: 'Bob', age: 25})
        """)

        # MATCH with WHERE, then MERGE
        results = gf.execute("""
            MATCH (p:Person)
            WHERE p.age > 28
            MERGE (p)-[r:WORKS_AT]->(c:Company {name: 'Acme'})
            RETURN p.name AS person, c.name AS company
        """)

        # Only Alice (age 30) should get the relationship
        assert len(results) == 1
        assert results[0]["person"].value == "Alice"
        assert results[0]["company"].value == "Acme"

    def test_merge_with_null_property(self):
        """MERGE with NULL property value should always create (NULL never matches NULL)."""
        gf = GraphForge()

        # First MERGE with NULL property creates node
        results = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: NULL})
            RETURN p.name AS name
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

        # Second MERGE with NULL should CREATE new node (NULL doesn't match NULL per openCypher)
        results2 = gf.execute("""
            MERGE (p:Person {name: 'Alice', age: NULL})
            RETURN p
        """)

        assert len(results2) == 1

        # Total count should be 2 (NULL never matches NULL per openCypher)
        count_result = gf.execute("MATCH (p:Person {name: 'Alice'}) RETURN count(p) AS count")
        assert count_result[0]["count"].value == 2

    def test_merge_relationship_incoming_direction(self):
        """MERGE with incoming relationship direction (a)<-[r]-(b)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'})
        """)

        # MERGE incoming relationship: (a)<-[r:KNOWS]-(b)
        # This should create relationship from Bob to Alice
        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)<-[r:KNOWS]-(b)
            RETURN r
        """)

        assert len(results) == 1

        # Verify relationship direction: Bob->Alice
        rel_results = gf.execute("""
            MATCH (b:Person {name: 'Bob'})-[r:KNOWS]->(a:Person {name: 'Alice'})
            RETURN r
        """)
        assert len(rel_results) == 1

        # Second MERGE should find existing relationship
        results2 = gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)<-[r:KNOWS]-(b)
            RETURN r
        """)
        assert len(results2) == 1

        # Verify only one relationship exists
        count_result = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(r) AS count")
        assert count_result[0]["count"].value == 1

    def test_merge_relationship_undirected(self):
        """MERGE with undirected relationship pattern (a)-[r]-(b)."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'})
        """)

        # Create directed relationship first
        gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            CREATE (a)-[:KNOWS]->(b)
        """)

        # MERGE undirected should find the existing relationship
        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)-[r:KNOWS]-(b)
            RETURN r
        """)
        assert len(results) == 1

        # Verify still only one relationship exists
        count_result = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(r) AS count")
        assert count_result[0]["count"].value == 1

    def test_merge_relationship_incoming_with_properties(self):
        """MERGE incoming relationship with property matching."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice'}),
                   (b:Person {name: 'Bob'})
        """)

        # First MERGE creates relationship with property
        gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)<-[r:KNOWS {since: 2020}]-(b)
        """)

        # Second MERGE with same property should find it
        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)<-[r:KNOWS {since: 2020}]-(b)
            RETURN r.since AS since
        """)
        assert len(results) == 1
        assert results[0]["since"].value == 2020

        # MERGE with different property should create new relationship
        gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            MERGE (a)<-[r:KNOWS {since: 2021}]-(b)
        """)

        # Now there should be 2 relationships
        count_result = gf.execute("MATCH ()-[r:KNOWS]->() RETURN count(r) AS count")
        assert count_result[0]["count"].value == 2
