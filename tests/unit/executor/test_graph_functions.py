"""Unit tests for graph introspection functions (id, labels, type)."""

import pytest

from graphforge import GraphForge


class TestIdFunction:
    """Tests for id() function."""

    def test_id_function_node(self):
        """Test id() returns node's internal integer ID."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        results = gf.execute("MATCH (n:Person) RETURN id(n) AS node_id")
        assert len(results) == 1
        assert results[0]["node_id"].value == alice.id

    def test_id_function_relationship(self):
        """Test id() returns relationship's internal integer ID."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        knows = gf.create_relationship(alice, bob, "KNOWS")
        results = gf.execute("MATCH ()-[r:KNOWS]->() RETURN id(r) AS rel_id")
        assert len(results) == 1
        assert results[0]["rel_id"].value == knows.id

    def test_id_function_multiple_nodes(self):
        """Test id() works for multiple nodes with different IDs."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")

        results = gf.execute(
            "MATCH (n:Person) RETURN n.name AS name, id(n) AS node_id ORDER BY id(n)"
        )
        assert len(results) == 3
        # IDs should be unique
        ids = [r["node_id"].value for r in results]
        assert len(set(ids)) == 3
        # Check specific IDs match
        assert alice.id in ids
        assert bob.id in ids
        assert charlie.id in ids

    def test_id_function_null_argument(self):
        """Test id(null) returns null."""
        gf = GraphForge()
        results = gf.execute("RETURN id(null) AS result")
        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)

    def test_id_function_invalid_argument(self):
        """Test id() with non-node/relationship argument raises error."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="ID expects node or relationship argument"):
            gf.execute("RETURN id('not a node')")

    def test_id_function_in_where_clause(self):
        """Test id() can be used in WHERE clause."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        gf.create_node(["Person"], name="Bob")  # Create Bob but don't need the reference

        results = gf.execute(f"MATCH (n:Person) WHERE id(n) = {alice.id} RETURN n.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Alice"

    def test_id_function_in_return_expression(self):
        """Test id() can be used in expressions."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        results = gf.execute("MATCH (n:Person) RETURN id(n) * 2 AS doubled_id")
        assert len(results) == 1
        assert results[0]["doubled_id"].value == alice.id * 2


class TestLabelsFunction:
    """Tests for labels() function."""

    def test_labels_function_single_label(self):
        """Test labels() returns single label as list."""
        gf = GraphForge()
        gf.create_node(["Person"], name="Alice")
        results = gf.execute("MATCH (n:Person) RETURN labels(n) AS labels")
        assert len(results) == 1
        labels_list = results[0]["labels"]
        # Should be CypherList of CypherString
        from graphforge.types.values import CypherList, CypherString

        assert isinstance(labels_list, CypherList)
        assert len(labels_list.value) == 1
        assert isinstance(labels_list.value[0], CypherString)
        assert labels_list.value[0].value == "Person"

    def test_labels_function_multiple_labels(self):
        """Test labels() returns multiple labels in sorted order."""
        gf = GraphForge()
        gf.create_node(["Person", "Customer", "VIP"], name="Alice")
        results = gf.execute("MATCH (n) RETURN labels(n) AS labels")
        assert len(results) == 1
        labels_list = results[0]["labels"].value
        # Extract string values
        label_strings = [label.value for label in labels_list]
        # Should be sorted alphabetically
        assert label_strings == ["Customer", "Person", "VIP"]

    def test_labels_function_no_labels(self):
        """Test labels() returns empty list for node with no labels."""
        gf = GraphForge()
        gf.create_node([], name="Unlabeled")
        results = gf.execute("MATCH (n) RETURN labels(n) AS labels")
        assert len(results) == 1
        labels_list = results[0]["labels"].value
        assert labels_list == []

    def test_labels_function_null_argument(self):
        """Test labels(null) returns null."""
        gf = GraphForge()
        results = gf.execute("RETURN labels(null) AS result")
        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)

    def test_labels_function_invalid_argument(self):
        """Test labels() with non-node argument raises error."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="LABELS expects node argument"):
            gf.execute("RETURN labels('not a node')")

    def test_labels_function_in_where_clause(self):
        """Test labels() can be used to filter nodes by checking if label exists.

        Note: IN operator with lists not yet supported in WHERE clause,
        so we test by checking labels list properties instead.
        """
        gf = GraphForge()
        gf.create_node(["Person", "Employee"], name="Alice")
        gf.create_node(["Person"], name="Bob")
        gf.create_node(["Customer"], name="Charlie")

        # Get all nodes and their labels
        results = gf.execute("MATCH (n) RETURN n.name AS name, labels(n) AS labels ORDER BY n.name")
        assert len(results) == 3

        # Check that Alice has Employee label
        alice = results[0]
        assert alice["name"].value == "Alice"
        alice_labels = [l.value for l in alice["labels"].value]
        assert "Employee" in alice_labels

    def test_labels_function_multiple_nodes(self):
        """Test labels() works for multiple nodes."""
        gf = GraphForge()
        gf.create_node(["Person"], name="Alice")
        gf.create_node(["Company"], name="Acme")
        gf.create_node(["Person", "Customer"], name="Bob")

        results = gf.execute("MATCH (n) RETURN n.name AS name, labels(n) AS labels ORDER BY n.name")
        assert len(results) == 3

        # Build a map of name -> labels for easier checking
        name_to_labels = {}
        for row in results:
            name = row["name"].value
            labels = [l.value for l in row["labels"].value]
            name_to_labels[name] = labels

        # Check Alice (Person)
        assert name_to_labels["Alice"] == ["Person"]

        # Check Acme (Company)
        assert name_to_labels["Acme"] == ["Company"]

        # Check Bob (Customer, Person - sorted)
        assert name_to_labels["Bob"] == ["Customer", "Person"]


class TestTypeFunction:
    """Tests for type() function."""

    def test_type_function_relationship(self):
        """Test type() returns relationship type string."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        gf.create_relationship(alice, bob, "KNOWS")

        results = gf.execute("MATCH ()-[r]->() RETURN type(r) AS rel_type")
        assert len(results) == 1
        assert results[0]["rel_type"].value == "KNOWS"

    def test_type_function_multiple_relationship_types(self):
        """Test type() works for multiple relationship types."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        company = gf.create_node(["Company"], name="Acme")

        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, company, "WORKS_FOR")
        gf.create_relationship(bob, company, "WORKS_FOR")

        results = gf.execute("MATCH ()-[r]->() RETURN type(r) AS rel_type ORDER BY type(r)")
        assert len(results) == 3
        types = [r["rel_type"].value for r in results]
        assert types == ["KNOWS", "WORKS_FOR", "WORKS_FOR"]

    def test_type_function_null_argument(self):
        """Test type(null) returns null."""
        gf = GraphForge()
        results = gf.execute("RETURN type(null) AS result")
        assert len(results) == 1
        from graphforge.types.values import CypherNull

        assert isinstance(results[0]["result"], CypherNull)

    def test_type_function_in_where_clause(self):
        """Test type() can be used in WHERE clause."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        charlie = gf.create_node(["Person"], name="Charlie")

        gf.create_relationship(alice, bob, "KNOWS")
        gf.create_relationship(alice, charlie, "FOLLOWS")

        results = gf.execute("MATCH (a)-[r]->(b) WHERE type(r) = 'KNOWS' RETURN b.name AS name")
        assert len(results) == 1
        assert results[0]["name"].value == "Bob"

    def test_type_function_value_introspection(self):
        """Test type() also works for value type introspection."""
        gf = GraphForge()
        results = gf.execute("RETURN type('hello') AS string_type, type(123) AS int_type")
        assert len(results) == 1
        assert results[0]["string_type"].value == "String"
        assert results[0]["int_type"].value == "Int"


class TestCombinedGraphFunctions:
    """Tests for using multiple graph functions together."""

    def test_id_and_labels_together(self):
        """Test using id() and labels() in same query."""
        gf = GraphForge()
        alice = gf.create_node(["Person", "Customer"], name="Alice")
        results = gf.execute("MATCH (n:Person) RETURN id(n) AS nid, labels(n) AS labels")
        assert len(results) == 1
        assert results[0]["nid"].value == alice.id
        labels = [l.value for l in results[0]["labels"].value]
        assert labels == ["Customer", "Person"]

    def test_all_graph_functions(self):
        """Test using id(), labels(), and type() in one query."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        knows = gf.create_relationship(alice, bob, "KNOWS")

        results = gf.execute(
            """
            MATCH (a)-[r]->(b)
            RETURN id(a) AS src_id, labels(a) AS src_labels,
                   id(r) AS rel_id, type(r) AS rel_type,
                   id(b) AS dst_id, labels(b) AS dst_labels
            """
        )
        assert len(results) == 1
        assert results[0]["src_id"].value == alice.id
        assert results[0]["rel_id"].value == knows.id
        assert results[0]["rel_type"].value == "KNOWS"
        assert results[0]["dst_id"].value == bob.id

    def test_graph_functions_in_projection(self):
        """Test graph functions work in complex projections."""
        gf = GraphForge()
        alice = gf.create_node(["Person"], name="Alice")
        bob = gf.create_node(["Person"], name="Bob")
        acme = gf.create_node(["Company"], name="Acme")

        results = gf.execute(
            """
            MATCH (n)
            RETURN id(n) AS nid, labels(n) AS labels
            ORDER BY id(n)
            """
        )
        assert len(results) == 3

        # Build map of id -> labels
        id_to_labels = {}
        for row in results:
            nid = row["nid"].value
            labels = [l.value for l in row["labels"].value]
            id_to_labels[nid] = labels

        # Check that all nodes are present
        assert alice.id in id_to_labels
        assert bob.id in id_to_labels
        assert acme.id in id_to_labels

        # Check labels
        assert id_to_labels[alice.id] == ["Person"]
        assert id_to_labels[bob.id] == ["Person"]
        assert id_to_labels[acme.id] == ["Company"]
