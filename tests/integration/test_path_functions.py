"""Integration tests for path functions."""

from graphforge import GraphForge


class TestPathFunctionLength:
    """Test length() function in queries."""

    def test_length_single_hop(self):
        """Test length() with single-hop path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a:Person)-[:KNOWS]->(b:Person)
            RETURN length(p) AS pathLength
            """
        )

        assert len(results) == 1
        assert results[0]["pathLength"].value == 1

    def test_length_multi_hop(self):
        """Test length() with multi-hop path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")
        d = gf.create_node(["Person"], name="D")

        gf.create_relationship(a, b, "R1")
        gf.create_relationship(b, c, "R2")
        gf.create_relationship(c, d, "R3")

        results = gf.execute(
            """
            MATCH p = (a)-[:R1]->(b)-[:R2]->(c)-[:R3]->(d)
            RETURN length(p) AS pathLength
            """
        )

        assert len(results) == 1
        assert results[0]["pathLength"].value == 3

    def test_length_variable_length(self):
        """Test length() with variable-length path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN x.name AS name, length(p) AS pathLength
            ORDER BY pathLength
            """
        )

        assert len(results) == 2
        # 1-hop: A -> B
        assert results[0]["name"].value == "B"
        assert results[0]["pathLength"].value == 1
        # 2-hop: A -> B -> C
        assert results[1]["name"].value == "C"
        assert results[1]["pathLength"].value == 2

    def test_length_single_node(self):
        """Test length() with single-node path."""
        gf = GraphForge()

        gf.create_node(["Person"], name="Alice")

        results = gf.execute(
            """
            MATCH p = (a:Person)
            RETURN length(p) AS pathLength
            """
        )

        assert len(results) == 1
        assert results[0]["pathLength"].value == 0

    def test_length_in_where_clause(self):
        """Test length() in WHERE clause."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            WHERE length(p) = 2
            RETURN x.name AS name
            """
        )

        assert len(results) == 1
        assert results[0]["name"].value == "C"


class TestPathFunctionNodes:
    """Test nodes() function in queries."""

    def test_nodes_single_hop(self):
        """Test nodes() with single-hop path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person)
            RETURN nodes(p) AS pathNodes
            """
        )

        assert len(results) == 1
        nodes = results[0]["pathNodes"].value
        assert len(nodes) == 2
        assert nodes[0].id == a.id
        assert nodes[1].id == b.id

    def test_nodes_multi_hop(self):
        """Test nodes() with multi-hop path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "R1")
        gf.create_relationship(b, c, "R2")

        results = gf.execute(
            """
            MATCH p = (a)-[:R1]->(b)-[:R2]->(c)
            RETURN nodes(p) AS pathNodes
            """
        )

        assert len(results) == 1
        nodes = results[0]["pathNodes"].value
        assert len(nodes) == 3
        assert nodes[0].id == a.id
        assert nodes[1].id == b.id
        assert nodes[2].id == c.id

    def test_nodes_single_node(self):
        """Test nodes() with single-node path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")

        results = gf.execute(
            """
            MATCH p = (a:Person {name: 'Alice'})
            RETURN nodes(p) AS pathNodes
            """
        )

        assert len(results) == 1
        nodes = results[0]["pathNodes"].value
        assert len(nodes) == 1
        assert nodes[0].id == a.id

    def test_nodes_with_size(self):
        """Test size(nodes(p)) to count nodes."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN length(p) AS pathLength, size(nodes(p)) AS nodeCount
            ORDER BY pathLength
            """
        )

        assert len(results) == 2
        # 1-hop: 2 nodes
        assert results[0]["pathLength"].value == 1
        assert results[0]["nodeCount"].value == 2
        # 2-hop: 3 nodes
        assert results[1]["pathLength"].value == 2
        assert results[1]["nodeCount"].value == 3


class TestPathFunctionRelationships:
    """Test relationships() function in queries."""

    def test_relationships_single_hop(self):
        """Test relationships() with single-hop path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        r = gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person)
            RETURN relationships(p) AS pathRels
            """
        )

        assert len(results) == 1
        rels = results[0]["pathRels"].value
        assert len(rels) == 1
        assert rels[0].id == r.id
        assert rels[0].type == "KNOWS"

    def test_relationships_multi_hop(self):
        """Test relationships() with multi-hop path."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        r1 = gf.create_relationship(a, b, "R1")
        r2 = gf.create_relationship(b, c, "R2")

        results = gf.execute(
            """
            MATCH p = (a)-[:R1]->(b)-[:R2]->(c)
            RETURN relationships(p) AS pathRels
            """
        )

        assert len(results) == 1
        rels = results[0]["pathRels"].value
        assert len(rels) == 2
        assert rels[0].id == r1.id
        assert rels[0].type == "R1"
        assert rels[1].id == r2.id
        assert rels[1].type == "R2"

    def test_relationships_single_node(self):
        """Test relationships() with single-node path (no relationships)."""
        gf = GraphForge()

        gf.create_node(["Person"], name="Alice")

        results = gf.execute(
            """
            MATCH p = (a:Person {name: 'Alice'})
            RETURN relationships(p) AS pathRels
            """
        )

        assert len(results) == 1
        rels = results[0]["pathRels"].value
        assert len(rels) == 0

    def test_relationships_with_size(self):
        """Test size(relationships(p)) equals length(p)."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN length(p) AS pathLength, size(relationships(p)) AS relCount
            ORDER BY pathLength
            """
        )

        assert len(results) == 2
        # 1-hop: length=1, relCount=1
        assert results[0]["pathLength"].value == 1
        assert results[0]["relCount"].value == 1
        # 2-hop: length=2, relCount=2
        assert results[1]["pathLength"].value == 2
        assert results[1]["relCount"].value == 2


class TestPathFunctionsCombined:
    """Test combinations of path functions."""

    def test_all_path_functions(self):
        """Test length(), nodes(), and relationships() together."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="Alice")
        b = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(a, b, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a:Person {name: 'Alice'})-[:KNOWS]->(b:Person)
            RETURN
                length(p) AS pathLength,
                size(nodes(p)) AS nodeCount,
                size(relationships(p)) AS relCount
            """
        )

        assert len(results) == 1
        assert results[0]["pathLength"].value == 1
        assert results[0]["nodeCount"].value == 2
        assert results[0]["relCount"].value == 1

    def test_path_functions_with_aggregation(self):
        """Test path functions with aggregation."""
        gf = GraphForge()

        a = gf.create_node(["Person"], name="A")
        b = gf.create_node(["Person"], name="B")
        c = gf.create_node(["Person"], name="C")

        gf.create_relationship(a, b, "KNOWS")
        gf.create_relationship(b, c, "KNOWS")

        results = gf.execute(
            """
            MATCH p = (a {name: 'A'})-[:KNOWS*1..2]->(x)
            RETURN
                count(p) AS pathCount,
                avg(length(p)) AS avgLength,
                max(length(p)) AS maxLength,
                min(length(p)) AS minLength
            """
        )

        assert len(results) == 1
        assert results[0]["pathCount"].value == 2
        assert results[0]["avgLength"].value == 1.5  # (1+2)/2
        assert results[0]["maxLength"].value == 2
        assert results[0]["minLength"].value == 1
