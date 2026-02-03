"""Unit tests for executing MERGE ON MATCH SET."""

from graphforge import GraphForge


class TestMergeOnMatchExecution:
    """Test execution of MERGE with ON MATCH SET."""

    def test_on_match_executes_when_matching(self):
        """ON MATCH SET should execute when matching existing node."""
        gf = GraphForge()

        # Create node first
        gf.execute("CREATE (n:Test {id: 1, value: 'original'})")

        # MERGE with ON MATCH SET should match existing and update
        gf.execute("MERGE (n:Test {id: 1}) ON MATCH SET n.updated = true")

        result = gf.execute("MATCH (n:Test {id: 1}) RETURN n.updated as val")
        assert len(result) == 1
        assert result[0]["val"].value is True

    def test_on_match_not_executed_when_creating(self):
        """ON MATCH SET should NOT execute when creating new node."""
        gf = GraphForge()

        # MERGE creates node, should NOT execute ON MATCH SET
        gf.execute("MERGE (n:Test {id: 1}) ON MATCH SET n.updated = true")

        result = gf.execute("MATCH (n:Test {id: 1}) RETURN n.updated as val")
        assert len(result) == 1
        # Property should not be set because node was created, not matched
        assert "val" not in result[0] or result[0]["val"].value is None

    def test_on_match_multiple_properties(self):
        """ON MATCH SET with multiple properties."""
        gf = GraphForge()

        # Create node
        gf.execute("CREATE (n:Person {id: 1, name: 'Alice'})")

        # MERGE with ON MATCH SET multiple properties
        gf.execute("""
            MERGE (n:Person {id: 1})
            ON MATCH SET n.updated = true, n.counter = 42
        """)

        result = gf.execute("""
            MATCH (n:Person {id: 1})
            RETURN n.updated as updated, n.counter as counter
        """)
        assert result[0]["updated"].value is True
        assert result[0]["counter"].value == 42

    def test_on_match_updates_existing_property(self):
        """ON MATCH SET can update existing properties."""
        gf = GraphForge()

        # Create node with initial counter
        gf.execute("CREATE (n:Node {id: 1, counter: 1})")

        # MERGE with ON MATCH SET to increment
        gf.execute("MERGE (n:Node {id: 1}) ON MATCH SET n.counter = 2")

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.counter as count")
        assert result[0]["count"].value == 2

    def test_on_match_with_string(self):
        """ON MATCH SET with string values."""
        gf = GraphForge()

        # Create node
        gf.execute("CREATE (m:Movie {title: 'The Matrix'})")

        # Update with ON MATCH SET
        gf.execute("""
            MERGE (m:Movie {title: 'The Matrix'})
            ON MATCH SET m.status = 'watched'
        """)

        result = gf.execute("MATCH (m:Movie {title: 'The Matrix'}) RETURN m.status as status")
        assert result[0]["status"].value == "watched"


class TestMergeOnCreateAndOnMatch:
    """Test MERGE with both ON CREATE SET and ON MATCH SET."""

    def test_on_create_executes_when_creating(self):
        """When creating, ON CREATE SET should execute, not ON MATCH SET."""
        gf = GraphForge()

        # MERGE creates node
        gf.execute("""
            MERGE (n:Person {id: 1})
            ON CREATE SET n.created = true
            ON MATCH SET n.updated = true
        """)

        result = gf.execute("""
            MATCH (n:Person {id: 1})
            RETURN n.created as created, n.updated as updated
        """)
        assert result[0]["created"].value is True
        # updated should not be set (node was created, not matched)
        assert "updated" not in result[0] or result[0]["updated"].value is None

    def test_on_match_executes_when_matching(self):
        """When matching, ON MATCH SET should execute, not ON CREATE SET."""
        gf = GraphForge()

        # Create node first
        gf.execute("CREATE (n:Person {id: 1})")

        # MERGE matches existing node
        gf.execute("""
            MERGE (n:Person {id: 1})
            ON CREATE SET n.created = true
            ON MATCH SET n.updated = true
        """)

        result = gf.execute("""
            MATCH (n:Person {id: 1})
            RETURN n.created as created, n.updated as updated
        """)
        # created should not be set (node was matched, not created)
        assert "created" not in result[0] or result[0]["created"].value is None
        assert result[0]["updated"].value is True

    def test_repeated_merge_tracks_state(self):
        """Test that repeated MERGE correctly tracks create vs match."""
        gf = GraphForge()

        # First MERGE creates
        gf.execute("""
            MERGE (n:Test {id: 1})
            ON CREATE SET n.created = 'first'
            ON MATCH SET n.matched = 'never'
        """)

        result1 = gf.execute("MATCH (n:Test {id: 1}) RETURN n.created as c, n.matched as m")
        assert result1[0]["c"].value == "first"
        assert "m" not in result1[0] or result1[0]["m"].value is None

        # Second MERGE matches
        gf.execute("""
            MERGE (n:Test {id: 1})
            ON CREATE SET n.created = 'second'
            ON MATCH SET n.matched = 'yes'
        """)

        result2 = gf.execute("MATCH (n:Test {id: 1}) RETURN n.created as c, n.matched as m")
        assert result2[0]["c"].value == "first"  # Should still be 'first'
        assert result2[0]["m"].value == "yes"  # Now set by ON MATCH

    def test_on_create_and_match_with_multiple_properties(self):
        """Both ON CREATE and ON MATCH with multiple properties."""
        gf = GraphForge()

        # Create with ON CREATE
        gf.execute("""
            MERGE (n:Node {id: 1})
            ON CREATE SET n.created = true, n.createdAt = 100
            ON MATCH SET n.updated = true, n.updatedAt = 200
        """)

        result1 = gf.execute("""
            MATCH (n:Node {id: 1})
            RETURN n.created as c, n.createdAt as cat, n.updated as u, n.updatedAt as uat
        """)
        assert result1[0]["c"].value is True
        assert result1[0]["cat"].value == 100
        assert "u" not in result1[0] or result1[0]["u"].value is None
        assert "uat" not in result1[0] or result1[0]["uat"].value is None

        # Match with ON MATCH
        gf.execute("""
            MERGE (n:Node {id: 1})
            ON CREATE SET n.created = false, n.createdAt = 999
            ON MATCH SET n.updated = true, n.updatedAt = 200
        """)

        result2 = gf.execute("""
            MATCH (n:Node {id: 1})
            RETURN n.created as c, n.createdAt as cat, n.updated as u, n.updatedAt as uat
        """)
        # Original values from creation
        assert result2[0]["c"].value is True
        assert result2[0]["cat"].value == 100
        # New values from match
        assert result2[0]["u"].value is True
        assert result2[0]["uat"].value == 200


class TestBackwardCompatibility:
    """Test that existing MERGE behavior is preserved."""

    def test_merge_with_only_on_create_still_works(self):
        """MERGE with only ON CREATE SET still works."""
        gf = GraphForge()

        gf.execute("MERGE (n:Test {id: 1}) ON CREATE SET n.val = 1")
        result = gf.execute("MATCH (n:Test {id: 1}) RETURN n.val as val")
        assert result[0]["val"].value == 1

    def test_merge_without_on_clauses_still_works(self):
        """MERGE without ON CREATE or ON MATCH still works."""
        gf = GraphForge()

        gf.execute("MERGE (n:Test {id: 1})")
        result = gf.execute("MATCH (n:Test {id: 1}) RETURN count(n) as count")
        assert result[0]["count"].value == 1
