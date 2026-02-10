"""Integration tests for new string functions (v0.4.0)."""

from graphforge.api import GraphForge


class TestStringFunctionsIntegration:
    """Integration tests for split, replace, left, right, ltrim, rtrim functions."""

    def test_split_in_query(self):
        """Test split() in a Cypher query."""
        gf = GraphForge()
        results = gf.execute("RETURN split('a,b,c', ',') AS parts")
        assert len(results) == 1
        parts = [p.value for p in results[0]["parts"].value]
        assert parts == ["a", "b", "c"]

    def test_replace_in_query(self):
        """Test replace() in a Cypher query."""
        gf = GraphForge()
        results = gf.execute("RETURN replace('hello world', 'world', 'GraphForge') AS text")
        assert len(results) == 1
        assert results[0]["text"].value == "hello GraphForge"

    def test_left_in_query(self):
        """Test left() in a Cypher query."""
        gf = GraphForge()
        results = gf.execute("RETURN left('hello', 3) AS left_part")
        assert len(results) == 1
        assert results[0]["left_part"].value == "hel"

    def test_right_in_query(self):
        """Test right() in a Cypher query."""
        gf = GraphForge()
        results = gf.execute("RETURN right('hello', 2) AS right_part")
        assert len(results) == 1
        assert results[0]["right_part"].value == "lo"

    def test_ltrim_in_query(self):
        """Test ltrim() in a Cypher query."""
        gf = GraphForge()
        results = gf.execute("RETURN ltrim('  hello  ') AS trimmed")
        assert len(results) == 1
        assert results[0]["trimmed"].value == "hello  "

    def test_rtrim_in_query(self):
        """Test rtrim() in a Cypher query."""
        gf = GraphForge()
        results = gf.execute("RETURN rtrim('  hello  ') AS trimmed")
        assert len(results) == 1
        assert results[0]["trimmed"].value == "  hello"

    def test_split_with_node_properties(self):
        """Test split() on node properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Data {tags: 'tag1,tag2,tag3'})")
        results = gf.execute(
            """
            MATCH (d:Data)
            RETURN split(d.tags, ',') AS tag_list
            """
        )
        assert len(results) == 1
        tags = [t.value for t in results[0]["tag_list"].value]
        assert tags == ["tag1", "tag2", "tag3"]

    def test_replace_with_node_properties(self):
        """Test replace() on node properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'John Doe'})")
        results = gf.execute(
            """
            MATCH (p:Person)
            RETURN replace(p.name, 'Doe', 'Smith') AS new_name
            """
        )
        assert len(results) == 1
        assert results[0]["new_name"].value == "John Smith"

    def test_combined_string_functions(self):
        """Test combining multiple string functions."""
        gf = GraphForge()
        results = gf.execute(
            """
            RETURN
                left(rtrim('  hello  '), 3) AS result1,
                replace(ltrim('  hello world  '), ' ', '_') AS result2
            """
        )
        assert len(results) == 1
        assert results[0]["result1"].value == "  h"
        assert results[0]["result2"].value == "hello_world__"

    def test_split_in_where_clause(self):
        """Test split() in WHERE clause."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: 'a,b,c'})")
        gf.execute("CREATE (:Item {tags: 'x,y'})")
        results = gf.execute(
            """
            MATCH (i:Item)
            WHERE size(split(i.tags, ',')) > 2
            RETURN i.tags AS tags
            """
        )
        assert len(results) == 1
        assert results[0]["tags"].value == "a,b,c"

    def test_string_functions_with_null(self):
        """Test string functions with NULL values."""
        gf = GraphForge()
        results = gf.execute(
            """
            RETURN
                split(null, ',') AS s1,
                replace(null, 'a', 'b') AS s2,
                left(null, 3) AS s3,
                right(null, 2) AS s4,
                ltrim(null) AS s5,
                rtrim(null) AS s6
            """
        )
        assert len(results) == 1
        assert results[0]["s1"].value is None
        assert results[0]["s2"].value is None
        assert results[0]["s3"].value is None
        assert results[0]["s4"].value is None
        assert results[0]["s5"].value is None
        assert results[0]["s6"].value is None
