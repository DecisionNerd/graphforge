"""Tests for multi-hop CREATE patterns."""

from graphforge import GraphForge


class TestMultiHopCreate:
    """Test CREATE with multiple relationships in a single pattern."""

    def test_create_two_hop_pattern(self):
        """CREATE (a)-[r1]->(b)-[r2]->(c) should create all nodes and relationships."""
        gf = GraphForge()

        gf.execute(
            "CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})-[:KNOWS]->(c:Person {name: 'Charlie'})"
        )

        # Verify all three nodes exist
        nodes = gf.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY name")
        assert len(nodes) == 3
        assert nodes[0]["name"].value == "Alice"
        assert nodes[1]["name"].value == "Bob"
        assert nodes[2]["name"].value == "Charlie"

        # Verify both relationships exist
        result = gf.execute("""
            MATCH (a:Person)-[:KNOWS]->(b:Person)-[:KNOWS]->(c:Person)
            RETURN a.name AS a, b.name AS b, c.name AS c
        """)
        assert len(result) == 1
        assert result[0]["a"].value == "Alice"
        assert result[0]["b"].value == "Bob"
        assert result[0]["c"].value == "Charlie"

    def test_create_three_hop_pattern(self):
        """CREATE (a)-[r1]->(b)-[r2]->(c)-[r3]->(d) should work."""
        gf = GraphForge()

        gf.execute("""
            CREATE (a:Person {name: 'A'})-[:KNOWS]->(b:Person {name: 'B'})
                   -[:KNOWS]->(c:Person {name: 'C'})-[:KNOWS]->(d:Person {name: 'D'})
        """)

        # Verify all four nodes exist
        nodes = gf.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY name")
        assert len(nodes) == 4

        # Verify the chain exists
        result = gf.execute("""
            MATCH (a:Person)-[:KNOWS]->(b:Person)-[:KNOWS]->(c:Person)-[:KNOWS]->(d:Person)
            RETURN a.name AS a, b.name AS b, c.name AS c, d.name AS d
        """)
        assert len(result) == 1
        assert result[0]["a"].value == "A"
        assert result[0]["b"].value == "B"
        assert result[0]["c"].value == "C"
        assert result[0]["d"].value == "D"

    def test_create_multihop_with_different_types(self):
        """Multi-hop CREATE with different relationship types."""
        gf = GraphForge()

        gf.execute("""
            CREATE (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person {name: 'Bob'})
                   -[:WORKS_AT]->(c:Company {name: 'ACME'})
        """)

        # Verify nodes
        persons = gf.execute("MATCH (n:Person) RETURN n.name AS name ORDER BY name")
        assert len(persons) == 2

        companies = gf.execute("MATCH (n:Company) RETURN n.name AS name")
        assert len(companies) == 1
        assert companies[0]["name"].value == "ACME"

        # Verify relationships
        knows = gf.execute("MATCH ()-[r:KNOWS]->() RETURN r")
        assert len(knows) == 1

        works_at = gf.execute("MATCH ()-[r:WORKS_AT]->() RETURN r")
        assert len(works_at) == 1

    def test_create_multihop_with_bound_variables(self):
        """Multi-hop CREATE can bind variables to created elements."""
        gf = GraphForge()

        result = gf.execute("""
            CREATE (a:Person {name: 'Alice'})-[r1:KNOWS]->(b:Person {name: 'Bob'})
                   -[r2:KNOWS]->(c:Person {name: 'Charlie'})
            RETURN a.name AS a, b.name AS b, c.name AS c,
                   type(r1) AS rel1, type(r2) AS rel2
        """)

        assert len(result) == 1
        assert result[0]["a"].value == "Alice"
        assert result[0]["b"].value == "Bob"
        assert result[0]["c"].value == "Charlie"
        assert result[0]["rel1"].value == "KNOWS"
        assert result[0]["rel2"].value == "KNOWS"

    def test_create_multihop_with_properties_on_relationships(self):
        """Multi-hop CREATE with properties on each relationship."""
        gf = GraphForge()

        gf.execute("""
            CREATE (a:Person {name: 'Alice'})-[:KNOWS {since: 2020}]->(b:Person {name: 'Bob'})
                   -[:KNOWS {since: 2021}]->(c:Person {name: 'Charlie'})
        """)

        # Verify relationship properties
        result = gf.execute("""
            MATCH (a)-[r1:KNOWS]->(b)-[r2:KNOWS]->(c)
            RETURN r1.since AS since1, r2.since AS since2
        """)

        assert len(result) == 1
        assert result[0]["since1"].value == 2020
        assert result[0]["since2"].value == 2021

    def test_create_multihop_connecting_to_existing_node(self):
        """Multi-hop CREATE can connect to existing nodes."""
        gf = GraphForge()

        # Create existing node
        gf.execute("CREATE (:Person {name: 'Existing'})")

        # Create chain connecting to existing node
        gf.execute("""
            MATCH (e:Person {name: 'Existing'})
            CREATE (a:Person {name: 'New1'})-[:KNOWS]->(b:Person {name: 'New2'})-[:KNOWS]->(e)
        """)

        # Verify the chain
        result = gf.execute("""
            MATCH (a:Person {name: 'New1'})-[:KNOWS]->(b:Person {name: 'New2'})-[:KNOWS]->(c:Person {name: 'Existing'})
            RETURN a.name AS a, b.name AS b, c.name AS c
        """)

        assert len(result) == 1
        assert result[0]["a"].value == "New1"
        assert result[0]["b"].value == "New2"
        assert result[0]["c"].value == "Existing"

    def test_create_multihop_between_existing_nodes(self):
        """Multi-hop CREATE between existing start and end nodes."""
        gf = GraphForge()

        # Create two existing nodes
        gf.execute("CREATE (:Person {name: 'Start'})")
        gf.execute("CREATE (:Person {name: 'End'})")

        # Create chain between them
        gf.execute("""
            MATCH (start:Person {name: 'Start'}), (end:Person {name: 'End'})
            CREATE (start)-[:KNOWS]->(:Person {name: 'Middle'})-[:KNOWS]->(end)
        """)

        # Verify the chain
        result = gf.execute("""
            MATCH (s:Person {name: 'Start'})-[:KNOWS]->(m:Person)-[:KNOWS]->(e:Person {name: 'End'})
            RETURN s.name AS start, m.name AS middle, e.name AS end
        """)

        assert len(result) == 1
        assert result[0]["start"].value == "Start"
        assert result[0]["middle"].value == "Middle"
        assert result[0]["end"].value == "End"

    def test_create_multihop_with_no_properties(self):
        """Multi-hop CREATE with minimal patterns (no properties)."""
        gf = GraphForge()

        # Need to bind variables to make multi-hop work
        gf.execute("CREATE (a)-[:TYPE1]->(b)-[:TYPE2]->(c)-[:TYPE3]->(d)")

        # Verify chain exists
        result = gf.execute("""
            MATCH (a)-[r1:TYPE1]->(b)-[r2:TYPE2]->(c)-[r3:TYPE3]->(d)
            RETURN count(*) AS count
        """)

        assert result[0]["count"].value == 1

    def test_create_multihop_complex_pattern(self):
        """Complex multi-hop pattern with multiple node labels and properties."""
        gf = GraphForge()

        gf.execute("""
            CREATE (person:Person:User {name: 'Alice', age: 30})
                   -[:WORKS_AT {role: 'Engineer'}]->(company:Company {name: 'ACME'})
                   -[:LOCATED_IN]->(city:City {name: 'NYC'})
        """)

        # Verify all elements
        result = gf.execute("""
            MATCH (p:Person:User)-[w:WORKS_AT]->(c:Company)-[l:LOCATED_IN]->(city:City)
            RETURN p.name AS person, p.age AS age, w.role AS role,
                   c.name AS company, city.name AS cityName
        """)

        assert len(result) == 1
        assert result[0]["person"].value == "Alice"
        assert result[0]["age"].value == 30
        assert result[0]["role"].value == "Engineer"
        assert result[0]["company"].value == "ACME"
        assert result[0]["cityName"].value == "NYC"
