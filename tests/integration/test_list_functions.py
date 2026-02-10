"""Integration tests for list functions using full Cypher queries."""

from graphforge.api import GraphForge


class TestListFunctionsIntegration:
    """Integration tests for list functions in full query context."""

    def test_tail_in_return(self):
        """Test tail() function in RETURN clause."""
        gf = GraphForge()
        results = gf.execute("RETURN tail([1, 2, 3, 4]) AS result")
        assert len(results) == 1
        assert len(results[0]["result"].value) == 3
        assert [x.value for x in results[0]["result"].value] == [2, 3, 4]

    def test_head_in_return(self):
        """Test head() function in RETURN clause."""
        gf = GraphForge()
        results = gf.execute("RETURN head([1, 2, 3]) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 1

    def test_last_in_return(self):
        """Test last() function in RETURN clause."""
        gf = GraphForge()
        results = gf.execute("RETURN last([1, 2, 3]) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 3

    def test_reverse_list_in_return(self):
        """Test reverse() function with list in RETURN clause."""
        gf = GraphForge()
        results = gf.execute("RETURN reverse([1, 2, 3]) AS result")
        assert len(results) == 1
        assert [x.value for x in results[0]["result"].value] == [3, 2, 1]

    def test_reverse_string_in_return(self):
        """Test reverse() function with string in RETURN clause."""
        gf = GraphForge()
        results = gf.execute("RETURN reverse('hello') AS result")
        assert len(results) == 1
        assert results[0]["result"].value == "olleh"

    def test_range_basic(self):
        """Test range() function with default step."""
        gf = GraphForge()
        results = gf.execute("RETURN range(1, 5) AS result")
        assert len(results) == 1
        assert [x.value for x in results[0]["result"].value] == [1, 2, 3, 4, 5]

    def test_range_with_step(self):
        """Test range() function with custom step."""
        gf = GraphForge()
        results = gf.execute("RETURN range(0, 10, 2) AS result")
        assert len(results) == 1
        assert [x.value for x in results[0]["result"].value] == [0, 2, 4, 6, 8, 10]

    def test_range_negative_step(self):
        """Test range() function with negative step."""
        gf = GraphForge()
        results = gf.execute("RETURN range(5, 1, -1) AS result")
        assert len(results) == 1
        assert [x.value for x in results[0]["result"].value] == [5, 4, 3, 2, 1]

    def test_size_list(self):
        """Test size() function with list."""
        gf = GraphForge()
        results = gf.execute("RETURN size([1, 2, 3]) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 3

    def test_size_empty_list(self):
        """Test size() function with empty list."""
        gf = GraphForge()
        results = gf.execute("RETURN size([]) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 0


class TestListFunctionsWithGraphData:
    """Tests for list functions with actual graph data."""

    def test_collect_and_tail(self):
        """Test tail() on collected node properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        results = gf.execute(
            """
            MATCH (p:Person)
            WITH collect(p.age) AS ages
            RETURN tail(ages) AS tail_ages
            """
        )
        assert len(results) == 1
        assert len(results[0]["tail_ages"].value) == 2

    def test_range_for_loop_unwind(self):
        """Test range() with UNWIND to generate sequence."""
        gf = GraphForge()
        results = gf.execute(
            """
            UNWIND range(1, 3) AS num
            RETURN num
            """
        )
        assert len(results) == 3
        assert results[0]["num"].value == 1
        assert results[1]["num"].value == 2
        assert results[2]["num"].value == 3

    def test_head_of_labels(self):
        """Test head() on labels() result."""
        gf = GraphForge()
        gf.execute("CREATE (:Person:Employee {name: 'Alice'})")

        results = gf.execute(
            """
            MATCH (p:Person)
            RETURN head(labels(p)) AS first_label
            """
        )
        assert len(results) == 1
        # Labels are sorted, so either 'Employee' or 'Person' could be first
        assert results[0]["first_label"].value in ["Employee", "Person"]

    def test_reverse_collected_names(self):
        """Test reverse() on collected property values."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob'})")
        gf.execute("CREATE (:Person {name: 'Charlie'})")

        results = gf.execute(
            """
            MATCH (p:Person)
            WITH collect(p.name) AS names
            RETURN reverse(names) AS reversed_names
            """
        )
        assert len(results) == 1
        assert len(results[0]["reversed_names"].value) == 3


class TestListFunctionComposition:
    """Tests for composing multiple list functions."""

    def test_head_tail_range(self):
        """Test head(tail(range(1, 5)))."""
        gf = GraphForge()
        results = gf.execute("RETURN head(tail(range(1, 5))) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 2

    def test_size_reverse(self):
        """Test size(reverse([1, 2, 3]))."""
        gf = GraphForge()
        results = gf.execute("RETURN size(reverse([1, 2, 3])) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 3

    def test_last_range_with_step(self):
        """Test last(range(0, 10, 3))."""
        gf = GraphForge()
        results = gf.execute("RETURN last(range(0, 10, 3)) AS result")
        assert len(results) == 1
        assert results[0]["result"].value == 9

    def test_tail_reverse(self):
        """Test tail(reverse([1, 2, 3]))."""
        gf = GraphForge()
        results = gf.execute("RETURN tail(reverse([1, 2, 3])) AS result")
        assert len(results) == 1
        assert [x.value for x in results[0]["result"].value] == [2, 1]

    def test_nested_function_chain(self):
        """Test complex nested function chain."""
        gf = GraphForge()
        results = gf.execute(
            """
            RETURN size(tail(reverse(range(1, 5)))) AS result
            """
        )
        assert len(results) == 1
        # range(1, 5) = [1, 2, 3, 4, 5]
        # reverse = [5, 4, 3, 2, 1]
        # tail = [4, 3, 2, 1]
        # size = 4
        assert results[0]["result"].value == 4


class TestListFunctionsWithWhere:
    """Tests for list functions in WHERE clauses."""

    def test_filter_by_list_size(self):
        """Test filtering using size() in WHERE clause."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', hobbies: ['reading', 'coding']})")
        gf.execute("CREATE (:Person {name: 'Bob', hobbies: ['gaming']})")
        gf.execute("CREATE (:Person {name: 'Charlie', hobbies: ['reading', 'gaming', 'cooking']})")

        results = gf.execute(
            """
            MATCH (p:Person)
            WHERE size(p.hobbies) > 1
            RETURN p.name AS name, size(p.hobbies) AS hobby_count
            ORDER BY name
            """
        )
        assert len(results) == 2
        assert results[0]["name"].value == "Alice"
        assert results[0]["hobby_count"].value == 2
        assert results[1]["name"].value == "Charlie"
        assert results[1]["hobby_count"].value == 3

    def test_filter_by_head_value(self):
        """Test filtering using head() in WHERE clause."""
        gf = GraphForge()
        gf.execute("CREATE (:Seq {values: [1, 2, 3]})")
        gf.execute("CREATE (:Seq {values: [5, 6, 7]})")
        gf.execute("CREATE (:Seq {values: [1, 9, 10]})")

        results = gf.execute(
            """
            MATCH (s:Seq)
            WHERE head(s.values) = 1
            RETURN size(s.values) AS count
            """
        )
        assert len(results) == 2


class TestListFunctionsEdgeCases:
    """Tests for edge cases and error handling."""

    def test_tail_on_empty_list(self):
        """Test tail() on empty list returns empty list."""
        gf = GraphForge()
        results = gf.execute("RETURN tail([]) AS result")
        assert len(results) == 1
        assert len(results[0]["result"].value) == 0

    def test_head_on_empty_list(self):
        """Test head() on empty list returns NULL."""
        gf = GraphForge()
        results = gf.execute("RETURN head([]) AS result")
        assert len(results) == 1
        assert results[0]["result"].value is None

    def test_last_on_empty_list(self):
        """Test last() on empty list returns NULL."""
        gf = GraphForge()
        results = gf.execute("RETURN last([]) AS result")
        assert len(results) == 1
        assert results[0]["result"].value is None

    def test_range_backwards_empty(self):
        """Test range() with start > end and positive step returns empty list."""
        gf = GraphForge()
        results = gf.execute("RETURN range(5, 1) AS result")
        assert len(results) == 1
        assert len(results[0]["result"].value) == 0

    def test_null_propagation(self):
        """Test NULL propagation through list functions."""
        gf = GraphForge()
        results = gf.execute("RETURN tail(null) AS t, head(null) AS h, last(null) AS l")
        assert len(results) == 1
        assert results[0]["t"].value is None
        assert results[0]["h"].value is None
        assert results[0]["l"].value is None
