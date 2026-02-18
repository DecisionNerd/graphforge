"""Integration tests for list operation functions (filter, extract, reduce)."""

import pytest

from graphforge import GraphForge
from graphforge.types.values import CypherList, CypherNull


class TestFilterExpression:
    """Test FILTER() expression."""

    def test_filter_basic_predicate(self):
        """Filter list with simple predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN [1,2,3,4,5] WHERE x > 3) AS filtered")
        filtered = result[0]["filtered"]
        assert isinstance(filtered, CypherList)
        assert [v.value for v in filtered.value] == [4, 5]

    def test_filter_comparison_operators(self):
        """Filter with various comparison operators."""
        gf = GraphForge()
        # Less than
        result = gf.execute("RETURN filter(x IN [1,2,3,4,5] WHERE x < 3) AS filtered")
        assert [v.value for v in result[0]["filtered"].value] == [1, 2]

        # Equal
        result = gf.execute("RETURN filter(x IN [1,2,3,4,5] WHERE x = 3) AS filtered")
        assert [v.value for v in result[0]["filtered"].value] == [3]

        # Not equal
        result = gf.execute("RETURN filter(x IN [1,2,3] WHERE x <> 2) AS filtered")
        assert [v.value for v in result[0]["filtered"].value] == [1, 3]

    def test_filter_all_excluded(self):
        """Filter where all items are excluded."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN [1,2,3] WHERE x > 10) AS filtered")
        filtered = result[0]["filtered"]
        assert isinstance(filtered, CypherList)
        assert len(filtered.value) == 0

    def test_filter_all_included(self):
        """Filter where all items pass predicate."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN [1,2,3] WHERE x > 0) AS filtered")
        assert [v.value for v in result[0]["filtered"].value] == [1, 2, 3]

    def test_filter_empty_list(self):
        """Filter empty list returns empty list."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN [] WHERE x > 3) AS filtered")
        filtered = result[0]["filtered"]
        assert isinstance(filtered, CypherList)
        assert len(filtered.value) == 0

    def test_filter_null_list(self):
        """Filter NULL list returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN null WHERE x > 3) AS filtered")
        assert isinstance(result[0]["filtered"], CypherNull)

    def test_filter_null_predicate(self):
        """Filter with NULL predicate excludes items (NULL treated as false)."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN [1,2,3] WHERE null) AS filtered")
        filtered = result[0]["filtered"]
        assert isinstance(filtered, CypherList)
        assert len(filtered.value) == 0

    def test_filter_strings(self):
        """Filter list of strings."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN filter(s IN ['apple', 'banana', 'cherry'] WHERE s = 'banana') AS filtered"
        )
        filtered = result[0]["filtered"]
        assert len(filtered.value) == 1
        assert filtered.value[0].value == "banana"

    def test_filter_with_node_properties(self):
        """Filter nodes by property values."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")
        gf.execute("CREATE (:Person {name: 'Charlie', age: 35})")

        result = gf.execute(
            """
            MATCH (p:Person)
            WITH collect(p) AS people
            RETURN filter(person IN people WHERE person.age >= 30) AS adults
            """
        )

        adults = result[0]["adults"]
        assert isinstance(adults, CypherList)
        assert len(adults.value) == 2
        ages = sorted([person.properties["age"].value for person in adults.value])
        assert ages == [30, 35]


class TestExtractExpression:
    """Test EXTRACT() expression."""

    def test_extract_basic_transformation(self):
        """Extract with simple transformation."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [1,2,3] | x * 2) AS doubled")
        doubled = result[0]["doubled"]
        assert isinstance(doubled, CypherList)
        assert [v.value for v in doubled.value] == [2, 4, 6]

    def test_extract_addition(self):
        """Extract with addition."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [1,2,3] | x + 10) AS incremented")
        assert [v.value for v in result[0]["incremented"].value] == [11, 12, 13]

    def test_extract_identity(self):
        """Extract with identity transformation."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [1,2,3] | x) AS same")
        assert [v.value for v in result[0]["same"].value] == [1, 2, 3]

    def test_extract_empty_list(self):
        """Extract from empty list returns empty list."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [] | x * 2) AS doubled")
        doubled = result[0]["doubled"]
        assert isinstance(doubled, CypherList)
        assert len(doubled.value) == 0

    def test_extract_null_list(self):
        """Extract from NULL list returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN null | x * 2) AS doubled")
        assert isinstance(result[0]["doubled"], CypherNull)

    def test_extract_null_items(self):
        """Extract processes NULL items normally."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [1, null, 3] | x) AS items")
        items = result[0]["items"]
        assert len(items.value) == 3
        assert items.value[0].value == 1
        assert isinstance(items.value[1], CypherNull)
        assert items.value[2].value == 3

    def test_extract_property_access(self):
        """Extract node properties."""
        gf = GraphForge()
        gf.execute("CREATE (:Person {name: 'Alice', age: 30})")
        gf.execute("CREATE (:Person {name: 'Bob', age: 25})")

        result = gf.execute(
            """
            MATCH (p:Person)
            WITH collect(p) AS people
            RETURN extract(person IN people | person.name) AS names
            """
        )

        names = result[0]["names"]
        assert isinstance(names, CypherList)
        assert len(names.value) == 2
        name_values = sorted([name.value for name in names.value])
        assert name_values == ["Alice", "Bob"]

    def test_extract_complex_expression(self):
        """Extract with complex expression."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [1,2,3] | x * x + x) AS computed")
        # x=1: 1*1+1=2, x=2: 2*2+2=6, x=3: 3*3+3=12
        assert [v.value for v in result[0]["computed"].value] == [2, 6, 12]

    def test_extract_strings(self):
        """Extract from list of strings."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(s IN ['hello', 'world'] | s) AS words")
        words = result[0]["words"]
        assert [w.value for w in words.value] == ["hello", "world"]


class TestReduceExpression:
    """Test REDUCE() expression."""

    def test_reduce_sum(self):
        """Reduce to compute sum."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(sum = 0, x IN [1,2,3,4] | sum + x) AS total")
        assert result[0]["total"].value == 10

    def test_reduce_product(self):
        """Reduce to compute product."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(product = 1, x IN [2,3,4] | product * x) AS total")
        assert result[0]["total"].value == 24

    def test_reduce_string_concatenation(self):
        """Reduce to concatenate strings."""
        gf = GraphForge()
        result = gf.execute(
            "RETURN reduce(str = '', s IN ['a', 'b', 'c'] | str + s) AS concatenated"
        )
        assert result[0]["concatenated"].value == "abc"

    def test_reduce_empty_list_returns_initial(self):
        """Reduce on empty list returns initial value."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(sum = 42, x IN [] | sum + x) AS total")
        assert result[0]["total"].value == 42

    def test_reduce_null_list(self):
        """Reduce on NULL list returns NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(sum = 0, x IN null | sum + x) AS total")
        assert isinstance(result[0]["total"], CypherNull)

    def test_reduce_with_initial_null(self):
        """Reduce with NULL initial value."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(acc = null, x IN [1,2,3] | x) AS result")
        # Last value wins since we just assign x
        assert result[0]["result"].value == 3

    def test_reduce_max_value(self):
        """Reduce to find maximum value."""
        # This is a bit contrived but tests conditional logic in reduce
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN reduce(
                maxVal = 0,
                x IN [5, 2, 8, 3, 9, 1] |
                CASE WHEN x > maxVal THEN x ELSE maxVal END
            ) AS maximum
            """
        )
        assert result[0]["maximum"].value == 9

    def test_reduce_complex_accumulator(self):
        """Reduce with complex accumulator expression."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(acc = 0, x IN [1,2,3] | acc + x * 2) AS total")
        # acc=0, x=1: 0 + 1*2 = 2
        # acc=2, x=2: 2 + 2*2 = 6
        # acc=6, x=3: 6 + 3*2 = 12
        assert result[0]["total"].value == 12

    def test_reduce_count_items(self):
        """Reduce to count items."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(count = 0, x IN [10,20,30,40] | count + 1) AS length")
        assert result[0]["length"].value == 4

    def test_reduce_nested_expression(self):
        """Reduce with nested expression."""
        gf = GraphForge()
        result = gf.execute("RETURN reduce(sum = 0, x IN [1,2,3] | sum + (x * x)) AS sumOfSquares")
        # 1*1 + 2*2 + 3*3 = 1 + 4 + 9 = 14
        assert result[0]["sumOfSquares"].value == 14


class TestListOperationComposition:
    """Test composition of list operations."""

    def test_filter_then_extract(self):
        """Filter followed by extract."""
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN extract(
                x IN filter(y IN [1,2,3,4,5] WHERE y > 2) | x * 2
            ) AS result
            """
        )
        # filter: [3,4,5], then extract (double): [6,8,10]
        assert [v.value for v in result[0]["result"].value] == [6, 8, 10]

    def test_extract_then_reduce(self):
        """Extract followed by reduce."""
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN reduce(
                sum = 0,
                x IN extract(y IN [1,2,3] | y * 2) | sum + x
            ) AS total
            """
        )
        # extract: [2,4,6], then reduce (sum): 12
        assert result[0]["total"].value == 12

    def test_filter_extract_reduce_chain(self):
        """Chain filter, extract, and reduce."""
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN reduce(
                sum = 0,
                x IN extract(
                    y IN filter(z IN [1,2,3,4,5] WHERE z > 2) | y * 2
                ) | sum + x
            ) AS total
            """
        )
        # filter: [3,4,5], extract: [6,8,10], reduce: 24
        assert result[0]["total"].value == 24

    def test_nested_filter(self):
        """Nested filter expressions (different variables)."""
        # This is a bit artificial but tests variable scoping
        gf = GraphForge()
        result = gf.execute(
            """
            WITH [1,2,3] AS nums1, [4,5,6] AS nums2
            RETURN [
                x IN nums1 WHERE x IN filter(y IN nums2 WHERE y < 6)
            ] AS result
            """
        )
        # This should return [] since nums1 and nums2 don't overlap
        # Actually, this tests if 1,2,3 are IN [4,5], which they're not
        filtered = result[0]["result"]
        assert isinstance(filtered, CypherList)
        assert len(filtered.value) == 0

    def test_extract_with_filter_in_expression(self):
        """Extract where the map expression contains a filter."""
        gf = GraphForge()
        result = gf.execute(
            """
            RETURN extract(
                x IN [1,2,3] |
                filter(y IN [1,2,3,4,5] WHERE y > x)
            ) AS result
            """
        )
        # x=1: filter [2,3,4,5]
        # x=2: filter [3,4,5]
        # x=3: filter [4,5]
        assert len(result[0]["result"].value) == 3
        assert [len(item.value) for item in result[0]["result"].value] == [4, 3, 2]


class TestListOperationEdgeCases:
    """Test edge cases and error conditions."""

    def test_filter_non_list_raises_error(self):
        """Filter on non-list raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="FILTER requires a list"):
            gf.execute("RETURN filter(x IN 123 WHERE x > 1) AS result")

    def test_extract_non_list_raises_error(self):
        """Extract on non-list raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="EXTRACT requires a list"):
            gf.execute("RETURN extract(x IN 123 | x * 2) AS result")

    def test_reduce_non_list_raises_error(self):
        """Reduce on non-list raises TypeError."""
        gf = GraphForge()
        with pytest.raises(TypeError, match="REDUCE requires a list"):
            gf.execute("RETURN reduce(sum = 0, x IN 123 | sum + x) AS result")

    def test_variable_shadowing_filter(self):
        """Filter with variable shadowing."""
        gf = GraphForge()
        result = gf.execute(
            """
            WITH 10 AS x
            RETURN filter(x IN [1,2,3] WHERE x > 1) AS filtered, x AS outer_x
            """
        )
        # Inner x shadows outer x in filter
        assert [v.value for v in result[0]["filtered"].value] == [2, 3]
        assert result[0]["outer_x"].value == 10

    def test_variable_shadowing_extract(self):
        """Extract with variable shadowing."""
        gf = GraphForge()
        result = gf.execute(
            """
            WITH 10 AS x
            RETURN extract(x IN [1,2,3] | x * 2) AS doubled, x AS outer_x
            """
        )
        # Inner x shadows outer x in extract
        assert [v.value for v in result[0]["doubled"].value] == [2, 4, 6]
        assert result[0]["outer_x"].value == 10

    def test_variable_shadowing_reduce(self):
        """Reduce with variable shadowing."""
        gf = GraphForge()
        result = gf.execute(
            """
            WITH 100 AS x
            RETURN reduce(sum = 0, x IN [1,2,3] | sum + x) AS total, x AS outer_x
            """
        )
        # Inner x shadows outer x in reduce
        assert result[0]["total"].value == 6
        assert result[0]["outer_x"].value == 100

    def test_filter_with_null_in_list(self):
        """Filter list containing NULL values."""
        gf = GraphForge()
        result = gf.execute("RETURN filter(x IN [1, null, 3, null, 5] WHERE x > 2) AS filtered")
        # NULL comparisons return NULL, treated as false in WHERE
        filtered = result[0]["filtered"]
        assert len(filtered.value) == 2
        assert [v.value for v in filtered.value] == [3, 5]

    def test_extract_null_transformation_result(self):
        """Extract where transformation produces NULL."""
        gf = GraphForge()
        result = gf.execute("RETURN extract(x IN [1,2,3] | null) AS nulls")
        nulls = result[0]["nulls"]
        assert len(nulls.value) == 3
        assert all(isinstance(v, CypherNull) for v in nulls.value)

    def test_reduce_with_null_in_list(self):
        """Reduce over list containing NULL values."""
        # This tests that NULL items are processed
        gf = GraphForge()
        result = gf.execute("RETURN reduce(count = 0, x IN [1, null, 3] | count + 1) AS count")
        # Count all items including NULL
        assert result[0]["count"].value == 3
