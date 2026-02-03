"""Integration tests for REMOVE clause (issue #25).

Tests for removing properties and labels from nodes.
"""

from graphforge import GraphForge
from graphforge.types.values import CypherNull


class TestRemoveProperty:
    """Tests for removing properties."""

    def test_remove_single_property(self):
        """Remove a single property from a node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30, city: 'NYC'})")

        gf.execute("""
            MATCH (n:Person {name: 'Alice'})
            REMOVE n.age
        """)

        # Verify age property was removed
        results = gf.execute("""
            MATCH (n:Person {name: 'Alice'})
            RETURN n.name AS name, n.age AS age, n.city AS city
        """)
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert isinstance(results[0]["age"], CypherNull)
        assert results[0]["city"].value == "NYC"

    def test_remove_multiple_properties(self):
        """Remove multiple properties from a node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Bob', age: 25, city: 'LA', country: 'USA'})")

        gf.execute("""
            MATCH (n:Person {name: 'Bob'})
            REMOVE n.age, n.country
        """)

        # Verify both properties were removed
        results = gf.execute("""
            MATCH (n:Person {name: 'Bob'})
            RETURN n.name AS name, n.age AS age, n.city AS city, n.country AS country
        """)
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"
        assert isinstance(results[0]["age"], CypherNull)
        assert results[0]["city"].value == "LA"
        assert isinstance(results[0]["country"], CypherNull)

    def test_remove_nonexistent_property(self):
        """Remove a property that doesn't exist (should not error)."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Charlie'})")

        # This should not error
        gf.execute("""
            MATCH (n:Person {name: 'Charlie'})
            REMOVE n.age
        """)

        # Verify node is unchanged
        results = gf.execute("""
            MATCH (n:Person {name: 'Charlie'})
            RETURN n.name AS name, n.age AS age
        """)
        assert len(results) == 1
        assert results[0]["name"].value == "Charlie"
        assert isinstance(results[0]["age"], CypherNull)

    def test_remove_property_with_return(self):
        """REMOVE with RETURN clause."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Diana', age: 28, city: 'SF'})")

        results = gf.execute("""
            MATCH (n:Person {name: 'Diana'})
            REMOVE n.city
            RETURN n.name AS name, n.city AS city
        """)

        assert len(results) == 1
        assert results[0]["name"].value == "Diana"
        assert isinstance(results[0]["city"], CypherNull)

    def test_remove_property_from_multiple_nodes(self):
        """Remove property from multiple matched nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30, temp: 'x'}),
                   (b:Person {name: 'Bob', age: 25, temp: 'y'}),
                   (c:Person {name: 'Charlie', age: 35, temp: 'z'})
        """)

        gf.execute("""
            MATCH (n:Person)
            WHERE n.age > 24
            REMOVE n.temp
        """)

        # All three should have temp removed
        results = gf.execute("""
            MATCH (n:Person)
            RETURN n.name AS name, n.temp AS temp
            ORDER BY name
        """)
        assert len(results) == 3
        for r in results:
            assert isinstance(r["temp"], CypherNull)


class TestRemoveLabel:
    """Tests for removing labels."""

    def test_remove_single_label(self):
        """Remove a single label from a node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person:Employee {name: 'Eve'})")

        gf.execute("""
            MATCH (n {name: 'Eve'})
            REMOVE n:Employee
        """)

        # Verify Employee label was removed
        results = gf.execute("MATCH (n:Person {name: 'Eve'}) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Eve"

        # Verify node no longer has Employee label
        results = gf.execute("MATCH (n:Employee {name: 'Eve'}) RETURN n")
        assert len(results) == 0

    def test_remove_nonexistent_label(self):
        """Remove a label that doesn't exist (should not error)."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Frank'})")

        # This should not error
        gf.execute("""
            MATCH (n:Person {name: 'Frank'})
            REMOVE n:Admin
        """)

        # Verify node is unchanged
        results = gf.execute("MATCH (n:Person {name: 'Frank'}) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Frank"

    def test_remove_label_from_multiple_nodes(self):
        """Remove label from multiple matched nodes."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person:Temp {name: 'Alice'}),
                   (b:Person:Temp {name: 'Bob'}),
                   (c:Person:Temp {name: 'Charlie'})
        """)

        gf.execute("""
            MATCH (n:Temp)
            REMOVE n:Temp
        """)

        # All three should have Temp label removed
        results = gf.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert results[0]["count"].value == 3

        results = gf.execute("MATCH (n:Temp) RETURN count(n) AS count")
        assert results[0]["count"].value == 0


class TestRemoveMixed:
    """Tests for removing both properties and labels."""

    def test_remove_property_and_label(self):
        """Remove both property and label in single query."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person:Temp {name: 'Grace', age: 40})")

        gf.execute("""
            MATCH (n {name: 'Grace'})
            REMOVE n.age, n:Temp
        """)

        # Verify both were removed
        results = gf.execute("""
            MATCH (n:Person {name: 'Grace'})
            RETURN n.name AS name, n.age AS age
        """)
        assert len(results) == 1
        assert results[0]["name"].value == "Grace"
        assert isinstance(results[0]["age"], CypherNull)

        # Verify Temp label removed
        results = gf.execute("MATCH (n:Temp) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

    def test_remove_multiple_properties_and_labels(self):
        """Remove multiple properties and labels."""
        gf = GraphForge()
        gf.execute(
            "CREATE (n:Person:Employee:Manager {name: 'Henry', age: 45, dept: 'IT', level: 5})"
        )

        gf.execute("""
            MATCH (n {name: 'Henry'})
            REMOVE n.age, n.level, n:Employee, n:Manager
        """)

        # Verify properties removed
        results = gf.execute("""
            MATCH (n:Person {name: 'Henry'})
            RETURN n.name AS name, n.dept AS dept, n.age AS age, n.level AS level
        """)
        assert len(results) == 1
        assert results[0]["name"].value == "Henry"
        assert results[0]["dept"].value == "IT"
        assert isinstance(results[0]["age"], CypherNull)
        assert isinstance(results[0]["level"], CypherNull)

        # Verify labels removed
        assert len(gf.execute("MATCH (n:Employee) RETURN n")) == 0
        assert len(gf.execute("MATCH (n:Manager) RETURN n")) == 0
        assert len(gf.execute("MATCH (n:Person) RETURN n")) == 1


class TestRemoveWithOtherClauses:
    """Tests for REMOVE with other clauses."""

    def test_remove_with_where(self):
        """REMOVE with WHERE filter."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30, flag: true}),
                   (b:Person {name: 'Bob', age: 20, flag: true}),
                   (c:Person {name: 'Charlie', age: 40, flag: true})
        """)

        gf.execute("""
            MATCH (n:Person)
            WHERE n.age > 25
            REMOVE n.flag
        """)

        # Only Alice and Charlie should have flag removed
        results = gf.execute("""
            MATCH (n:Person)
            RETURN n.name AS name, n.flag AS flag
            ORDER BY name
        """)
        assert len(results) == 3
        assert isinstance(results[0]["flag"], CypherNull)  # Alice
        assert results[1]["flag"].value is True  # Bob
        assert isinstance(results[2]["flag"], CypherNull)  # Charlie

    def test_match_remove_set(self):
        """MATCH, REMOVE, then SET."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Iris', old_age: 50})")

        gf.execute("""
            MATCH (n:Person {name: 'Iris'})
            REMOVE n.old_age
            SET n.age = 51
        """)

        # Verify old_age removed and age set
        results = gf.execute("""
            MATCH (n:Person {name: 'Iris'})
            RETURN n.old_age AS old_age, n.age AS age
        """)
        assert len(results) == 1
        assert isinstance(results[0]["old_age"], CypherNull)
        assert results[0]["age"].value == 51

    def test_remove_with_return_and_order(self):
        """REMOVE with RETURN, ORDER BY, and LIMIT."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', score: 100}),
                   (b:Person {name: 'Bob', score: 200}),
                   (c:Person {name: 'Charlie', score: 150})
        """)

        results = gf.execute("""
            MATCH (n:Person)
            REMOVE n.score
            RETURN n.name AS name
            ORDER BY name DESC
            LIMIT 2
        """)

        assert len(results) == 2
        assert results[0]["name"].value == "Charlie"
        assert results[1]["name"].value == "Bob"

        # Verify all scores removed
        check = gf.execute("MATCH (n:Person) RETURN n.score AS score")
        for r in check:
            assert isinstance(r["score"], CypherNull)


class TestRemoveEdgeCases:
    """Edge case tests for REMOVE."""

    def test_remove_from_relationship(self):
        """Remove property from relationship."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Jack'})-[r:KNOWS {since: 2020, temp: 'x'}]->(b:Person {name: 'Jill'})
        """)

        gf.execute("""
            MATCH (a)-[r:KNOWS]->(b)
            REMOVE r.temp
        """)

        # Verify temp removed but since remains
        results = gf.execute("""
            MATCH (a)-[r:KNOWS]->(b)
            RETURN r.since AS since, r.temp AS temp
        """)
        assert len(results) == 1
        assert results[0]["since"].value == 2020
        assert isinstance(results[0]["temp"], CypherNull)

    def test_remove_all_properties(self):
        """Remove all properties from a node."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Kate', age: 30, city: 'NYC'})")

        gf.execute("""
            MATCH (n:Person)
            REMOVE n.name, n.age, n.city
        """)

        # Node should still exist but have no properties
        results = gf.execute("MATCH (n:Person) RETURN count(n) AS count")
        assert results[0]["count"].value == 1

        results = gf.execute("""
            MATCH (n:Person)
            RETURN n.name AS name, n.age AS age, n.city AS city
        """)
        assert len(results) == 1
        assert isinstance(results[0]["name"], CypherNull)
        assert isinstance(results[0]["age"], CypherNull)
        assert isinstance(results[0]["city"], CypherNull)

    def test_remove_with_no_matches(self):
        """REMOVE when MATCH finds no nodes."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Leo'})")

        # This should not error
        results = gf.execute("""
            MATCH (n:Person {name: 'NonExistent'})
            REMOVE n.age
            RETURN n
        """)

        assert len(results) == 0

    def test_remove_multiple_variables(self):
        """Remove properties from multiple different variables."""
        gf = GraphForge()
        gf.execute("""
            CREATE (a:Person {name: 'Alice', age: 30}),
                   (b:Person {name: 'Bob', age: 25})
        """)

        results = gf.execute("""
            MATCH (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})
            REMOVE a.age, b.age
            RETURN a.name AS name1, b.name AS name2, a.age AS age1, b.age AS age2
        """)

        assert len(results) == 1
        assert results[0]["name1"].value == "Alice"
        assert results[0]["name2"].value == "Bob"
        assert isinstance(results[0]["age1"], CypherNull)
        assert isinstance(results[0]["age2"], CypherNull)

    def test_remove_same_property_twice(self):
        """Remove same property twice in one query (idempotent)."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Mike', age: 40})")

        gf.execute("""
            MATCH (n:Person {name: 'Mike'})
            REMOVE n.age, n.age
        """)

        results = gf.execute("""
            MATCH (n:Person {name: 'Mike'})
            RETURN n.age AS age
        """)
        assert len(results) == 1
        assert isinstance(results[0]["age"], CypherNull)

    def test_remove_label_twice(self):
        """Remove same label twice in one query (idempotent)."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person:Temp {name: 'Nina'})")

        gf.execute("""
            MATCH (n {name: 'Nina'})
            REMOVE n:Temp, n:Temp
        """)

        # Should only have Person label
        results = gf.execute("MATCH (n:Person {name: 'Nina'}) RETURN n.name AS name")
        assert len(results) == 1

        results = gf.execute("MATCH (n:Temp) RETURN count(n) AS count")
        assert results[0]["count"].value == 0

    def test_remove_property_then_set_same_property(self):
        """Remove property, then SET it in next query."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Oscar', age: 50})")

        gf.execute("""
            MATCH (n:Person {name: 'Oscar'})
            REMOVE n.age
        """)

        gf.execute("""
            MATCH (n:Person {name: 'Oscar'})
            SET n.age = 51
        """)

        results = gf.execute("""
            MATCH (n:Person {name: 'Oscar'})
            RETURN n.age AS age
        """)
        assert results[0]["age"].value == 51

    def test_remove_on_node_without_property(self):
        """Remove property that was never set (not just removed)."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Paul'})")

        # Node was created without 'age' property
        gf.execute("""
            MATCH (n:Person {name: 'Paul'})
            REMOVE n.age
        """)

        # Should complete without error
        results = gf.execute("MATCH (n:Person {name: 'Paul'}) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Paul"
