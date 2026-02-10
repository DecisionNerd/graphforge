"""Integration tests for list/path function overloading."""

import pytest

from graphforge.api import GraphForge


class TestHeadLastPathOverloading:
    """Tests for head() and last() with lists and paths."""

    def test_head_on_list_of_nodes(self):
        """Test head() returns first element of node list."""
        gf = GraphForge()
        gf.execute("CREATE (:A {id: 1})")
        gf.execute("CREATE (:B {id: 2})")

        results = gf.execute(
            """
            MATCH (n)
            WITH n
            ORDER BY n.id
            WITH collect(n) AS nodes
            RETURN size(nodes) AS count, head(nodes) AS first
            """
        )
        assert len(results) == 1
        assert results[0]["count"].value == 2
        # Verify head() returns the first node (id=1)
        assert results[0]["first"].properties["id"].value == 1

    def test_last_on_list_of_nodes(self):
        """Test last() returns last element of node list."""
        gf = GraphForge()
        gf.execute("CREATE (:A {id: 1})")
        gf.execute("CREATE (:B {id: 2})")

        results = gf.execute(
            """
            MATCH (n)
            WITH n
            ORDER BY n.id
            WITH collect(n) AS nodes
            RETURN size(nodes) AS count, last(nodes) AS last_node
            """
        )
        assert len(results) == 1
        assert results[0]["count"].value == 2
        # Verify last() returns the last node (id=2)
        assert results[0]["last_node"].properties["id"].value == 2


class TestReverseOverloading:
    """Tests for reverse() with strings and lists."""

    def test_reverse_string_in_query(self):
        """Test reverse() on string properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")

        results = gf.execute(
            """
            MATCH (p:Person)
            RETURN reverse(p.name) AS reversed
            """
        )
        assert len(results) == 1
        assert results[0]["reversed"].value == "ecilA"

    def test_reverse_list_in_query(self):
        """Test reverse() on list properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Data {values: [1, 2, 3, 4, 5]})")

        results = gf.execute(
            """
            MATCH (d:Data)
            RETURN reverse(d.values) AS reversed
            """
        )
        assert len(results) == 1
        assert [x.value for x in results[0]["reversed"].value] == [5, 4, 3, 2, 1]

    def test_reverse_mixed_usage(self):
        """Test reverse() with both strings and lists in same query."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {name: 'abc', nums: [1, 2, 3]})")

        results = gf.execute(
            """
            MATCH (i:Item)
            RETURN reverse(i.name) AS rev_name,
                   reverse(i.nums) AS rev_nums
            """
        )
        assert len(results) == 1
        assert results[0]["rev_name"].value == "cba"
        assert [x.value for x in results[0]["rev_nums"].value] == [3, 2, 1]


class TestFunctionOverloadingErrors:
    """Tests for error handling in overloaded functions."""

    def test_head_with_invalid_type_in_query(self):
        """Test head() with invalid type raises error."""
        gf = GraphForge()
        gf.execute("CREATE (:Node {value: 42})")

        with pytest.raises(TypeError, match="HEAD expects list or path argument"):
            gf.execute(
                """
                MATCH (n:Node)
                RETURN head(n.value) AS result
                """
            )

    def test_last_with_invalid_type_in_query(self):
        """Test last() with invalid type raises error."""
        gf = GraphForge()
        gf.execute("CREATE (:Node {value: 'string'})")

        with pytest.raises(TypeError, match="LAST expects list or path argument"):
            gf.execute(
                """
                MATCH (n:Node)
                RETURN last(n.value) AS result
                """
            )

    def test_reverse_with_invalid_type_in_query(self):
        """Test reverse() with invalid type raises error."""
        gf = GraphForge()
        gf.execute("CREATE (:Node {value: 123})")

        with pytest.raises(TypeError, match="REVERSE expects list or string argument"):
            gf.execute(
                """
                MATCH (n:Node)
                RETURN reverse(n.value) AS result
                """
            )


class TestSizeFunctionOverloading:
    """Tests for size() with both lists and strings."""

    def test_size_on_string_property(self):
        """Test size() on string property."""
        gf = GraphForge()
        gf.execute("CREATE (:Text {content: 'hello world'})")

        results = gf.execute(
            """
            MATCH (t:Text)
            RETURN size(t.content) AS length
            """
        )
        assert len(results) == 1
        assert results[0]["length"].value == 11

    def test_size_on_list_property(self):
        """Test size() on list property."""
        gf = GraphForge()
        gf.execute("CREATE (:Container {items: [1, 2, 3, 4, 5]})")

        results = gf.execute(
            """
            MATCH (c:Container)
            RETURN size(c.items) AS count
            """
        )
        assert len(results) == 1
        assert results[0]["count"].value == 5

    def test_size_distinguishes_types(self):
        """Test size() works correctly on both string and list."""
        gf = GraphForge()
        gf.execute("CREATE (:Data {text: 'abc', list: [1, 2, 3, 4]})")

        results = gf.execute(
            """
            MATCH (d:Data)
            RETURN size(d.text) AS text_size,
                   size(d.list) AS list_size
            """
        )
        assert len(results) == 1
        assert results[0]["text_size"].value == 3
        assert results[0]["list_size"].value == 4


class TestComplexOverloadingScenarios:
    """Tests for complex scenarios involving overloaded functions."""

    def test_nested_overloaded_functions(self):
        """Test nesting overloaded functions."""
        gf = GraphForge()
        gf.execute("CREATE (:Node {data: [[1, 2], [3, 4], [5, 6]]})")

        results = gf.execute(
            """
            MATCH (n:Node)
            RETURN head(reverse(n.data)) AS result
            """
        )
        assert len(results) == 1
        # reverse([[1,2],[3,4],[5,6]]) = [[5,6],[3,4],[1,2]]
        # head(...) = [5,6]
        assert [x.value for x in results[0]["result"].value] == [5, 6]

    def test_overloading_in_conditional(self):
        """Test overloaded functions in WHERE clause."""
        gf = GraphForge()
        gf.execute("CREATE (:A {list: [1, 2, 3]})")
        gf.execute("CREATE (:B {list: [4, 5]})")

        results = gf.execute(
            """
            MATCH (n)
            WHERE size(n.list) > 2
            RETURN n.list AS list
            """
        )
        assert len(results) == 1
        assert [x.value for x in results[0]["list"].value] == [1, 2, 3]

    def test_overloading_with_aggregation(self):
        """Test overloaded functions with aggregation."""
        gf = GraphForge()
        gf.execute("CREATE (:Item {tags: ['a', 'b', 'c']})")
        gf.execute("CREATE (:Item {tags: ['x', 'y']})")

        results = gf.execute(
            """
            MATCH (i:Item)
            RETURN sum(size(i.tags)) AS total_tags
            """
        )
        assert len(results) == 1
        assert results[0]["total_tags"].value == 5
