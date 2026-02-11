"""Integration tests for pattern predicates (WHERE inside patterns)."""

from graphforge.api import GraphForge


class TestPatternPredicatesBasic:
    """Basic pattern predicate tests."""

    def test_simple_property_filter(self):
        """Filter edges by property in pattern WHERE clause."""
        gf = GraphForge()
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})"
        )
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2015}]->(c:Person {name: 'Charlie'})"
        )

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.since > 2018]->(b:Person)
            RETURN a.name AS a_name, b.name AS b_name, r.since AS since
            """
        )

        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"
        assert results[0]["since"].value == 2020

    def test_pattern_predicate_with_equality(self):
        """Pattern predicate with equality check."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:WORKS_AT {role: 'engineer'}]->(c:Company)")
        gf.execute("CREATE (b:Person)-[:WORKS_AT {role: 'manager'}]->(c:Company)")

        results = gf.execute(
            """
            MATCH (p:Person)-[r:WORKS_AT WHERE r.role = 'engineer']->(c:Company)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 1

    def test_pattern_predicate_undirected(self):
        """Pattern predicate on undirected relationship."""
        gf = GraphForge()
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[:FRIEND {strength: 0.9}]-(b:Person {name: 'Bob'})"
        )
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[:FRIEND {strength: 0.3}]-(c:Person {name: 'Charlie'})"
        )

        results = gf.execute(
            """
            MATCH (a:Person)-[r:FRIEND WHERE r.strength > 0.5]-(b:Person)
            WHERE a.name = 'Alice'
            RETURN b.name AS name
            ORDER BY name
            """
        )

        # Since we anchor on a.name = 'Alice', we only get (Alice)-[r]-(Bob) once
        # (not twice, because the WHERE clause filters to only rows where a is Alice)
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_pattern_predicate_with_complex_expression(self):
        """Pattern predicate with AND expression."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2020, active: true}]->(b:Person)")
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2020, active: false}]->(c:Person)")
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2015, active: true}]->(d:Person)")

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.since > 2018 AND r.active = true]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 1

    def test_pattern_predicate_no_variable(self):
        """Pattern predicate on anonymous relationship."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:RATED {score: 5}]->(m:Movie)")
        gf.execute("CREATE (b:Person)-[:RATED {score: 3}]->(m:Movie)")

        results = gf.execute(
            """
            MATCH (p:Person)-[r:RATED WHERE r.score >= 4]->(m:Movie)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 1


class TestPatternPredicatesVariableLength:
    """Pattern predicate tests for variable-length paths."""

    def test_variable_length_with_predicate(self):
        """Filter edges in variable-length path."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {name: 'A'})-[:LINK {weight: 0.9}]->(b:Node {name: 'B'})")
        gf.execute(
            "MATCH (b:Node {name: 'B'}) CREATE (b)-[:LINK {weight: 0.8}]->(c:Node {name: 'C'})"
        )
        gf.execute(
            "MATCH (a:Node {name: 'A'}) CREATE (a)-[:LINK {weight: 0.2}]->(d:Node {name: 'D'})"
        )

        results = gf.execute(
            """
            MATCH (a:Node {name: 'A'})-[r:LINK*1..2 WHERE r.weight > 0.5]->(b:Node)
            RETURN b.name AS name
            ORDER BY name
            """
        )

        # Should find B (direct, weight 0.9) and C (through B, both edges > 0.5)
        # Should NOT find D (weight 0.2 < 0.5)
        assert len(results) == 2
        assert results[0]["name"].value == "B"
        assert results[1]["name"].value == "C"

    def test_variable_length_predicate_filters_all_edges(self):
        """Variable-length predicate must pass for ALL edges in path."""
        gf = GraphForge()
        gf.execute("CREATE (a:Node {name: 'A'})-[:LINK {cost: 1}]->(b:Node {name: 'B'})")
        gf.execute("MATCH (b:Node {name: 'B'}) CREATE (b)-[:LINK {cost: 10}]->(c:Node {name: 'C'})")
        gf.execute("MATCH (a:Node {name: 'A'}) CREATE (a)-[:LINK {cost: 2}]->(d:Node {name: 'D'})")
        gf.execute("MATCH (d:Node {name: 'D'}) CREATE (d)-[:LINK {cost: 3}]->(e:Node {name: 'E'})")

        results = gf.execute(
            """
            MATCH (a:Node {name: 'A'})-[r:LINK*1..2 WHERE r.cost < 5]->(b:Node)
            RETURN b.name AS name
            ORDER BY name
            """
        )

        # Should find B, D, E
        # Should NOT find C (path A->B->C has edge B->C with cost 10 > 5)
        assert len(results) == 3
        assert results[0]["name"].value == "B"
        assert results[1]["name"].value == "D"
        assert results[2]["name"].value == "E"


class TestPatternPredicatesCombinations:
    """Test pattern predicates combined with other features."""

    def test_pattern_predicate_with_multiple_conditions(self):
        """Pattern predicate with multiple AND conditions."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {type: 'friend', since: 2020}]->(:Person {name: 'Bob'})"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {type: 'friend', since: 2015}]->(:Person {name: 'Charlie'})"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS {type: 'colleague', since: 2020}]->(:Person {name: 'Dave'})"
        )

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.type = 'friend' AND r.since > 2018]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 1

    def test_pattern_predicate_with_external_where(self):
        """Pattern predicate combined with external WHERE clause."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {age: 30})-[:KNOWS {since: 2020}]->(b:Person {age: 25})")
        gf.execute("CREATE (a:Person {age: 30})-[:KNOWS {since: 2015}]->(c:Person {age: 35})")
        gf.execute("CREATE (d:Person {age: 20})-[:KNOWS {since: 2020}]->(e:Person {age: 25})")

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.since > 2018]->(b:Person)
            WHERE a.age >= 30
            RETURN count(*) AS cnt
            """
        )

        # Should match first relationship only
        assert results[0]["cnt"].value == 1

    def test_pattern_predicate_with_multiple_patterns(self):
        """Multiple patterns with different predicates."""
        gf = GraphForge()
        gf.execute(
            "CREATE (:Person {name: 'Alice'}), (:Person {name: 'Bob'}), (:Company {name: 'TechCorp'})"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'}) CREATE (a)-[:KNOWS {since: 2020}]->(b)"
        )
        gf.execute(
            "MATCH (b:Person {name: 'Bob'}), (c:Company {name: 'TechCorp'}) CREATE (b)-[:WORKS_AT {role: 'engineer'}]->(c)"
        )

        results = gf.execute(
            """
            MATCH (a:Person)-[r1:KNOWS WHERE r1.since > 2018]->(b:Person),
                  (b)-[r2:WORKS_AT WHERE r2.role = 'engineer']->(c:Company)
            RETURN a.name AS a_name, c.name AS c_name
            """
        )

        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["c_name"].value == "TechCorp"

    def test_pattern_predicate_with_null(self):
        """Pattern predicate handles NULL values correctly."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2020}]->(b:Person)")
        gf.execute("CREATE (a:Person)-[:KNOWS]->(c:Person)")  # No since property

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.since > 2018]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        # Only the first edge should match (second has NULL since)
        assert results[0]["cnt"].value == 1

    def test_pattern_predicate_or_expression(self):
        """Pattern predicate with OR expression."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:TAGGED {category: 'tech'}]->(p:Post)")
        gf.execute("CREATE (b:Person)-[:TAGGED {category: 'science'}]->(p:Post)")
        gf.execute("CREATE (c:Person)-[:TAGGED {category: 'sports'}]->(p:Post)")

        results = gf.execute(
            """
            MATCH (person:Person)-[r:TAGGED WHERE r.category = 'tech' OR r.category = 'science']->(p:Post)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 2


class TestPatternPredicatesEdgeCases:
    """Edge case tests for pattern predicates."""

    def test_pattern_predicate_always_false(self):
        """Pattern predicate that filters everything."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS]->(b:Person)")
        gf.execute("CREATE (a)-[:KNOWS]->(c:Person)")

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE false]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 0

    def test_pattern_predicate_always_true(self):
        """Pattern predicate that matches everything."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute(
            "MATCH (a:Person {name: 'Alice'}) CREATE (a)-[:KNOWS]->(c:Person {name: 'Charlie'})"
        )

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE true]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 2

    def test_pattern_predicate_with_function_call(self):
        """Pattern predicate using function."""
        gf = GraphForge()
        gf.execute(
            "CREATE (a:Person {name: 'Source'})-[:KNOWS {name: 'Alice'}]->(b:Person {name: 'B'})"
        )
        gf.execute(
            "MATCH (a:Person {name: 'Source'}) CREATE (a)-[:KNOWS {name: 'Bob'}]->(c:Person {name: 'C'})"
        )

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE length(r.name) = 3]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        # Only "Bob" has length 3
        assert results[0]["cnt"].value == 1

    def test_pattern_predicate_empty_result(self):
        """Pattern predicate with no matches."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person)-[:KNOWS {since: 2015}]->(b:Person)")

        results = gf.execute(
            """
            MATCH (a:Person)-[r:KNOWS WHERE r.since > 2020]->(b:Person)
            RETURN count(*) AS cnt
            """
        )

        assert results[0]["cnt"].value == 0
