"""Unit tests for advanced aggregation function error handling."""

import pytest

from graphforge.api import GraphForge


class TestPercentileDiscErrors:
    """Error handling tests for percentileDisc()."""

    def test_wrong_argument_count(self):
        """Test percentileDisc with wrong number of arguments."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(TypeError, match="percentileDisc expects 2 arguments"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileDisc(v.num) AS result
                """
            )

    def test_non_numeric_percentile(self):
        """Test percentileDisc with non-numeric percentile."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(TypeError, match="percentileDisc percentile must be a number"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileDisc(v.num, 'invalid') AS result
                """
            )

    def test_non_numeric_values(self):
        """Test percentileDisc with non-numeric values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {text: 'hello'})")

        with pytest.raises(TypeError, match="percentileDisc requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileDisc(v.text, 0.5) AS result
                """
            )

    def test_boolean_value(self):
        """Test percentileDisc with boolean values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {flag: true})")

        with pytest.raises(TypeError, match="percentileDisc requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileDisc(v.flag, 0.5) AS result
                """
            )


class TestPercentileContErrors:
    """Error handling tests for percentileCont()."""

    def test_wrong_argument_count(self):
        """Test percentileCont with wrong number of arguments."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(TypeError, match="percentileCont expects 2 arguments"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileCont(v.num) AS result
                """
            )

    def test_non_numeric_percentile(self):
        """Test percentileCont with non-numeric percentile."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(TypeError, match="percentileCont percentile must be a number"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileCont(v.num, 'invalid') AS result
                """
            )

    def test_invalid_percentile_range(self):
        """Test percentileCont with out-of-range percentile."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileCont(v.num, 1.5) AS result
                """
            )

    def test_non_numeric_values(self):
        """Test percentileCont with non-numeric values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {text: 'world'})")

        with pytest.raises(TypeError, match="percentileCont requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN percentileCont(v.text, 0.5) AS result
                """
            )

    def test_empty_result_returns_null(self):
        """Test percentileCont with no values returns NULL."""
        gf = GraphForge()
        results = gf.execute(
            """
            MATCH (v:NonExistent)
            RETURN percentileCont(v.num, 0.5) AS result
            """
        )
        assert len(results) == 1
        assert results[0]["result"].value is None


class TestStDevErrors:
    """Error handling tests for stDev()."""

    def test_non_numeric_values(self):
        """Test stDev with non-numeric values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {text: 'test'})")
        gf.execute("CREATE (:Value {text: 'data'})")

        with pytest.raises(TypeError, match="stDev requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN stDev(v.text) AS result
                """
            )

    def test_list_value_error(self):
        """Test stDev with list values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {nums: [1, 2, 3]})")
        gf.execute("CREATE (:Value {nums: [4, 5, 6]})")

        with pytest.raises(TypeError, match="stDev requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN stDev(v.nums) AS result
                """
            )


class TestStDevPErrors:
    """Error handling tests for stDevP()."""

    def test_empty_values_returns_null(self):
        """Test stDevP with no values returns NULL."""
        gf = GraphForge()
        results = gf.execute(
            """
            MATCH (v:NonExistent)
            RETURN stDevP(v.num) AS result
            """
        )
        assert len(results) == 1
        assert results[0]["result"].value is None

    def test_non_numeric_values(self):
        """Test stDevP with non-numeric values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {text: 'data'})")

        with pytest.raises(TypeError, match="stDevP requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN stDevP(v.text) AS result
                """
            )

    def test_map_value_error(self):
        """Test stDevP with map values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {props: {a: 1}})")

        with pytest.raises(TypeError, match="stDevP requires numeric values"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURN stDevP(v.props) AS result
                """
            )


class TestEdgeCases:
    """Edge case tests for advanced aggregation functions."""

    def test_percentile_disc_with_floats(self):
        """Test percentileDisc with float values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1.5})")
        gf.execute("CREATE (:Value {num: 2.5})")
        gf.execute("CREATE (:Value {num: 3.5})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN percentileDisc(v.num, 0.5) AS median
            """
        )
        assert results[0]["median"].value == 2.5

    def test_percentile_cont_null_percentile(self):
        """Test percentileCont with NULL percentile."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN percentileCont(v.num, null) AS result
            """
        )
        assert results[0]["result"].value is None

    def test_percentile_cont_boundary_upper_index(self):
        """Test percentileCont edge case near upper boundary."""
        gf = GraphForge()
        for i in [10, 20]:
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN percentileCont(v.num, 0.99) AS p99
            """
        )
        # Should handle upper_index boundary correctly
        assert results[0]["p99"].value > 10.0

    def test_stdevp_with_float_values(self):
        """Test stDevP with float values."""
        gf = GraphForge()
        for val in [1.5, 2.5, 3.5]:
            gf.execute(f"CREATE (:Value {{num: {val}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN stDevP(v.num) AS std
            """
        )
        assert results[0]["std"].value > 0
