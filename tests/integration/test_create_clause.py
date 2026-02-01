"""Integration tests for CREATE clause.

Tests the ability to create nodes and relationships using Cypher CREATE syntax.
"""

from graphforge import GraphForge


class TestBasicCreate:
    """Tests for basic CREATE functionality."""

    def test_create_simple_node(self):
        """CREATE a simple node without properties."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person)")

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

    def test_create_node_with_properties(self):
        """CREATE a node with properties."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30})")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30

    def test_create_node_multiple_labels(self):
        """CREATE a node with multiple labels."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person:Employee)")

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

        results = gf.execute("MATCH (e:Employee) RETURN count(*) AS count")
        assert results[0]["count"].value == 1

    def test_create_multiple_nodes(self):
        """CREATE multiple nodes in one statement."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name ORDER BY name")
        assert len(results) == 2
        names = [r["name"].value for r in results]
        assert names == ["Alice", "Bob"]

    def test_create_with_return(self):
        """CREATE with RETURN clause."""
        gf = GraphForge()
        results = gf.execute(
            "CREATE (n:Person {name: 'Alice', age: 30}) RETURN n.name AS name, n.age AS age"
        )

        assert len(results) == 1
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30


class TestCreateRelationships:
    """Tests for creating relationships."""

    def test_create_simple_relationship(self):
        """CREATE a simple relationship."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})")

        results = gf.execute(
            "MATCH (a:Person)-[r:KNOWS]->(b:Person) RETURN a.name AS a_name, b.name AS b_name"
        )
        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"

    def test_create_relationship_with_properties(self):
        """CREATE a relationship with properties."""
        gf = GraphForge()
        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[r:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})"
        )

        results = gf.execute("""
            MATCH (a:Person)-[r:KNOWS]->(b:Person)
            RETURN a.name AS a_name, b.name AS b_name, r.since AS since
        """)
        assert len(results) == 1
        assert results[0]["a_name"].value == "Alice"
        assert results[0]["b_name"].value == "Bob"
        assert results[0]["since"].value == 2020

    def test_create_multiple_relationships(self):
        """CREATE multiple relationships."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r:KNOWS]->(c:Person {name: 'Charlie'})")

        results = gf.execute(
            "MATCH (a:Person {name: 'Alice'})-[r:KNOWS]->(b:Person) RETURN count(*) AS count"
        )
        assert results[0]["count"].value == 2

    def test_create_two_relationships_separately(self):
        """CREATE two relationships in separate statements."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice'}), (b:Person {name: 'Bob'})")
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r1:KNOWS]->(b:Person {name: 'Bob'})")
        gf.execute("CREATE (a:Person {name: 'Alice'})-[r2:LIKES]->(b:Person {name: 'Bob'})")

        results = gf.execute(
            "MATCH (a:Person {name: 'Alice'})-[r]->(b:Person) RETURN count(*) AS count"
        )
        assert results[0]["count"].value == 2


class TestCreatePropertyTypes:
    """Tests for different property types in CREATE."""

    def test_create_with_string_property(self):
        """CREATE with string property."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice'})")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert results[0]["name"].value == "Alice"

    def test_create_with_int_property(self):
        """CREATE with int property."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {age: 30})")

        results = gf.execute("MATCH (p:Person) RETURN p.age AS age")
        assert results[0]["age"].value == 30

    def test_create_with_bool_property(self):
        """CREATE with boolean property."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {active: true})")

        results = gf.execute("MATCH (p:Person) RETURN p.active AS active")
        assert results[0]["active"].value is True

    def test_create_with_null_property(self):
        """CREATE with null property."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {nickname: null})")

        results = gf.execute("MATCH (p:Person) RETURN p.nickname AS nickname")
        assert results[0]["nickname"].value is None

    def test_create_with_multiple_property_types(self):
        """CREATE with multiple property types."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30, active: true, nickname: null})")

        results = gf.execute(
            "MATCH (p:Person) RETURN p.name AS name, p.age AS age, p.active AS active, p.nickname AS nickname"
        )
        assert results[0]["name"].value == "Alice"
        assert results[0]["age"].value == 30
        assert results[0]["active"].value is True
        assert results[0]["nickname"].value is None


class TestCreateAndQuery:
    """Tests combining CREATE with other clauses."""

    def test_create_then_match(self):
        """CREATE then MATCH the created nodes."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (n:Person {name: 'Bob', age: 25})")

        results = gf.execute("MATCH (p:Person) WHERE p.age > 25 RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_create_with_return_and_alias(self):
        """CREATE with RETURN and alias."""
        gf = GraphForge()
        results = gf.execute("CREATE (n:Person {name: 'Alice'}) RETURN n.name AS person_name")

        assert len(results) == 1
        assert results[0]["person_name"].value == "Alice"

    def test_create_multiple_then_aggregate(self):
        """CREATE multiple nodes then aggregate."""
        gf = GraphForge()
        gf.execute("CREATE (a:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (b:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (c:Person {name: 'Charlie', age: 35})")

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count, sum(p.age) AS total_age")
        assert results[0]["count"].value == 3
        assert results[0]["total_age"].value == 90


class TestCreatePersistence:
    """Tests for CREATE with persistence."""

    def test_create_persists_across_sessions(self):
        """Created nodes persist across sessions."""
        from pathlib import Path
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"

            # Session 1: CREATE
            gf1 = GraphForge(db_path)
            gf1.execute("CREATE (n:Person {name: 'Alice', age: 30})")
            gf1.close()

            # Session 2: Verify
            gf2 = GraphForge(db_path)
            results = gf2.execute("MATCH (p:Person) RETURN p.name AS name, p.age AS age")
            assert len(results) == 1
            assert results[0]["name"].value == "Alice"
            assert results[0]["age"].value == 30
            gf2.close()

    def test_create_with_transactions(self):
        """CREATE within transactions."""
        gf = GraphForge()

        gf.begin()
        gf.execute("CREATE (n:Person {name: 'Alice'})")
        gf.commit()

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_create_rollback(self):
        """CREATE can be rolled back."""
        gf = GraphForge()

        gf.execute("CREATE (n:Person {name: 'Alice'})")

        gf.begin()
        gf.execute("CREATE (n:Person {name: 'Bob'})")
        gf.rollback()

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"


class TestCreateEdgeCases:
    """Tests for edge cases and error handling."""

    def test_create_no_variable(self):
        """CREATE without binding to variable."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        results = gf.execute("MATCH (p:Person) RETURN p.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_create_no_labels(self):
        """CREATE without labels."""
        gf = GraphForge()
        gf.execute("CREATE (n {name: 'Alice'})")

        results = gf.execute("MATCH (n) RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_create_no_properties(self):
        """CREATE without properties."""
        gf = GraphForge()
        gf.execute("CREATE (n:Person)")

        results = gf.execute("MATCH (p:Person) RETURN count(*) AS count")
        assert results[0]["count"].value == 1
