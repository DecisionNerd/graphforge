"""Integration tests for pattern comprehension."""

from graphforge.api import GraphForge


class TestBasicPatternComprehension:
    """Basic pattern comprehension tests."""

    def test_simple_node_pattern(self):
        """Basic pattern comprehension with node pattern."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'}), (:Person {name: 'Bob'})")

        results = gf.execute(
            """
            MATCH (p:Person)
            RETURN [(x:Person) | x.name] AS names
            ORDER BY p.name
            LIMIT 1
            """
        )

        assert len(results) == 1
        names = results[0]["names"].value
        assert len(names) == 2
        # Results are unordered from pattern comprehension
        name_values = {n.value for n in names}
        assert name_values == {"Alice", "Bob"}

    def test_relationship_pattern(self):
        """Pattern comprehension with relationship pattern."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'}),
                   (a)-[:KNOWS]->(c:Person {name: 'Charlie'})
            """
        )

        results = gf.execute(
            """
            MATCH (p:Person {name: 'Alice'})
            RETURN [(p)-[:KNOWS]->(friend) | friend.name] AS friends
            """
        )

        assert len(results) == 1
        friends = results[0]["friends"].value
        assert len(friends) == 2
        friend_names = {f.value for f in friends}
        assert friend_names == {"Bob", "Charlie"}

    def test_with_property_access(self):
        """Pattern comprehension accessing properties."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice', age: 30}),
                   (:Person {name: 'Bob', age: 25})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) | p.age] AS ages
            """
        )

        assert len(results) == 1
        ages = results[0]["ages"].value
        assert len(ages) == 2
        age_values = {a.value for a in ages}
        assert age_values == {25, 30}


class TestPatternComprehensionWithFilter:
    """Pattern comprehension with WHERE filter tests."""

    def test_simple_filter(self):
        """Pattern comprehension with WHERE filter."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice', age: 30}),
                   (:Person {name: 'Bob', age: 25}),
                   (:Person {name: 'Charlie', age: 35})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) WHERE p.age > 28 | p.name] AS names
            """
        )

        assert len(results) == 1
        names = results[0]["names"].value
        assert len(names) == 2
        name_values = {n.value for n in names}
        assert name_values == {"Alice", "Charlie"}

    def test_relationship_filter(self):
        """Pattern comprehension with relationship and WHERE filter."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'}),
                   (a)-[:KNOWS {since: 2022}]->(c:Person {name: 'Charlie'})
            """
        )

        results = gf.execute(
            """
            MATCH (p:Person {name: 'Alice'})
            RETURN [(p)-[r:KNOWS]->(f) WHERE r.since > 2021 | f.name] AS recent_friends
            """
        )

        assert len(results) == 1
        friends = results[0]["recent_friends"].value
        assert len(friends) == 1
        assert friends[0].value == "Charlie"

    def test_complex_filter(self):
        """Pattern comprehension with complex WHERE filter."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice', age: 30, city: 'NYC'}),
                   (:Person {name: 'Bob', age: 25, city: 'LA'}),
                   (:Person {name: 'Charlie', age: 35, city: 'NYC'})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) WHERE p.age > 28 AND p.city = 'NYC' | p.name] AS names
            """
        )

        assert len(results) == 1
        names = results[0]["names"].value
        assert len(names) == 2
        name_values = {n.value for n in names}
        assert name_values == {"Alice", "Charlie"}


class TestPatternComprehensionNested:
    """Nested pattern comprehension tests."""

    def test_nested_in_return(self):
        """Pattern comprehension nested in RETURN clause."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'}),
                   (b)-[:KNOWS]->(c:Person {name: 'Charlie'})
            """
        )

        results = gf.execute(
            """
            MATCH (p:Person {name: 'Alice'})
            RETURN p.name AS name, [(p)-[:KNOWS]->(f) | f.name] AS friends
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        friends = results[0]["friends"].value
        assert len(friends) == 1
        assert friends[0].value == "Bob"

    def test_multiple_pattern_comprehensions(self):
        """Multiple pattern comprehensions in one query."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice'}), (:Person {name: 'Bob'}),
                   (:Company {name: 'TechCorp'}), (:Company {name: 'DataCo'})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) | p.name] AS people,
                   [(c:Company) | c.name] AS companies
            """
        )

        assert len(results) == 1
        people = results[0]["people"].value
        companies = results[0]["companies"].value

        assert len(people) == 2
        assert len(companies) == 2

        people_names = {p.value for p in people}
        company_names = {c.value for c in companies}

        assert people_names == {"Alice", "Bob"}
        assert company_names == {"TechCorp", "DataCo"}


class TestPatternComprehensionEdgeCases:
    """Edge case tests for pattern comprehension."""

    def test_empty_result(self):
        """Pattern comprehension with no matches."""
        gf = GraphForge()

        results = gf.execute(
            """
            RETURN [(p:Person) | p.name] AS names
            """
        )

        assert len(results) == 1
        names = results[0]["names"].value
        assert len(names) == 0
        assert names == []

    def test_filter_excludes_all(self):
        """Pattern comprehension where filter excludes all matches."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice', age: 30}),
                   (:Person {name: 'Bob', age: 25})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) WHERE p.age > 40 | p.name] AS names
            """
        )

        assert len(results) == 1
        names = results[0]["names"].value
        assert len(names) == 0

    def test_null_property_in_map(self):
        """Pattern comprehension with NULL property."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice', age: 30}),
                   (:Person {name: 'Bob'})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) | p.age] AS ages
            """
        )

        assert len(results) == 1
        ages = results[0]["ages"].value
        assert len(ages) == 2
        # One should be 30, one should be NULL
        age_values = [a.value for a in ages]
        assert 30 in age_values
        assert None in age_values

    def test_with_expression_in_map(self):
        """Pattern comprehension with complex expression."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (:Person {name: 'Alice', age: 30}),
                   (:Person {name: 'Bob', age: 25})
            """
        )

        results = gf.execute(
            """
            RETURN [(p:Person) | p.age * 2] AS doubled_ages
            """
        )

        assert len(results) == 1
        ages = results[0]["doubled_ages"].value
        assert len(ages) == 2
        age_values = {a.value for a in ages}
        assert age_values == {50, 60}

    def test_with_correlated_variable(self):
        """Pattern comprehension accessing outer scope variable."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (a:Person {name: 'Alice', team: 'A'}),
                   (b:Person {name: 'Bob', team: 'A'}),
                   (c:Person {name: 'Charlie', team: 'B'})
            """
        )

        results = gf.execute(
            """
            MATCH (p:Person {name: 'Alice'})
            RETURN [(x:Person) WHERE x.team = p.team | x.name] AS teammates
            """
        )

        assert len(results) == 1
        teammates = results[0]["teammates"].value
        assert len(teammates) == 2
        teammate_names = {t.value for t in teammates}
        assert teammate_names == {"Alice", "Bob"}


class TestPatternComprehensionInClauses:
    """Pattern comprehension in various clauses."""

    def test_in_where_clause(self):
        """Pattern comprehension in WHERE clause."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'}),
                   (c:Person {name: 'Charlie'})
            """
        )

        results = gf.execute(
            """
            MATCH (p:Person)
            WHERE size([(p)-[:KNOWS]->() | 1]) > 0
            RETURN p.name AS name
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_in_with_clause(self):
        """Pattern comprehension in WITH clause."""
        gf = GraphForge()
        gf.execute(
            """
            CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'}),
                   (a)-[:KNOWS]->(c:Person {name: 'Charlie'})
            """
        )

        results = gf.execute(
            """
            MATCH (p:Person {name: 'Alice'})
            WITH p, [(p)-[:KNOWS]->(f) | f.name] AS friends
            RETURN p.name AS name, friends
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        friends = results[0]["friends"].value
        assert len(friends) == 2
        friend_names = {f.value for f in friends}
        assert friend_names == {"Bob", "Charlie"}
