"""Integration tests for aggregate pushdown optimization."""

from graphforge import GraphForge


class TestAggregatePushdownCOUNT:
    """Test COUNT aggregation pushdown with real queries."""

    def test_count_friends_by_person(self):
        """COUNT friends per person with pushdown."""
        gf = GraphForge()

        # Create social network
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute("CREATE (:Person {name: 'Charlie'})")

        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)"
        )
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:KNOWS]->(c)"
        )

        # Query with aggregation that can be pushed down
        query = """
        MATCH (p:Person)-[:KNOWS]->(friend)
        WITH p, count(friend) AS friend_count
        RETURN p.name AS name, friend_count
        ORDER BY friend_count DESC
        """

        results = gf.execute(query)

        # Verify results
        assert len(results) == 2  # Alice and Bob have friends
        assert results[0]["name"].value == "Alice"
        assert results[0]["friend_count"].value == 2
        assert results[1]["name"].value == "Bob"
        assert results[1]["friend_count"].value == 1

    def test_count_star_aggregation(self):
        """COUNT(*) should work with pushdown."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute("CREATE (:Person {name: 'Charlie'})")

        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)"
        )

        query = """
        MATCH (p:Person)-[:KNOWS]->(friend)
        WITH p, count(*) AS count
        RETURN p.name AS name, count
        ORDER BY count DESC
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["count"].value == 2

    def test_count_with_filter(self):
        """COUNT with WHERE predicate should work."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 30})")

        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)"
        )

        # Query with filter that can be pushed into traversal
        query = """
        MATCH (p:Person)-[:KNOWS]->(friend)
        WHERE friend.age > 20
        WITH p, count(friend) AS adult_friends
        RETURN p.name AS name, adult_friends
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["adult_friends"].value == 2


class TestAggregatePushdownSUM:
    """Test SUM aggregation pushdown."""

    def test_sum_edge_weights(self):
        """SUM edge properties during traversal."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Task {name: 'Task1'})")
        gf.execute("CREATE (:Task {name: 'Task2'})")
        gf.execute("CREATE (:Task {name: 'Task3'})")

        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (t:Task {name: 'Task1'}) "
            "CREATE (a)-[:WORKED_ON {hours: 5}]->(t)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (t:Task {name: 'Task2'}) "
            "CREATE (a)-[:WORKED_ON {hours: 3}]->(t)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (t:Task {name: 'Task3'}) "
            "CREATE (a)-[:WORKED_ON {hours: 7}]->(t)"
        )

        query = """
        MATCH (p:Person)-[w:WORKED_ON]->(t:Task)
        WITH p, sum(w.hours) AS total_hours
        RETURN p.name AS name, total_hours
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["total_hours"].value == 15

    def test_sum_integer_values(self):
        """SUM with integer values."""
        gf = GraphForge()

        gf.execute("CREATE (:Account {id: 'A1'})")
        gf.execute("CREATE (:Transaction {amount: 100})")
        gf.execute("CREATE (:Transaction {amount: 200})")
        gf.execute("CREATE (:Transaction {amount: 50})")

        gf.execute(
            "MATCH (a:Account {id: 'A1'}), (t:Transaction {amount: 100}) "
            "CREATE (a)-[:HAS_TRANSACTION]->(t)"
        )
        gf.execute(
            "MATCH (a:Account {id: 'A1'}), (t:Transaction {amount: 200}) "
            "CREATE (a)-[:HAS_TRANSACTION]->(t)"
        )
        gf.execute(
            "MATCH (a:Account {id: 'A1'}), (t:Transaction {amount: 50}) "
            "CREATE (a)-[:HAS_TRANSACTION]->(t)"
        )

        query = """
        MATCH (a:Account)-[:HAS_TRANSACTION]->(t:Transaction)
        WITH a, sum(t.amount) AS total
        RETURN a.id AS account, total
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["account"].value == "A1"
        assert results[0]["total"].value == 350


class TestAggregatePushdownMINMAX:
    """Test MIN/MAX aggregation pushdown."""

    def test_min_aggregation(self):
        """MIN aggregation with pushdown."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Product {name: 'P1', price: 100})")
        gf.execute("CREATE (:Product {name: 'P2', price: 50})")
        gf.execute("CREATE (:Product {name: 'P3', price: 150})")

        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (p:Product {name: 'P1'}) CREATE (a)-[:BOUGHT]->(p)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (p:Product {name: 'P2'}) CREATE (a)-[:BOUGHT]->(p)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (p:Product {name: 'P3'}) CREATE (a)-[:BOUGHT]->(p)"
        )

        query = """
        MATCH (p:Person)-[:BOUGHT]->(product:Product)
        WITH p, min(product.price) AS min_price
        RETURN p.name AS name, min_price
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["min_price"].value == 50

    def test_max_aggregation(self):
        """MAX aggregation with pushdown."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute("CREATE (:Score {value: 85})")
        gf.execute("CREATE (:Score {value: 92})")
        gf.execute("CREATE (:Score {value: 78})")

        gf.execute(
            "MATCH (p:Person {name: 'Bob'}), (s:Score {value: 85}) CREATE (p)-[:HAS_SCORE]->(s)"
        )
        gf.execute(
            "MATCH (p:Person {name: 'Bob'}), (s:Score {value: 92}) CREATE (p)-[:HAS_SCORE]->(s)"
        )
        gf.execute(
            "MATCH (p:Person {name: 'Bob'}), (s:Score {value: 78}) CREATE (p)-[:HAS_SCORE]->(s)"
        )

        query = """
        MATCH (p:Person)-[:HAS_SCORE]->(s:Score)
        WITH p, max(s.value) AS max_score
        RETURN p.name AS name, max_score
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["name"].value == "Bob"
        assert results[0]["max_score"].value == 92


class TestAggregatePushdownCorrectness:
    """Verify pushdown produces same results as non-pushdown."""

    def test_correctness_count(self):
        """Verify COUNT pushdown produces same results."""
        gf_with = GraphForge()
        gf_without = GraphForge()

        # Create identical graphs
        for gf in [gf_with, gf_without]:
            gf.execute("CREATE (:Person {name: 'A'})")
            gf.execute("CREATE (:Person {name: 'B'})")
            gf.execute("CREATE (:Person {name: 'C'})")
            gf.execute(
                "MATCH (a:Person {name: 'A'}), (b:Person {name: 'B'}) CREATE (a)-[:KNOWS]->(b)"
            )
            gf.execute(
                "MATCH (a:Person {name: 'A'}), (c:Person {name: 'C'}) CREATE (a)-[:KNOWS]->(c)"
            )
            gf.execute(
                "MATCH (b:Person {name: 'B'}), (c:Person {name: 'C'}) CREATE (b)-[:KNOWS]->(c)"
            )

        query = """
        MATCH (p:Person)-[:KNOWS]->(f)
        WITH p, count(f) AS count
        RETURN p.name AS name, count
        ORDER BY name
        """

        results_with = gf_with.execute(query)
        # Disable aggregate pushdown
        gf_without.optimizer.enable_aggregate_pushdown = False
        results_without = gf_without.execute(query)

        # Results should be identical
        assert len(results_with) == len(results_without)
        for i in range(len(results_with)):
            assert results_with[i]["name"].value == results_without[i]["name"].value
            assert results_with[i]["count"].value == results_without[i]["count"].value

    def test_correctness_sum(self):
        """Verify SUM pushdown produces same results."""
        gf_with = GraphForge()
        gf_without = GraphForge()

        # Create identical graphs
        for gf in [gf_with, gf_without]:
            gf.execute("CREATE (:Person {name: 'Alice'})")
            gf.execute("CREATE (:Task {id: 1})")
            gf.execute("CREATE (:Task {id: 2})")
            gf.execute(
                "MATCH (p:Person {name: 'Alice'}), (t:Task {id: 1}) "
                "CREATE (p)-[:WORKED {hours: 5}]->(t)"
            )
            gf.execute(
                "MATCH (p:Person {name: 'Alice'}), (t:Task {id: 2}) "
                "CREATE (p)-[:WORKED {hours: 3}]->(t)"
            )

        query = """
        MATCH (p:Person)-[w:WORKED]->(t)
        WITH p, sum(w.hours) AS total
        RETURN p.name AS name, total
        """

        results_with = gf_with.execute(query)
        gf_without.optimizer.enable_aggregate_pushdown = False
        results_without = gf_without.execute(query)

        assert len(results_with) == len(results_without)
        assert results_with[0]["name"].value == results_without[0]["name"].value
        assert results_with[0]["total"].value == results_without[0]["total"].value


class TestAggregatePushdownEmptyResults:
    """Test aggregate pushdown with empty results."""

    def test_count_with_no_matches(self):
        """COUNT when no edges match should return empty."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        # No relationships

        query = """
        MATCH (p:Person)-[:KNOWS]->(f)
        WITH p, count(f) AS count
        RETURN p.name AS name, count
        """

        results = gf.execute(query)

        # No matches, no results
        assert len(results) == 0

    def test_count_with_null_values(self):
        """COUNT(expr) should skip NULL values, COUNT(*) should count all."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Task {id: 1, status: 'done'})")
        gf.execute("CREATE (:Task {id: 2})")  # No status property
        gf.execute("CREATE (:Task {id: 3, status: 'todo'})")

        gf.execute("MATCH (p:Person {name: 'Alice'}), (t:Task {id: 1}) CREATE (p)-[:ASSIGNED]->(t)")
        gf.execute("MATCH (p:Person {name: 'Alice'}), (t:Task {id: 2}) CREATE (p)-[:ASSIGNED]->(t)")
        gf.execute("MATCH (p:Person {name: 'Alice'}), (t:Task {id: 3}) CREATE (p)-[:ASSIGNED]->(t)")

        # COUNT(*) should count all tasks (3)
        query_star = """
        MATCH (p:Person)-[:ASSIGNED]->(t:Task)
        WITH p, count(*) AS total_tasks
        RETURN p.name AS name, total_tasks
        """
        results_star = gf.execute(query_star)
        assert len(results_star) == 1
        assert results_star[0]["total_tasks"].value == 3

        # COUNT(t.status) should only count non-NULL status values (2)
        query_expr = """
        MATCH (p:Person)-[:ASSIGNED]->(t:Task)
        WITH p, count(t.status) AS tasks_with_status
        RETURN p.name AS name, tasks_with_status
        """
        results_expr = gf.execute(query_expr)
        assert len(results_expr) == 1
        assert results_expr[0]["tasks_with_status"].value == 2

    def test_sum_with_null_values(self):
        """SUM should skip NULL values."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Task {id: 1})")
        gf.execute("CREATE (:Task {id: 2})")

        # One edge has hours, one doesn't
        gf.execute(
            "MATCH (p:Person {name: 'Alice'}), (t:Task {id: 1}) "
            "CREATE (p)-[:WORKED {hours: 5}]->(t)"
        )
        gf.execute("MATCH (p:Person {name: 'Alice'}), (t:Task {id: 2}) CREATE (p)-[:WORKED]->(t)")

        query = """
        MATCH (p:Person)-[w:WORKED]->(t)
        WITH p, sum(w.hours) AS total
        RETURN p.name AS name, total
        """

        results = gf.execute(query)

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        # Should sum only the non-NULL value
        assert results[0]["total"].value == 5


class TestAggregatePushdownMultipleGroups:
    """Test aggregate pushdown with multiple groups."""

    def test_count_multiple_people(self):
        """COUNT aggregation for multiple people."""
        gf = GraphForge()

        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute("CREATE (:Person {name: 'Charlie'})")
        gf.execute("CREATE (:Person {name: 'Dave'})")

        # Alice knows 3 people
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS]->(b)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (c:Person {name: 'Charlie'}) CREATE (a)-[:KNOWS]->(c)"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (d:Person {name: 'Dave'}) CREATE (a)-[:KNOWS]->(d)"
        )

        # Bob knows 1 person
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Person {name: 'Charlie'}) CREATE (b)-[:KNOWS]->(c)"
        )

        # Charlie knows 2 people
        gf.execute(
            "MATCH (c:Person {name: 'Charlie'}), (a:Person {name: 'Alice'}) CREATE (c)-[:KNOWS]->(a)"
        )
        gf.execute(
            "MATCH (c:Person {name: 'Charlie'}), (d:Person {name: 'Dave'}) CREATE (c)-[:KNOWS]->(d)"
        )

        query = """
        MATCH (p:Person)-[:KNOWS]->(f)
        WITH p, count(f) AS friend_count
        RETURN p.name AS name, friend_count
        ORDER BY friend_count DESC, name
        """

        results = gf.execute(query)

        assert len(results) == 3
        assert results[0]["name"].value == "Alice"
        assert results[0]["friend_count"].value == 3
        assert results[1]["name"].value == "Charlie"
        assert results[1]["friend_count"].value == 2
        assert results[2]["name"].value == "Bob"
        assert results[2]["friend_count"].value == 1
