"""Unit tests for expression matching in aggregation."""

from graphforge import GraphForge


class TestExpressionMatching:
    """Test the _expressions_match helper method."""

    def test_variable_matching(self):
        """Test Variable expression matching."""
        gf = GraphForge()

        # Create some data
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("CREATE (p:Person {name: 'Bob'})")

        # Test that variable matching works
        results = gf.execute("""
            MATCH (p:Person)
            WITH p, p.name as name
            RETURN p.name as person, name
        """)

        assert len(results) == 2

    def test_property_access_matching(self):
        """Test PropertyAccess expression matching."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (p:Person {name: 'Bob', age: 30})")
        gf.execute("CREATE (p:Person {name: 'Charlie', age: 25})")

        # Test property access in grouping
        results = gf.execute("""
            MATCH (p:Person)
            WITH p.age as age, count(p) as count
            RETURN age, count
            ORDER BY count DESC
        """)

        assert len(results) == 2
        assert results[0]["age"].value == 30
        assert results[0]["count"].value == 2

    def test_function_call_matching(self):
        """Test FunctionCall expression matching in aggregation."""
        gf = GraphForge()

        gf.execute("CREATE (p1:Person {name: 'Alice'})")
        gf.execute("CREATE (p2:Person {name: 'Bob'})")
        gf.execute("CREATE (m1:Movie {title: 'Movie1'})")
        gf.execute("CREATE (m2:Movie {title: 'Movie2'})")
        gf.execute("MATCH (p:Person {name: 'Alice'}), (m:Movie) CREATE (p)-[:ACTED_IN]->(m)")
        gf.execute(
            "MATCH (p:Person {name: 'Bob'}), (m:Movie {title: 'Movie1'}) CREATE (p)-[:ACTED_IN]->(m)"
        )

        # Test function call in aggregation
        results = gf.execute("""
            MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
            WITH p, count(m) as movie_count
            RETURN p.name as actor, movie_count
            ORDER BY movie_count DESC
        """)

        assert len(results) == 2
        assert results[0]["movie_count"].value == 2

    def test_multiple_aggregation_functions(self):
        """Test multiple different aggregation functions in WITH."""
        gf = GraphForge()

        gf.execute("CREATE (p:Product {category: 'A', price: 100})")
        gf.execute("CREATE (p:Product {category: 'A', price: 200})")
        gf.execute("CREATE (p:Product {category: 'B', price: 50})")

        # Test multiple aggregation functions
        results = gf.execute("""
            MATCH (p:Product)
            WITH p.category as cat, count(p) as cnt, avg(p.price) as avg_price, sum(p.price) as total
            RETURN cat, cnt, avg_price, total
            ORDER BY cat
        """)

        assert len(results) == 2
        assert results[0]["cat"].value == "A"
        assert results[0]["cnt"].value == 2
        assert results[0]["avg_price"].value == 150.0
        assert results[0]["total"].value == 300

    def test_nested_property_in_aggregation(self):
        """Test nested property access in aggregation."""
        gf = GraphForge()

        gf.execute("CREATE (u:User {name: 'Alice'})")
        gf.execute("CREATE (p1:Post {author: 'Alice', likes: 10})")
        gf.execute("CREATE (p2:Post {author: 'Alice', likes: 20})")

        # Test property access matching with aggregation
        results = gf.execute("""
            MATCH (p:Post)
            WITH p.author as author, sum(p.likes) as total_likes, max(p.likes) as max_likes
            RETURN author, total_likes, max_likes
        """)

        assert len(results) == 1
        assert results[0]["author"].value == "Alice"
        assert results[0]["total_likes"].value == 30
        assert results[0]["max_likes"].value == 20

    def test_aggregation_with_collect_distinct(self):
        """Test COLLECT DISTINCT in WITH clause."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice', city: 'NYC'})")
        gf.execute("CREATE (p:Person {name: 'Bob', city: 'NYC'})")
        gf.execute("CREATE (p:Person {name: 'Charlie', city: 'LA'})")

        # Test COLLECT DISTINCT
        results = gf.execute("""
            MATCH (p:Person)
            WITH collect(DISTINCT p.city) as cities, count(p) as total
            RETURN cities, total
        """)

        assert len(results) == 1
        assert len(results[0]["cities"].value) == 2
        assert results[0]["total"].value == 3
