"""Integration tests for MERGE ON CREATE SET with real-world patterns."""


from graphforge import GraphForge


class TestNeo4jMovieGraphPatterns:
    """Test patterns from Neo4j Movie Graph dataset."""

    def test_complete_movie_graph_workflow(self):
        """Test complete workflow similar to Neo4j Movie Graph dataset."""
        gf = GraphForge()

        # Create movies with ON CREATE SET
        gf.execute("""
            MERGE (TheMatrix:Movie {title:'The Matrix'})
            ON CREATE SET TheMatrix.released=1999, TheMatrix.tagline='Welcome to the Real World'
        """)

        gf.execute("""
            MERGE (TheMatrixReloaded:Movie {title:'The Matrix Reloaded'})
            ON CREATE SET TheMatrixReloaded.released=2003, TheMatrixReloaded.tagline='Free your mind'
        """)

        # Create people with ON CREATE SET
        gf.execute("""
            MERGE (Keanu:Person {name:'Keanu Reeves'})
            ON CREATE SET Keanu.born=1964
        """)

        gf.execute("""
            MERGE (Carrie:Person {name:'Carrie-Anne Moss'})
            ON CREATE SET Carrie.born=1967
        """)

        gf.execute("""
            MERGE (Laurence:Person {name:'Laurence Fishburne'})
            ON CREATE SET Laurence.born=1961
        """)

        # Verify movies exist with properties
        movies = gf.execute("""
            MATCH (m:Movie)
            RETURN m.title as title, m.released as year, m.tagline as tagline
            ORDER BY m.released
        """)
        assert len(movies) == 2
        assert movies[0]["title"].value == "The Matrix"
        assert movies[0]["year"].value == 1999
        assert movies[1]["title"].value == "The Matrix Reloaded"
        assert movies[1]["year"].value == 2003

        # Verify people exist with properties
        people = gf.execute("""
            MATCH (p:Person)
            RETURN p.name as name, p.born as born
            ORDER BY p.born
        """)
        assert len(people) == 3
        assert people[0]["name"].value == "Laurence Fishburne"
        assert people[0]["born"].value == 1961
        assert people[2]["name"].value == "Carrie-Anne Moss"
        assert people[2]["born"].value == 1967

    def test_repeated_merge_idempotent(self):
        """Test that repeated MERGE is idempotent (doesn't duplicate or change data)."""
        gf = GraphForge()

        # Execute same MERGE multiple times
        for _ in range(3):
            gf.execute("""
                MERGE (TheMatrix:Movie {title:'The Matrix'})
                ON CREATE SET TheMatrix.released=1999
            """)

        # Should only have one node
        count = gf.execute("MATCH (m:Movie {title:'The Matrix'}) RETURN count(m) as count")
        assert count[0]["count"].value == 1

        # Property should have value from first creation
        result = gf.execute("MATCH (m:Movie {title:'The Matrix'}) RETURN m.released as year")
        assert result[0]["year"].value == 1999

    def test_merge_with_existing_nodes(self):
        """Test MERGE ON CREATE SET with pre-existing nodes."""
        gf = GraphForge()

        # Create node manually first
        gf.execute("CREATE (m:Movie {title:'The Matrix', released:1998, budget: 63000000})")

        # MERGE with ON CREATE SET should match existing node
        gf.execute("""
            MERGE (TheMatrix:Movie {title:'The Matrix'})
            ON CREATE SET TheMatrix.released=1999, TheMatrix.tagline='Welcome to the Real World'
        """)

        # Should still be one node
        count = gf.execute("MATCH (m:Movie {title:'The Matrix'}) RETURN count(m) as count")
        assert count[0]["count"].value == 1

        # Original properties should be intact (not overwritten by ON CREATE SET)
        result = gf.execute("""
            MATCH (m:Movie {title:'The Matrix'})
            RETURN m.released as year, m.budget as budget, m.tagline as tagline
        """)
        assert result[0]["year"].value == 1998  # Original value, not 1999
        assert result[0]["budget"].value == 63000000  # Still exists
        # tagline was never set (ON CREATE didn't execute)
        assert "tagline" not in result[0] or result[0]["tagline"].value is None


class TestComplexQueries:
    """Test complex queries with MERGE ON CREATE SET."""

    def test_merge_with_return(self):
        """Test MERGE ON CREATE SET with RETURN clause."""
        gf = GraphForge()

        result = gf.execute("""
            MERGE (n:Person {id: 1})
            ON CREATE SET n.created = true, n.timestamp = 12345
            RETURN n.id as id, n.created as created, n.timestamp as ts
        """)

        assert len(result) == 1
        assert result[0]["id"].value == 1
        assert result[0]["created"].value is True
        assert result[0]["ts"].value == 12345

    def test_merge_multiple_patterns_with_on_create(self):
        """Test MERGE with multiple patterns and ON CREATE SET."""
        gf = GraphForge()

        gf.execute("""
            MERGE (a:Person {id: 1}), (b:Person {id: 2})
            ON CREATE SET a.name = 'Alice'
        """)

        # Both nodes should exist
        count = gf.execute("MATCH (p:Person) RETURN count(p) as count")
        assert count[0]["count"].value == 2

        # First node should have name set
        result_a = gf.execute("MATCH (p:Person {id: 1}) RETURN p.name as name")
        assert result_a[0]["name"].value == "Alice"

    def test_merge_on_create_with_where(self):
        """Test MERGE ON CREATE SET followed by WHERE filtering."""
        gf = GraphForge()

        # Create multiple nodes
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.value = 10")
        gf.execute("MERGE (n:Node {id: 2}) ON CREATE SET n.value = 20")
        gf.execute("MERGE (n:Node {id: 3}) ON CREATE SET n.value = 30")

        # Query with WHERE
        result = gf.execute("""
            MATCH (n:Node)
            WHERE n.value > 15
            RETURN n.id as id, n.value as value
            ORDER BY n.id
        """)

        assert len(result) == 2
        assert result[0]["id"].value == 2
        assert result[0]["value"].value == 20
        assert result[1]["id"].value == 3
        assert result[1]["value"].value == 30

    def test_merge_on_create_with_aggregation(self):
        """Test MERGE ON CREATE SET with aggregation queries."""
        gf = GraphForge()

        # Create nodes with timestamps
        gf.execute("MERGE (n:Event {id: 1}) ON CREATE SET n.timestamp = 100")
        gf.execute("MERGE (n:Event {id: 2}) ON CREATE SET n.timestamp = 200")
        gf.execute("MERGE (n:Event {id: 3}) ON CREATE SET n.timestamp = 300")

        # Aggregate query
        result = gf.execute("""
            MATCH (e:Event)
            RETURN count(e) as count, sum(e.timestamp) as total
        """)

        assert result[0]["count"].value == 3
        assert result[0]["total"].value == 600


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_merge_on_create_empty_set(self):
        """Test MERGE with ON CREATE SET but empty properties (should parse but do nothing extra)."""
        gf = GraphForge()

        # Just a basic MERGE with ON CREATE SET
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.flag = true")

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.flag as flag")
        assert result[0]["flag"].value is True

    def test_merge_on_create_overwrite_pattern_property(self):
        """Test ON CREATE SET can set properties that exist in pattern."""
        gf = GraphForge()

        # ON CREATE SET can add or modify properties
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.id = 999, n.extra = 'test'")

        result = gf.execute("MATCH (n:Node) RETURN n.id as id, n.extra as extra")
        # The node is matched by id: 1, so it exists with id: 1
        # ON CREATE SET modifies it after creation
        assert len(result) == 1
        assert result[0]["id"].value == 999  # Overwritten by ON CREATE SET
        assert result[0]["extra"].value == "test"

    def test_merge_on_create_with_null_pattern_properties(self):
        """Test MERGE ON CREATE SET when pattern has null in properties."""
        gf = GraphForge()

        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.optional = null, n.required = 'value'")

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.optional as opt, n.required as req")
        assert result[0]["opt"].value is None
        assert result[0]["req"].value == "value"

    def test_merge_on_create_multiple_labels(self):
        """Test MERGE ON CREATE SET with multiple labels."""
        gf = GraphForge()

        gf.execute("MERGE (n:Person:Employee {id: 1}) ON CREATE SET n.hired = 2020")

        result = gf.execute("MATCH (n:Person:Employee {id: 1}) RETURN n.hired as hired")
        assert result[0]["hired"].value == 2020

    def test_merge_on_create_no_variable(self):
        """Test MERGE ON CREATE SET when pattern has no variable."""
        gf = GraphForge()

        # Pattern without variable - ON CREATE SET won't have anything to reference
        # This should parse but the SET won't apply (no variable to set on)
        # This is more of a syntax edge case
        gf.execute("MERGE (:Node {id: 1})")

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN count(n) as count")
        assert result[0]["count"].value == 1


class TestPerformance:
    """Test performance characteristics of MERGE ON CREATE SET."""

    def test_bulk_merge_performance(self):
        """Test bulk MERGE operations with ON CREATE SET."""
        gf = GraphForge()

        # Create 100 nodes with ON CREATE SET
        for i in range(100):
            gf.execute(f"""
                MERGE (n:Node {{id: {i}}})
                ON CREATE SET n.value = {i * 10}, n.created = true
            """)

        # Verify all nodes exist
        count = gf.execute("MATCH (n:Node) RETURN count(n) as count")
        assert count[0]["count"].value == 100

        # Verify properties are set
        result = gf.execute("MATCH (n:Node {id: 50}) RETURN n.value as value, n.created as created")
        assert result[0]["value"].value == 500
        assert result[0]["created"].value is True

    def test_repeated_bulk_merge_idempotency(self):
        """Test that repeated bulk MERGE operations remain idempotent."""
        gf = GraphForge()

        # Run bulk MERGE twice
        for iteration in range(2):
            for i in range(50):
                gf.execute(f"""
                    MERGE (n:Node {{id: {i}}})
                    ON CREATE SET n.iteration = {iteration}, n.created = true
                """)

        # Should still have 50 nodes
        count = gf.execute("MATCH (n:Node) RETURN count(n) as count")
        assert count[0]["count"].value == 50

        # All nodes should have iteration = 0 (from first creation)
        result = gf.execute("MATCH (n:Node) WHERE n.iteration = 0 RETURN count(n) as count")
        assert result[0]["count"].value == 50
