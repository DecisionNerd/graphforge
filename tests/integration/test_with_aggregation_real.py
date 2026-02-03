"""Integration tests for WITH clause with aggregation in real-world scenarios."""

from graphforge import GraphForge


class TestRealWorldAggregationPatterns:
    """Test real-world aggregation patterns with WITH clause."""

    def test_top_n_by_count_pattern(self):
        """Test common pattern: find top N entities by count."""
        gf = GraphForge()

        # Create social network
        gf.execute("CREATE (alice:Person {name: 'Alice'})")
        gf.execute("CREATE (bob:Person {name: 'Bob'})")
        gf.execute("CREATE (charlie:Person {name: 'Charlie'})")
        gf.execute("CREATE (david:Person {name: 'David'})")

        # Alice has 3 friends, Bob 2, Charlie 1, David 0
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:FRIENDS_WITH]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:FRIENDS_WITH]->(c)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (d:Person {name: 'David'}) CREATE (a)-[:FRIENDS_WITH]->(d)"
        )
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:FRIENDS_WITH]->(c)"
        )
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (d:Person {name: 'David'}) CREATE (b)-[:FRIENDS_WITH]->(d)"
        )
        gf.execute(
            "MATCH (c:Person {name: 'Charlie'}), (d:Person {name: 'David'}) CREATE (c)-[:FRIENDS_WITH]->(d)"
        )

        # Find top 3 most connected people
        results = gf.execute("""
            MATCH (p:Person)-[:FRIENDS_WITH]->(friend)
            WITH p, count(friend) as friend_count
            RETURN p.name as person, friend_count
            ORDER BY friend_count DESC
            LIMIT 3
        """)

        assert len(results) == 3
        assert results[0]["person"].value == "Alice"
        assert results[0]["friend_count"].value == 3
        assert results[1]["person"].value == "Bob"
        assert results[1]["friend_count"].value == 2

    def test_aggregation_with_filtering(self):
        """Test aggregation with post-aggregation filtering."""
        gf = GraphForge()

        # Create e-commerce data
        for i in range(5):
            gf.execute(f"CREATE (u:User {{id: {i}, name: 'User{i}'}})")

        # User 0: 5 orders, User 1: 3 orders, User 2: 1 order
        for i in range(5):
            gf.execute(f"CREATE (o:Order {{id: {i}, user_id: 0, amount: 100}})")
        for i in range(3):
            gf.execute(f"CREATE (o:Order {{id: {i + 5}, user_id: 1, amount: 50}})")
        gf.execute("CREATE (o:Order {id: 8, user_id: 2, amount: 200})")

        # Find users with more than 2 orders
        results = gf.execute("""
            MATCH (o:Order)
            WITH o.user_id as user_id, count(o) as order_count, sum(o.amount) as total_spent
            WHERE order_count > 2
            RETURN user_id, order_count, total_spent
            ORDER BY total_spent DESC
        """)

        assert len(results) == 2
        assert results[0]["user_id"].value == 0
        assert results[0]["order_count"].value == 5
        assert results[0]["total_spent"].value == 500

    def test_multi_level_aggregation(self):
        """Test chained aggregations."""
        gf = GraphForge()

        # Create hierarchical data
        gf.execute("CREATE (dept1:Department {name: 'Engineering'})")
        gf.execute("CREATE (dept2:Department {name: 'Sales'})")
        gf.execute("CREATE (emp1:Employee {name: 'Alice', salary: 100000, dept: 'Engineering'})")
        gf.execute("CREATE (emp2:Employee {name: 'Bob', salary: 120000, dept: 'Engineering'})")
        gf.execute("CREATE (emp3:Employee {name: 'Charlie', salary: 80000, dept: 'Sales'})")
        gf.execute("CREATE (emp4:Employee {name: 'David', salary: 90000, dept: 'Sales'})")

        # Average salary by department, then filter for high-paying departments
        results = gf.execute("""
            MATCH (e:Employee)
            WITH e.dept as dept, avg(e.salary) as avg_salary
            WHERE avg_salary > 100000
            RETURN dept, avg_salary
        """)

        assert len(results) == 1
        assert results[0]["dept"].value == "Engineering"
        assert results[0]["avg_salary"].value == 110000.0

    def test_graph_analytics_pattern(self):
        """Test graph analytics pattern with aggregation."""
        gf = GraphForge()

        # Create citation network
        gf.execute("CREATE (p1:Paper {title: 'Paper1'})")
        gf.execute("CREATE (p2:Paper {title: 'Paper2'})")
        gf.execute("CREATE (p3:Paper {title: 'Paper3'})")
        gf.execute("CREATE (p4:Paper {title: 'Paper4'})")

        # Citation relationships
        gf.execute(
            "MATCH (p1:Paper {title: 'Paper1'}), (p2:Paper {title: 'Paper2'}) CREATE (p2)-[:CITES]->(p1)"
        )
        gf.execute(
            "MATCH (p1:Paper {title: 'Paper1'}), (p3:Paper {title: 'Paper3'}) CREATE (p3)-[:CITES]->(p1)"
        )
        gf.execute(
            "MATCH (p1:Paper {title: 'Paper1'}), (p4:Paper {title: 'Paper4'}) CREATE (p4)-[:CITES]->(p1)"
        )
        gf.execute(
            "MATCH (p2:Paper {title: 'Paper2'}), (p4:Paper {title: 'Paper4'}) CREATE (p4)-[:CITES]->(p2)"
        )

        # Find most cited papers
        results = gf.execute("""
            MATCH (p:Paper)<-[:CITES]-(citing)
            WITH p, count(citing) as citation_count
            RETURN p.title as paper, citation_count
            ORDER BY citation_count DESC
        """)

        assert len(results) == 2
        assert results[0]["paper"].value == "Paper1"
        assert results[0]["citation_count"].value == 3
        assert results[1]["paper"].value == "Paper2"
        assert results[1]["citation_count"].value == 1

    def test_time_series_aggregation(self):
        """Test time series aggregation pattern."""
        gf = GraphForge()

        # Create time series data
        gf.execute("CREATE (e1:Event {type: 'login', hour: 9, count: 100})")
        gf.execute("CREATE (e2:Event {type: 'login', hour: 10, count: 150})")
        gf.execute("CREATE (e3:Event {type: 'login', hour: 11, count: 120})")
        gf.execute("CREATE (e4:Event {type: 'purchase', hour: 9, count: 20})")
        gf.execute("CREATE (e5:Event {type: 'purchase', hour: 10, count: 30})")

        # Aggregate events by type
        results = gf.execute("""
            MATCH (e:Event)
            WITH e.type as event_type, sum(e.count) as total_count, avg(e.count) as avg_count
            RETURN event_type, total_count, avg_count
            ORDER BY total_count DESC
        """)

        assert len(results) == 2
        assert results[0]["event_type"].value == "login"
        assert results[0]["total_count"].value == 370
        assert results[1]["event_type"].value == "purchase"
        assert results[1]["total_count"].value == 50


class TestComplexWithPatterns:
    """Test complex WITH clause patterns."""

    def test_with_distinct_and_aggregation(self):
        """Test WITH with DISTINCT and aggregation."""
        gf = GraphForge()

        gf.execute("CREATE (p:Person {name: 'Alice', skill: 'Python'})")
        gf.execute("CREATE (p:Person {name: 'Bob', skill: 'Python'})")
        gf.execute("CREATE (p:Person {name: 'Charlie', skill: 'Java'})")

        # Count distinct skills
        results = gf.execute("""
            MATCH (p:Person)
            WITH DISTINCT p.skill as skill
            RETURN count(skill) as skill_count
        """)

        assert len(results) == 1
        assert results[0]["skill_count"].value == 2

    def test_with_aggregation_and_limit(self):
        """Test WITH aggregation with LIMIT."""
        gf = GraphForge()

        for i in range(10):
            gf.execute(f"CREATE (p:Product {{id: {i}, category: 'Cat{i % 3}', price: {i * 10}}})")

        # Get top 2 categories by average price
        results = gf.execute("""
            MATCH (p:Product)
            WITH p.category as category, avg(p.price) as avg_price
            RETURN category, avg_price
            ORDER BY avg_price DESC
            LIMIT 2
        """)

        assert len(results) == 2

    def test_with_nested_property_access(self):
        """Test WITH with nested property access in aggregation."""
        gf = GraphForge()

        gf.execute("CREATE (u:User {name: 'Alice'})")
        gf.execute("CREATE (u:User {name: 'Bob'})")
        gf.execute("CREATE (p:Post {author: 'Alice', likes: 10})")
        gf.execute("CREATE (p:Post {author: 'Alice', likes: 20})")
        gf.execute("CREATE (p:Post {author: 'Bob', likes: 5})")

        # Total likes by author
        results = gf.execute("""
            MATCH (p:Post)
            WITH p.author as author, sum(p.likes) as total_likes
            RETURN author, total_likes
            ORDER BY total_likes DESC
        """)

        assert len(results) == 2
        assert results[0]["author"].value == "Alice"
        assert results[0]["total_likes"].value == 30
        assert results[1]["author"].value == "Bob"
        assert results[1]["total_likes"].value == 5
