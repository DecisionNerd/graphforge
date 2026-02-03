"""Unit tests for WITH clause with aggregation."""

from graphforge import GraphForge


class TestWithAggregation:
    """Test WITH clause with aggregation functions."""

    def test_with_single_grouping_variable(self):
        """Test WITH with single grouping variable."""
        gf = GraphForge()
        gf.execute("CREATE (p1:Person {name: 'Alice'})")
        gf.execute("CREATE (p2:Person {name: 'Bob'})")
        gf.execute("CREATE (m1:Movie {title: 'Movie1'})")
        gf.execute("CREATE (m2:Movie {title: 'Movie2'})")
        gf.execute("MATCH (p:Person {name: 'Alice'}), (m:Movie) CREATE (p)-[:ACTED_IN]->(m)")
        gf.execute(
            "MATCH (p:Person {name: 'Bob'}), (m:Movie {title: 'Movie1'}) CREATE (p)-[:ACTED_IN]->(m)"
        )

        results = gf.execute("""
            MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
            WITH p, count(m) as movie_count
            RETURN p.name as actor, movie_count
            ORDER BY movie_count DESC
        """)

        assert len(results) == 2
        assert results[0]["actor"].value == "Alice"
        assert results[0]["movie_count"].value == 2
        assert results[1]["actor"].value == "Bob"
        assert results[1]["movie_count"].value == 1

    def test_with_multiple_grouping_variables(self):
        """Test WITH with multiple grouping variables."""
        gf = GraphForge()
        gf.execute("CREATE (p1:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (p2:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (p3:Person {name: 'Charlie', age: 30})")

        results = gf.execute("""
            MATCH (p:Person)
            WITH p.age as age, count(p) as person_count
            RETURN age, person_count
            ORDER BY age
        """)

        assert len(results) == 2
        assert results[0]["age"].value == 25
        assert results[0]["person_count"].value == 1
        assert results[1]["age"].value == 30
        assert results[1]["person_count"].value == 2

    def test_with_aggregation_then_filter(self):
        """Test WITH aggregation followed by WHERE filter."""
        gf = GraphForge()
        for i in range(5):
            gf.execute(f"CREATE (p:Person {{id: {i}}})")
            gf.execute(f"CREATE (m:Movie {{id: {i}}})")
            # Person 0 acts in 3 movies, Person 1 in 2, others in 1
            if i < 3:
                gf.execute(
                    "MATCH (p:Person {id: 0}), (m:Movie {id: "
                    + str(i)
                    + "}) CREATE (p)-[:ACTED_IN]->(m)"
                )
            if i < 2:
                gf.execute(
                    "MATCH (p:Person {id: 1}), (m:Movie {id: "
                    + str(i)
                    + "}) CREATE (p)-[:ACTED_IN]->(m)"
                )
            gf.execute(
                f"MATCH (p:Person {{id: {i}}}), (m:Movie {{id: {i}}}) CREATE (p)-[:ACTED_IN]->(m)"
            )

        results = gf.execute("""
            MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
            WITH p, count(m) as movie_count
            WHERE movie_count > 1
            RETURN p.id as id, movie_count
            ORDER BY movie_count DESC
        """)

        assert len(results) == 2
        assert results[0]["id"].value == 0
        assert results[0]["movie_count"].value == 4  # Acts in movies 0, 1, 2, and their own movie 0
        assert results[1]["id"].value == 1
        assert results[1]["movie_count"].value == 2

    def test_with_aggregation_sum(self):
        """Test WITH with SUM aggregation."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")
        gf.execute("CREATE (p:Person {name: 'Bob'})")
        gf.execute("CREATE (t1:Transaction {person: 'Alice', amount: 100})")
        gf.execute("CREATE (t2:Transaction {person: 'Alice', amount: 200})")
        gf.execute("CREATE (t3:Transaction {person: 'Bob', amount: 150})")

        results = gf.execute("""
            MATCH (t:Transaction)
            WITH t.person as person, sum(t.amount) as total
            RETURN person, total
            ORDER BY total DESC
        """)

        assert len(results) == 2
        assert results[0]["person"].value == "Alice"
        assert results[0]["total"].value == 300
        assert results[1]["person"].value == "Bob"
        assert results[1]["total"].value == 150

    def test_with_aggregation_avg(self):
        """Test WITH with AVG aggregation."""
        gf = GraphForge()
        gf.execute("CREATE (p:Product {category: 'Electronics', price: 100})")
        gf.execute("CREATE (p:Product {category: 'Electronics', price: 200})")
        gf.execute("CREATE (p:Product {category: 'Books', price: 20})")
        gf.execute("CREATE (p:Product {category: 'Books', price: 30})")

        results = gf.execute("""
            MATCH (p:Product)
            WITH p.category as category, avg(p.price) as avg_price
            RETURN category, avg_price
            ORDER BY avg_price DESC
        """)

        assert len(results) == 2
        assert results[0]["category"].value == "Electronics"
        assert results[0]["avg_price"].value == 150.0
        assert results[1]["category"].value == "Books"
        assert results[1]["avg_price"].value == 25.0

    def test_with_aggregation_min_max(self):
        """Test WITH with MIN and MAX aggregations."""
        gf = GraphForge()
        gf.execute("CREATE (p:Product {category: 'Electronics', price: 100})")
        gf.execute("CREATE (p:Product {category: 'Electronics', price: 200})")
        gf.execute("CREATE (p:Product {category: 'Books', price: 20})")

        results = gf.execute("""
            MATCH (p:Product)
            WITH p.category as category, min(p.price) as min_price, max(p.price) as max_price
            RETURN category, min_price, max_price
            ORDER BY category
        """)

        assert len(results) == 2
        assert results[0]["category"].value == "Books"
        assert results[0]["min_price"].value == 20
        assert results[0]["max_price"].value == 20
        assert results[1]["category"].value == "Electronics"
        assert results[1]["min_price"].value == 100
        assert results[1]["max_price"].value == 200

    def test_with_collect(self):
        """Test WITH with COLLECT aggregation."""
        gf = GraphForge()
        gf.execute("CREATE (p1:Person {name: 'Alice'})")
        gf.execute("CREATE (p2:Person {name: 'Bob'})")
        gf.execute("CREATE (m1:Movie {title: 'Movie1'})")
        gf.execute("CREATE (m2:Movie {title: 'Movie2'})")
        gf.execute("MATCH (p:Person {name: 'Alice'}), (m:Movie) CREATE (p)-[:ACTED_IN]->(m)")
        gf.execute(
            "MATCH (p:Person {name: 'Bob'}), (m:Movie {title: 'Movie1'}) CREATE (p)-[:ACTED_IN]->(m)"
        )

        results = gf.execute("""
            MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
            WITH p, collect(m.title) as movies
            RETURN p.name as actor, movies
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["actor"].value == "Alice"
        assert len(results[0]["movies"].value) == 2
        assert results[1]["actor"].value == "Bob"
        assert len(results[1]["movies"].value) == 1


class TestWithAggregationEdgeCases:
    """Test edge cases for WITH aggregation."""

    def test_with_aggregation_no_results(self):
        """Test WITH aggregation with no matching results."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice'})")

        results = gf.execute("""
            MATCH (p:Person)-[:ACTED_IN]->(m:Movie)
            WITH p, count(m) as movie_count
            RETURN p.name as actor, movie_count
        """)

        assert len(results) == 0

    def test_with_aggregation_only_aggregates(self):
        """Test WITH with only aggregates, no grouping."""
        gf = GraphForge()
        for i in range(10):
            gf.execute(f"CREATE (p:Person {{id: {i}}})")

        results = gf.execute("""
            MATCH (p:Person)
            WITH count(p) as total
            RETURN total
        """)

        assert len(results) == 1
        assert results[0]["total"].value == 10

    def test_with_aggregation_chained(self):
        """Test multiple WITH clauses with aggregation."""
        gf = GraphForge()
        gf.execute("CREATE (p1:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (p2:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (p3:Person {name: 'Charlie', age: 30})")

        results = gf.execute("""
            MATCH (p:Person)
            WITH p.age as age, count(p) as person_count
            WITH age, person_count
            WHERE person_count > 1
            RETURN age, person_count
        """)

        assert len(results) == 1
        assert results[0]["age"].value == 30
        assert results[0]["person_count"].value == 2

    def test_with_aggregation_property_access(self):
        """Test WITH aggregation accessing properties after grouping."""
        gf = GraphForge()
        gf.execute("CREATE (p1:Person {name: 'Alice', city: 'NYC'})")
        gf.execute("CREATE (p2:Person {name: 'Bob', city: 'LA'})")
        gf.execute("CREATE (p3:Person {name: 'Charlie', city: 'NYC'})")

        results = gf.execute("""
            MATCH (p:Person)
            WITH p.city as city, count(p) as count
            RETURN city, count
            ORDER BY count DESC
        """)

        assert len(results) == 2
        assert results[0]["city"].value == "NYC"
        assert results[0]["count"].value == 2
        assert results[1]["city"].value == "LA"
        assert results[1]["count"].value == 1
