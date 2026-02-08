"""Integration tests for list comprehensions."""

from graphforge import GraphForge


class TestListComprehensionBasic:
    """Test basic list comprehension functionality."""

    def test_simple_list_iteration(self):
        """Test list comprehension with just iteration (no filter or map)."""
        gf = GraphForge()

        # [x IN [1,2,3]] should return [1,2,3]
        results = gf.execute("RETURN [x IN [1,2,3]] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 3
        assert [v.value for v in result_list.value] == [1, 2, 3]

    def test_list_with_filter(self):
        """Test list comprehension with WHERE filter."""
        gf = GraphForge()

        # [x IN [1,2,3,4,5] WHERE x > 3] should return [4,5]
        results = gf.execute("RETURN [x IN [1,2,3,4,5] WHERE x > 3] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 2
        assert [v.value for v in result_list.value] == [4, 5]

    def test_list_with_map(self):
        """Test list comprehension with map transformation."""
        gf = GraphForge()

        # [x IN [1,2,3] | x * 2] should return [2,4,6]
        results = gf.execute("RETURN [x IN [1,2,3] | x * 2] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 3
        assert [v.value for v in result_list.value] == [2, 4, 6]

    def test_list_with_filter_and_map(self):
        """Test list comprehension with both filter and map."""
        gf = GraphForge()

        # [x IN [1,2,3,4,5] WHERE x > 2 | x * 2] should return [6,8,10]
        results = gf.execute("RETURN [x IN [1,2,3,4,5] WHERE x > 2 | x * 2] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 3
        assert [v.value for v in result_list.value] == [6, 8, 10]


class TestListComprehensionWithData:
    """Test list comprehensions with graph data."""

    def test_filter_node_properties(self):
        """Test list comprehension filtering node properties."""
        gf = GraphForge()

        # Create nodes with ages
        gf.execute("CREATE (:Person {name: 'Alice', age: 25})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 30})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        # Get list of ages > 28
        results = gf.execute("""
            MATCH (p:Person)
            WITH collect(p.age) AS ages
            RETURN [age IN ages WHERE age > 28] AS filtered_ages
        """)

        assert len(results) == 1
        filtered = results[0]["filtered_ages"]
        assert len(filtered.value) == 2
        ages = sorted([v.value for v in filtered.value])
        assert ages == [30, 35]

    def test_transform_node_properties(self):
        """Test list comprehension transforming node properties."""
        gf = GraphForge()

        # Create nodes
        gf.execute("CREATE (:Person {name: 'Alice', salary: 50000})")
        gf.execute("CREATE (:Person {name: 'Bob', salary: 60000})")

        # Double all salaries
        results = gf.execute("""
            MATCH (p:Person)
            WITH collect(p.salary) AS salaries
            RETURN [s IN salaries | s * 2] AS doubled
        """)

        assert len(results) == 1
        doubled = results[0]["doubled"]
        assert len(doubled.value) == 2
        salaries = sorted([v.value for v in doubled.value])
        assert salaries == [100000, 120000]

    def test_complex_filter_and_transform(self):
        """Test complex list comprehension with filter and transform."""
        gf = GraphForge()

        # Create nodes
        gf.execute("CREATE (:Product {name: 'Widget', price: 10})")
        gf.execute("CREATE (:Product {name: 'Gadget', price: 25})")
        gf.execute("CREATE (:Product {name: 'Gizmo', price: 50})")

        # Get prices > 20, apply 10% discount
        results = gf.execute("""
            MATCH (p:Product)
            WITH collect(p.price) AS prices
            RETURN [price IN prices WHERE price > 20 | price * 0.9] AS discounted
        """)

        assert len(results) == 1
        discounted = results[0]["discounted"]
        assert len(discounted.value) == 2
        prices = sorted([v.value for v in discounted.value])
        assert prices == [22.5, 45.0]


class TestListComprehensionEdgeCases:
    """Test list comprehension edge cases."""

    def test_empty_list(self):
        """Test list comprehension on empty list."""
        gf = GraphForge()

        results = gf.execute("RETURN [x IN [] WHERE x > 5] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 0

    def test_all_filtered_out(self):
        """Test list comprehension where filter removes everything."""
        gf = GraphForge()

        results = gf.execute("RETURN [x IN [1,2,3] WHERE x > 10] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 0

    def test_nested_list_comprehension(self):
        """Test nested list comprehensions."""
        gf = GraphForge()

        # [[y IN [1,2]] for each x in [1,2]]
        results = gf.execute("RETURN [x IN [1,2] | [y IN [10,20] | x + y]] AS result")

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 2

        # First inner list: [1+10, 1+20] = [11, 21]
        inner1 = result_list.value[0]
        assert len(inner1.value) == 2
        assert [v.value for v in inner1.value] == [11, 21]

        # Second inner list: [2+10, 2+20] = [12, 22]
        inner2 = result_list.value[1]
        assert len(inner2.value) == 2
        assert [v.value for v in inner2.value] == [12, 22]

    def test_string_list_filter(self):
        """Test list comprehension with strings."""
        gf = GraphForge()

        results = gf.execute(
            "RETURN [name IN ['Alice', 'Bob', 'Charlie'] WHERE name STARTS WITH 'A'] AS result"
        )

        assert len(results) == 1
        result_list = results[0]["result"]
        assert len(result_list.value) == 1
        assert result_list.value[0].value == "Alice"

    def test_null_handling(self):
        """Test list comprehension with NULL values."""
        gf = GraphForge()

        # Create node with NULL property
        gf.execute("CREATE (:Person {name: 'Alice'})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 30})")

        # Filter should skip NULL (NULL > 20 is NULL, treated as false)
        results = gf.execute("""
            MATCH (p:Person)
            WITH collect(p.age) AS ages
            RETURN [age IN ages WHERE age > 20] AS filtered
        """)

        assert len(results) == 1
        filtered = results[0]["filtered"]
        # Only Bob's age (30) should pass
        assert len(filtered.value) == 1
        assert filtered.value[0].value == 30
