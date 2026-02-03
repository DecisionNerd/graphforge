"""Integration tests for MERGE ON MATCH SET with real-world patterns."""

from graphforge import GraphForge


class TestNeo4jTimestampPatterns:
    """Test timestamp tracking patterns common in Neo4j."""

    def test_timestamp_pattern(self):
        """Test Neo4j pattern: track creation and last seen timestamps."""
        gf = GraphForge()

        # First visit - create with timestamp
        gf.execute("""
            MERGE (n:User {id: 'user123'})
            ON CREATE SET n.created = 100
            ON MATCH SET n.lastSeen = 200
        """)

        result = gf.execute("""
            MATCH (n:User {id: 'user123'})
            RETURN n.created as created, n.lastSeen as lastSeen
        """)
        assert result[0]["created"].value == 100
        assert "lastSeen" not in result[0] or result[0]["lastSeen"].value is None

        # Second visit - update last seen
        gf.execute("""
            MERGE (n:User {id: 'user123'})
            ON CREATE SET n.created = 999
            ON MATCH SET n.lastSeen = 200
        """)

        result = gf.execute("""
            MATCH (n:User {id: 'user123'})
            RETURN n.created as created, n.lastSeen as lastSeen
        """)
        assert result[0]["created"].value == 100  # Original timestamp
        assert result[0]["lastSeen"].value == 200  # Updated timestamp

    def test_counter_increment_pattern(self):
        """Test Neo4j pattern: increment counter on match."""
        gf = GraphForge()

        # Create with initial view count
        gf.execute("""
            MERGE (p:Page {url: '/home'})
            ON CREATE SET p.views = 1
            ON MATCH SET p.views = 2
        """)

        result = gf.execute("MATCH (p:Page {url: '/home'}) RETURN p.views as views")
        assert result[0]["views"].value == 1

        # Subsequent visits increment
        gf.execute("""
            MERGE (p:Page {url: '/home'})
            ON CREATE SET p.views = 1
            ON MATCH SET p.views = 3
        """)

        result = gf.execute("MATCH (p:Page {url: '/home'}) RETURN p.views as views")
        assert result[0]["views"].value == 3


class TestStatusTracking:
    """Test status tracking patterns."""

    def test_status_workflow(self):
        """Test workflow: create as 'pending', update to 'active' on match."""
        gf = GraphForge()

        # Create task
        gf.execute("""
            MERGE (t:Task {id: 'task1'})
            ON CREATE SET t.status = 'pending', t.createdAt = 100
            ON MATCH SET t.status = 'active', t.updatedAt = 200
        """)

        result = gf.execute("""
            MATCH (t:Task {id: 'task1'})
            RETURN t.status as status, t.createdAt as created, t.updatedAt as updated
        """)
        assert result[0]["status"].value == "pending"
        assert result[0]["created"].value == 100
        assert "updated" not in result[0] or result[0]["updated"].value is None

        # Update task
        gf.execute("""
            MERGE (t:Task {id: 'task1'})
            ON CREATE SET t.status = 'pending', t.createdAt = 999
            ON MATCH SET t.status = 'active', t.updatedAt = 200
        """)

        result = gf.execute("""
            MATCH (t:Task {id: 'task1'})
            RETURN t.status as status, t.createdAt as created, t.updatedAt as updated
        """)
        assert result[0]["status"].value == "active"
        assert result[0]["created"].value == 100
        assert result[0]["updated"].value == 200


class TestComplexQueries:
    """Test complex queries with ON MATCH SET."""

    def test_merge_with_return(self):
        """Test MERGE ON MATCH SET with RETURN clause."""
        gf = GraphForge()

        # Create
        result1 = gf.execute("""
            MERGE (n:Person {id: 1})
            ON CREATE SET n.created = true
            ON MATCH SET n.updated = true
            RETURN n.created as c, n.updated as u
        """)
        assert result1[0]["c"].value is True
        assert "u" not in result1[0] or result1[0]["u"].value is None

        # Match
        result2 = gf.execute("""
            MERGE (n:Person {id: 1})
            ON CREATE SET n.created = false
            ON MATCH SET n.updated = true
            RETURN n.created as c, n.updated as u
        """)
        assert result2[0]["c"].value is True  # Original value
        assert result2[0]["u"].value is True  # Now set

    def test_merge_multiple_nodes_with_on_match(self):
        """Test MERGE with multiple nodes and ON MATCH."""
        gf = GraphForge()

        # Create two nodes
        gf.execute("CREATE (a:Node {id: 1}), (b:Node {id: 2})")

        # MERGE both with ON MATCH
        gf.execute("""
            MERGE (a:Node {id: 1}), (b:Node {id: 2})
            ON MATCH SET a.matched = true
        """)

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.matched as matched")
        assert result[0]["matched"].value is True

    def test_merge_on_match_with_where(self):
        """Test MERGE ON MATCH followed by WHERE filtering."""
        gf = GraphForge()

        # Create nodes with different status
        gf.execute("""
            MERGE (n:Node {id: 1})
            ON CREATE SET n.status = 'active'
        """)
        gf.execute("""
            MERGE (n:Node {id: 2})
            ON CREATE SET n.status = 'inactive'
        """)

        # Update with ON MATCH
        gf.execute("""
            MERGE (n:Node {id: 1})
            ON MATCH SET n.lastChecked = 100
        """)

        # Query with WHERE
        result = gf.execute("""
            MATCH (n:Node)
            WHERE n.lastChecked = 100
            RETURN n.id as id, n.status as status
        """)
        assert len(result) == 1
        assert result[0]["id"].value == 1
        assert result[0]["status"].value == "active"


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_merge_on_match_with_null_value(self):
        """Test ON MATCH SET can set null values."""
        gf = GraphForge()

        # Create with value
        gf.execute("CREATE (n:Node {id: 1, optional: 'value'})")

        # Clear value with ON MATCH SET
        gf.execute("""
            MERGE (n:Node {id: 1})
            ON MATCH SET n.optional = null
        """)

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.optional as val")
        assert result[0]["val"].value is None

    def test_merge_on_match_overwrite_property(self):
        """Test ON MATCH SET can overwrite existing properties."""
        gf = GraphForge()

        # Create with initial value
        gf.execute("CREATE (n:Node {id: 1, value: 'old'})")

        # Overwrite with ON MATCH SET
        gf.execute("""
            MERGE (n:Node {id: 1})
            ON MATCH SET n.value = 'new'
        """)

        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.value as val")
        assert result[0]["val"].value == "new"

    def test_merge_idempotency_with_on_match(self):
        """Test that repeated MERGE with ON MATCH is idempotent for same values."""
        gf = GraphForge()

        # Create node
        gf.execute("CREATE (n:Node {id: 1})")

        # Set value multiple times
        for _ in range(3):
            gf.execute("""
                MERGE (n:Node {id: 1})
                ON MATCH SET n.flag = true
            """)

        # Should still be one node with flag=true
        result = gf.execute("MATCH (n:Node {id: 1}) RETURN count(n) as count, n.flag as flag")
        assert result[0]["count"].value == 1
        assert result[0]["flag"].value is True


class TestPerformance:
    """Test performance characteristics of MERGE ON MATCH SET."""

    def test_bulk_merge_with_on_match(self):
        """Test bulk MERGE operations with ON MATCH SET."""
        gf = GraphForge()

        # Create nodes
        for i in range(50):
            gf.execute(f"CREATE (n:Node {{id: {i}}})")

        # Update all with ON MATCH
        for i in range(50):
            gf.execute(f"""
                MERGE (n:Node {{id: {i}}})
                ON MATCH SET n.processed = true
            """)

        # Verify all updated
        result = gf.execute("MATCH (n:Node) WHERE n.processed = true RETURN count(n) as count")
        assert result[0]["count"].value == 50

    def test_alternating_create_and_match(self):
        """Test alternating between create and match."""
        gf = GraphForge()

        # Create/match pattern
        for i in range(10):
            gf.execute(f"""
                MERGE (n:Node {{id: 1}})
                ON CREATE SET n.created = {i}
                ON MATCH SET n.matched = {i}
            """)

        # Should have created on first iteration, matched on rest
        result = gf.execute("MATCH (n:Node {id: 1}) RETURN n.created as c, n.matched as m")
        assert result[0]["c"].value == 0  # Set on first create
        assert result[0]["m"].value == 9  # Last match value
