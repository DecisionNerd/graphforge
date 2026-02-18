"""Integration tests for CALL { } subqueries."""

from graphforge.api import GraphForge


class TestCallBasic:
    """Basic CALL subquery tests."""

    def test_simple_call_match_return(self):
        """Basic CALL with MATCH RETURN."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'}), (:Person {name: 'Bob'})")

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person)
                RETURN p.name AS name
            }
            RETURN name
            ORDER BY name
            """
        )

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Bob"

    def test_call_with_create(self):
        """CALL with CREATE statement."""
        gf = GraphForge()
        results = gf.execute(
            """
            CALL {
                CREATE (p:Person {name: 'Charlie'})
                RETURN p.name AS name
            }
            RETURN name
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Charlie"

        # Verify node was created
        verify = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(verify) == 1
        assert verify[0]["name"].value == "Charlie"

    def test_call_with_aggregation(self):
        """CALL with aggregation inside."""
        gf = GraphForge()
        gf.execute("CREATE (:Person), (:Person), (:Person)")

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person)
                RETURN count(p) AS cnt
            }
            RETURN cnt
            """
        )

        assert len(results) == 1
        assert results[0]["cnt"].value == 3


class TestCallCorrelated:
    """Test correlated CALL subqueries (accessing outer scope)."""

    def test_call_with_outer_variable(self):
        """CALL accessing variable from outer scope."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Bob'})")
        gf.execute("CREATE (:Person {name: 'Alice'})-[:KNOWS]->(:Person {name: 'Charlie'})")

        results = gf.execute(
            """
            MATCH (p:Person {name: 'Alice'})
            CALL {
                MATCH (p)-[:KNOWS]->(friend)
                RETURN friend.name AS friend_name
            }
            RETURN p.name AS name, friend_name
            ORDER BY friend_name
            """
        )

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[0]["friend_name"].value == "Bob"
        assert results[1]["name"].value == "Alice"
        assert results[1]["friend_name"].value == "Charlie"

    def test_call_with_multiple_outer_variables(self):
        """CALL accessing multiple outer variables."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")

        results = gf.execute(
            """
            MATCH (p:Person)
            WITH p, p.name AS name, p.age AS age
            CALL {
                RETURN 'processed' AS status
            }
            RETURN name, age, status
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[0]["status"].value == "processed"


class TestCallUnion:
    """Test CALL with UNION inside subquery."""

    def test_call_with_union(self):
        """CALL containing UNION."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'}), (:Company {name: 'TechCorp'})")

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person) RETURN p.name AS name
                UNION
                MATCH (c:Company) RETURN c.name AS name
            }
            RETURN name
            ORDER BY name
            """
        )

        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "TechCorp"

    def test_call_with_union_all(self):
        """CALL containing UNION ALL."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Alice'})")  # Duplicate

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person {name: 'Alice'}) RETURN p.name AS name
                UNION ALL
                MATCH (p:Person {name: 'Alice'}) RETURN p.name AS name
            }
            RETURN name
            """
        )

        # UNION ALL should keep duplicates: 2 from first branch + 2 from second = 4
        assert len(results) == 4
        # Verify all results are "Alice"
        assert all(r["name"].value == "Alice" for r in results)


class TestCallNested:
    """Test nested CALL subqueries."""

    def test_nested_call(self):
        """Nested CALL subqueries."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        results = gf.execute(
            """
            CALL {
                CALL {
                    MATCH (p:Person)
                    RETURN p.name AS inner_name
                }
                RETURN inner_name AS name
            }
            RETURN name
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"


class TestCallMultiple:
    """Test multiple CALL subqueries in one query."""

    def test_multiple_calls(self):
        """Multiple CALL clauses in sequence."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'}), (:Company {name: 'TechCorp'})")

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person) RETURN p.name AS person_name
            }
            CALL {
                MATCH (c:Company) RETURN c.name AS company_name
            }
            RETURN person_name, company_name
            """
        )

        # Cartesian product: 1 person x 1 company = 1 row
        assert len(results) == 1
        assert results[0]["person_name"].value == "Alice"
        assert results[0]["company_name"].value == "TechCorp"


class TestCallEdgeCases:
    """Edge case tests for CALL subqueries."""

    def test_call_empty_result(self):
        """CALL with no matching results."""
        gf = GraphForge()

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person)
                RETURN p.name AS name
            }
            RETURN name
            """
        )

        assert len(results) == 0

    def test_call_with_where(self):
        """CALL with WHERE clause inside."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {age: 25}), (:Person {age: 35})")

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person)
                WHERE p.age > 30
                RETURN count(*) AS cnt
            }
            RETURN cnt
            """
        )

        assert len(results) == 1
        assert results[0]["cnt"].value == 1

    def test_call_with_limit(self):
        """CALL with LIMIT inside."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'A'}), (:Person {name: 'B'}), (:Person {name: 'C'})")

        results = gf.execute(
            """
            CALL {
                MATCH (p:Person)
                RETURN p.name AS name
                ORDER BY name
                LIMIT 2
            }
            RETURN name
            ORDER BY name
            """
        )

        assert len(results) == 2
        assert results[0]["name"].value == "A"
        assert results[1]["name"].value == "B"

    def test_call_with_unwind(self):
        """CALL with UNWIND inside."""
        gf = GraphForge()

        results = gf.execute(
            """
            CALL {
                UNWIND [1, 2, 3] AS x
                RETURN x
            }
            RETURN x
            ORDER BY x
            """
        )

        assert len(results) == 3
        assert results[0]["x"].value == 1
        assert results[1]["x"].value == 2
        assert results[2]["x"].value == 3
