"""Integration tests for CASE expressions (issue #22).

Tests for CASE conditional expressions per Cypher semantics.
"""

from graphforge import GraphForge


class TestBasicCase:
    """Tests for basic CASE functionality."""

    def test_case_simple_categorization(self):
        """CASE expression for basic categorization."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 15}),
                   (b:Person {name: 'Bob', age: 25}),
                   (c:Person {name: 'Charlie', age: 70})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE
                       WHEN p.age < 18 THEN 'minor'
                       WHEN p.age < 65 THEN 'adult'
                       ELSE 'senior'
                   END AS category
            ORDER BY p.name
        """)

        assert len(results) == 3
        assert results[0]["name"].value == "Alice"
        assert results[0]["category"].value == "minor"
        assert results[1]["name"].value == "Bob"
        assert results[1]["category"].value == "adult"
        assert results[2]["name"].value == "Charlie"
        assert results[2]["category"].value == "senior"

    def test_case_with_single_when(self):
        """CASE with single WHEN clause."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice', active: true})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE WHEN p.active THEN 'yes' ELSE 'no' END AS status
        """)

        assert len(results) == 1
        assert results[0]["status"].value == "yes"

    def test_case_returns_null_without_else(self):
        """CASE without ELSE returns NULL when no WHEN matches."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice', age: 25})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE
                WHEN p.age < 18 THEN 'minor'
                WHEN p.age >= 65 THEN 'senior'
            END AS category
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["category"], CypherNull)

    def test_case_with_numeric_results(self):
        """CASE returning numeric values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {name: 'High', level: 'high'}),
                   (b:Item {name: 'Medium', level: 'medium'}),
                   (c:Item {name: 'Low', level: 'low'})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.name AS name,
                   CASE
                       WHEN i.level = 'high' THEN 3
                       WHEN i.level = 'medium' THEN 2
                       ELSE 1
                   END AS priority
            ORDER BY priority DESC
        """)

        assert len(results) == 3
        assert results[0]["priority"].value == 3
        assert results[1]["priority"].value == 2
        assert results[2]["priority"].value == 1


class TestCaseNullHandling:
    """Tests for NULL handling in CASE expressions."""

    def test_case_with_null_condition(self):
        """NULL condition in WHEN is treated as false."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 25}),
                   (b:Person {name: 'Bob'})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE
                       WHEN p.age > 18 THEN 'adult'
                       ELSE 'unknown'
                   END AS status
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["status"].value == "adult"  # Alice
        assert results[1]["status"].value == "unknown"  # Bob (NULL age)

    def test_case_for_null_coalescing(self):
        """CASE for NULL handling/coalescing."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', email: 'alice@example.com', has_email: true}),
                   (b:Person {name: 'Bob', has_email: false})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE
                       WHEN p.has_email THEN p.email
                       ELSE 'no-email@example.com'
                   END AS contact
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["contact"].value == "alice@example.com"
        assert results[1]["contact"].value == "no-email@example.com"

    def test_case_can_return_null_explicitly(self):
        """CASE can explicitly return NULL."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice', status: 'inactive'})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE
                WHEN p.status = 'active' THEN p.name
                ELSE NULL
            END AS active_name
        """)

        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["active_name"], CypherNull)


class TestCaseInDifferentContexts:
    """Tests for CASE in different query contexts."""

    def test_case_in_where_clause(self):
        """CASE expression in WHERE clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 25, vip: true}),
                   (b:Person {name: 'Bob', age: 15, vip: false}),
                   (c:Person {name: 'Charlie', age: 30, vip: false})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            WHERE CASE
                WHEN p.vip THEN p.age >= 18
                ELSE p.age >= 21
            END
            RETURN p.name AS name
            ORDER BY p.name
        """)

        # Alice: VIP and >= 18 → included
        # Bob: not VIP and < 21 → excluded
        # Charlie: not VIP and >= 21 → included
        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[1]["name"].value == "Charlie"

    def test_case_in_set_clause(self):
        """CASE expression in SET clause."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice', points: 150})")

        gf.execute("""
            MATCH (p:Person)
            SET p.level = CASE
                WHEN p.points >= 100 THEN 'gold'
                WHEN p.points >= 50 THEN 'silver'
                ELSE 'bronze'
            END
        """)

        results = gf.execute("MATCH (p:Person) RETURN p.level AS level")
        assert results[0]["level"].value == "gold"

    def test_case_with_aggregation(self):
        """CASE combined with aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 15}),
                   (b:Person {name: 'Bob', age: 25}),
                   (c:Person {name: 'Charlie', age: 70}),
                   (d:Person {name: 'David', age: 30})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE
                WHEN p.age < 18 THEN 'minor'
                WHEN p.age < 65 THEN 'adult'
                ELSE 'senior'
            END AS category,
            COUNT(*) AS count
        """)

        # Find the counts
        category_counts = {row["category"].value: row["count"].value for row in results}
        assert category_counts["minor"] == 1
        assert category_counts["adult"] == 2
        assert category_counts["senior"] == 1

    def test_case_in_order_by(self):
        """CASE expression in ORDER BY clause."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {name: 'High Priority', priority: 'high'}),
                   (b:Item {name: 'Low Priority', priority: 'low'}),
                   (c:Item {name: 'Medium Priority', priority: 'medium'})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.name AS name
            ORDER BY CASE
                WHEN i.priority = 'high' THEN 1
                WHEN i.priority = 'medium' THEN 2
                ELSE 3
            END
        """)

        assert len(results) == 3
        assert results[0]["name"].value == "High Priority"
        assert results[1]["name"].value == "Medium Priority"
        assert results[2]["name"].value == "Low Priority"


class TestCaseComplexConditions:
    """Tests for CASE with complex conditions."""

    def test_case_with_and_condition(self):
        """CASE with AND in condition."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 25, citizen: true}),
                   (b:Person {name: 'Bob', age: 15, citizen: true}),
                   (c:Person {name: 'Charlie', age: 25, citizen: false})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE
                       WHEN p.age >= 18 AND p.citizen THEN 'can vote'
                       ELSE 'cannot vote'
                   END AS voting_status
            ORDER BY p.name
        """)

        assert len(results) == 3
        assert results[0]["voting_status"].value == "can vote"  # Alice
        assert results[1]["voting_status"].value == "cannot vote"  # Bob
        assert results[2]["voting_status"].value == "cannot vote"  # Charlie

    def test_case_with_or_condition(self):
        """CASE with OR in condition."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', admin: true, moderator: false}),
                   (b:Person {name: 'Bob', admin: false, moderator: true}),
                   (c:Person {name: 'Charlie', admin: false, moderator: false})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE
                       WHEN p.admin OR p.moderator THEN 'elevated'
                       ELSE 'normal'
                   END AS access_level
            ORDER BY p.name
        """)

        assert len(results) == 3
        assert results[0]["access_level"].value == "elevated"  # Alice
        assert results[1]["access_level"].value == "elevated"  # Bob
        assert results[2]["access_level"].value == "normal"  # Charlie

    def test_case_with_comparison_operators(self):
        """CASE with various comparison operators."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Item {name: 'A', value: 10}),
                   (b:Item {name: 'B', value: 20}),
                   (c:Item {name: 'C', value: 30})
        """)

        results = gf.execute("""
            MATCH (i:Item)
            RETURN i.name AS name,
                   CASE
                       WHEN i.value < 15 THEN 'low'
                       WHEN i.value <= 25 THEN 'medium'
                       WHEN i.value > 25 THEN 'high'
                   END AS range
            ORDER BY i.name
        """)

        assert len(results) == 3
        assert results[0]["range"].value == "low"
        assert results[1]["range"].value == "medium"
        assert results[2]["range"].value == "high"


class TestCaseEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_nested_case_expression(self):
        """Nested CASE expressions."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 15, student: true}),
                   (b:Person {name: 'Bob', age: 25, employed: true})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN p.name AS name,
                   CASE
                       WHEN p.age < 18 THEN
                           CASE
                               WHEN p.student THEN 'student minor'
                               ELSE 'minor'
                           END
                       ELSE
                           CASE
                               WHEN p.employed THEN 'working adult'
                               ELSE 'adult'
                           END
                   END AS status
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["status"].value == "student minor"
        assert results[1]["status"].value == "working adult"

    def test_case_short_circuit_evaluation(self):
        """CASE stops at first matching WHEN."""
        gf = GraphForge()
        gf.execute("CREATE (p:Person {name: 'Alice', value: 15})")

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE
                WHEN p.value > 10 THEN 'first'
                WHEN p.value > 5 THEN 'second'
                WHEN p.value > 0 THEN 'third'
            END AS result
        """)

        # Should return 'first', not 'second' or 'third'
        assert results[0]["result"].value == "first"

    def test_case_with_string_concatenation(self):
        """CASE with string operations in results."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', title: 'Dr', has_title: true}),
                   (b:Person {name: 'Bob', has_title: false})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE
                WHEN p.has_title THEN p.title + ' ' + p.name
                ELSE p.name
            END AS full_name
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["full_name"].value == "Dr Alice"
        assert results[1]["full_name"].value == "Bob"

    def test_case_with_arithmetic_in_results(self):
        """CASE with arithmetic expressions in results."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Product {name: 'A', price: 100, discount: true}),
                   (b:Product {name: 'B', price: 100, discount: false})
        """)

        results = gf.execute("""
            MATCH (p:Product)
            RETURN p.name AS name,
                   CASE
                       WHEN p.discount THEN p.price * 0.8
                       ELSE p.price
                   END AS final_price
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["final_price"].value == 80.0  # 20% discount
        assert results[1]["final_price"].value == 100

    def test_case_with_property_in_result(self):
        """CASE returning property values."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', nickname: 'Ally', formal: false}),
                   (b:Person {name: 'Bob', nickname: 'Bobby', formal: true})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN CASE
                WHEN p.formal THEN p.name
                ELSE p.nickname
            END AS display_name
            ORDER BY p.name
        """)

        assert len(results) == 2
        assert results[0]["display_name"].value == "Ally"  # Alice, not formal
        assert results[1]["display_name"].value == "Bob"  # Bob, formal

    def test_case_in_collect_aggregation(self):
        """CASE expression inside COLLECT aggregation."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 15}),
                   (b:Person {name: 'Bob', age: 25}),
                   (c:Person {name: 'Charlie', age: 70})
        """)

        results = gf.execute("""
            MATCH (p:Person)
            RETURN COLLECT(
                CASE
                    WHEN p.age < 18 THEN 'M'
                    WHEN p.age < 65 THEN 'A'
                    ELSE 'S'
                END
            ) AS categories
        """)

        assert len(results) == 1
        categories = [v.value for v in results[0]["categories"].value]
        assert sorted(categories) == ["A", "M", "S"]
