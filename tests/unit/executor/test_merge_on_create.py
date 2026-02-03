"""Unit tests for executing MERGE ON CREATE SET."""


from graphforge import GraphForge


class TestMergeOnCreateExecution:
    """Test execution of MERGE with ON CREATE SET."""

    def test_on_create_executes_when_creating(self):
        """ON CREATE SET should execute when creating new node."""
        gf = GraphForge()
        gf.execute("MERGE (n:Test {id: 1}) ON CREATE SET n.created = true")

        result = gf.execute("MATCH (n:Test {id: 1}) RETURN n.created as val")
        assert len(result) == 1
        assert result[0]["val"].value is True

    def test_on_create_not_executed_when_matching(self):
        """ON CREATE SET should NOT execute when matching existing node."""
        gf = GraphForge()

        # First MERGE creates the node and sets created = true
        gf.execute("MERGE (n:Test {id: 1}) ON CREATE SET n.created = true")

        # Second MERGE matches the existing node, should NOT set created = false
        gf.execute("MERGE (n:Test {id: 1}) ON CREATE SET n.created = false")

        result = gf.execute("MATCH (n:Test {id: 1}) RETURN n.created as val")
        assert len(result) == 1
        assert result[0]["val"].value is True  # Should still be true from first create

    def test_on_create_multiple_properties(self):
        """ON CREATE SET with multiple properties."""
        gf = GraphForge()
        gf.execute("""
            MERGE (n:Person {id: 1})
            ON CREATE SET n.created = true, n.timestamp = 123
        """)

        result = gf.execute("""
            MATCH (n:Person {id: 1})
            RETURN n.created as created, n.timestamp as ts
        """)
        assert len(result) == 1
        assert result[0]["created"].value is True
        assert result[0]["ts"].value == 123

    def test_on_create_with_expressions(self):
        """ON CREATE SET with expression evaluation."""
        gf = GraphForge()
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.doubled = 2 * 5")

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.doubled as val")
        assert len(result) == 1
        assert result[0]["val"].value == 10

    def test_on_create_with_string_concatenation(self):
        """ON CREATE SET with string values."""
        gf = GraphForge()
        gf.execute("""
            MERGE (m:Movie {title: 'The Matrix'})
            ON CREATE SET m.tagline = 'Welcome to the Real World'
        """)

        result = gf.execute("MATCH (m:Movie {title: 'The Matrix'}) RETURN m.tagline as tag")
        assert len(result) == 1
        assert result[0]["tag"].value == "Welcome to the Real World"

    def test_on_create_preserves_existing_properties(self):
        """ON CREATE SET should not affect existing properties on matched nodes."""
        gf = GraphForge()

        # Create node with some properties
        gf.execute("CREATE (n:Person {id: 1, name: 'Alice', age: 30})")

        # MERGE with ON CREATE SET should match existing node and NOT execute SET
        gf.execute("MERGE (n:Person {id: 1}) ON CREATE SET n.age = 99")

        result = gf.execute("MATCH (n:Person {id: 1}) RETURN n.age as age")
        assert len(result) == 1
        assert result[0]["age"].value == 30  # Should still be 30, not 99

    def test_on_create_with_null_value(self):
        """ON CREATE SET can set null values."""
        gf = GraphForge()
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.optional = null")

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.optional as val")
        assert len(result) == 1
        assert result[0]["val"].value is None

    def test_on_create_multiple_merges(self):
        """Multiple MERGE statements with ON CREATE SET."""
        gf = GraphForge()

        # First merge creates node with prop1
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.prop1 = 'first'")

        # Second merge creates different node with prop2
        gf.execute("MERGE (n:Node {id: 2}) ON CREATE SET n.prop2 = 'second'")

        # Third merge matches first node, should NOT set prop3
        gf.execute("MERGE (n:Node {id: 1}) ON CREATE SET n.prop3 = 'third'")

        result1 = gf.execute("MATCH (n:Node {id: 1}) RETURN n.prop1 as p1, n.prop3 as p3")
        assert result1[0]["p1"].value == "first"
        # prop3 should not exist since node was matched, not created
        assert "p3" not in result1[0] or result1[0]["p3"].value is None

        result2 = gf.execute("MATCH (n:Node {id: 2}) RETURN n.prop2 as p2")
        assert result2[0]["p2"].value == "second"


class TestBackwardCompatibility:
    """Test that MERGE without ON CREATE still works."""

    def test_merge_without_on_create_still_works(self):
        """Ensure MERGE without ON CREATE still works."""
        gf = GraphForge()

        # Simple MERGE without ON CREATE
        gf.execute("MERGE (n:Person {name: 'Alice'})")

        result = gf.execute("MATCH (n:Person {name: 'Alice'}) RETURN count(n) as count")
        assert result[0]["count"].value == 1

    def test_merge_with_manual_set_after(self):
        """MERGE followed by SET (not ON CREATE SET)."""
        gf = GraphForge()

        # MERGE then SET (separate statements)
        gf.execute("MERGE (n:Person {id: 1})")
        gf.execute("MATCH (n:Person {id: 1}) SET n.updated = true")

        result = gf.execute("MATCH (n:Person {id: 1}) RETURN n.updated as val")
        assert result[0]["val"].value is True

    def test_merge_existing_behavior_unchanged(self):
        """Verify existing MERGE behavior is not affected."""
        gf = GraphForge()

        # Create a node
        gf.execute("CREATE (n:Test {id: 1, value: 'original'})")

        # MERGE should match it
        gf.execute("MERGE (n:Test {id: 1})")

        # Should still be one node
        result = gf.execute("MATCH (n:Test {id: 1}) RETURN count(n) as count")
        assert result[0]["count"].value == 1

        # Original properties should be intact
        result = gf.execute("MATCH (n:Test {id: 1}) RETURN n.value as val")
        assert result[0]["val"].value == "original"


class TestNeo4jPatterns:
    """Test real Neo4j patterns from example datasets."""

    def test_movie_graph_pattern(self):
        """Test Neo4j Movie Graph pattern."""
        gf = GraphForge()

        # Real pattern from Neo4j Movie dataset
        gf.execute("""
            MERGE (TheMatrix:Movie {title:'The Matrix'})
            ON CREATE SET TheMatrix.released=1999,
                          TheMatrix.tagline='Welcome to the Real World'
        """)

        # Verify the node exists with correct properties
        result = gf.execute("""
            MATCH (m:Movie {title:'The Matrix'})
            RETURN m.released as year, m.tagline as tagline
        """)

        assert len(result) == 1
        assert result[0]["year"].value == 1999
        assert result[0]["tagline"].value == "Welcome to the Real World"

    def test_repeated_merge_tracks_state(self):
        """Test that repeated MERGE only sets on first create."""
        gf = GraphForge()

        # First MERGE creates and sets properties
        gf.execute("""
            MERGE (TheMatrix:Movie {title:'The Matrix'})
            ON CREATE SET TheMatrix.released=1999, TheMatrix.tagline='Welcome to the Real World'
        """)

        # Second MERGE matches existing, should NOT change properties
        gf.execute("""
            MERGE (TheMatrix:Movie {title:'The Matrix'})
            ON CREATE SET TheMatrix.released=2020, TheMatrix.tagline='Different tagline'
        """)

        # Properties should still have original values
        result = gf.execute("""
            MATCH (m:Movie {title:'The Matrix'})
            RETURN m.released as year, m.tagline as tagline
        """)

        assert len(result) == 1
        assert result[0]["year"].value == 1999  # Original value
        assert result[0]["tagline"].value == "Welcome to the Real World"  # Original value

    def test_multiple_movie_merges(self):
        """Test multiple MERGE statements like in Neo4j datasets."""
        gf = GraphForge()

        # Multiple MERGE statements from dataset
        gf.execute(
            "MERGE (TheMatrix:Movie {title:'The Matrix'}) ON CREATE SET TheMatrix.released=1999"
        )
        gf.execute("MERGE (Keanu:Person {name:'Keanu Reeves'}) ON CREATE SET Keanu.born=1964")
        gf.execute(
            "MERGE (TheMatrixReloaded:Movie {title:'The Matrix Reloaded'}) ON CREATE SET TheMatrixReloaded.released=2003"
        )

        # Verify all nodes exist
        movie_count = gf.execute("MATCH (m:Movie) RETURN count(m) as count")
        assert movie_count[0]["count"].value == 2

        person_count = gf.execute("MATCH (p:Person) RETURN count(p) as count")
        assert person_count[0]["count"].value == 1

        # Verify properties
        keanu = gf.execute("MATCH (p:Person {name:'Keanu Reeves'}) RETURN p.born as born")
        assert keanu[0]["born"].value == 1964
