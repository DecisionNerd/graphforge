"""Unit tests for advanced aggregation functions (v0.4.0)."""

import math

import pytest

from graphforge.api import GraphForge


class TestPercentileDiscFunction:
    """Tests for percentileDisc() function."""

    def test_percentile_disc_median(self):
        """Test percentileDisc with 0.5 (median)."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")
        gf.execute("CREATE (:Value {num: 2})")
        gf.execute("CREATE (:Value {num: 3})")
        gf.execute("CREATE (:Value {num: 4})")
        gf.execute("CREATE (:Value {num: 5})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileDisc(v.num, 0.5) AS median
            """
        )
        assert len(results) == 1
        # For [1,2,3,4,5], 0.5 * 5 = 2.5, int(2.5) = 2 (0-indexed), so value is 3
        assert results[0]["median"].value == 3.0

    def test_percentile_disc_min(self):
        """Test percentileDisc with 0.0 (minimum)."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 10})")
        gf.execute("CREATE (:Value {num: 20})")
        gf.execute("CREATE (:Value {num: 30})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileDisc(v.num, 0.0) AS min_val
            """
        )
        assert results[0]["min_val"].value == 10.0

    def test_percentile_disc_max(self):
        """Test percentileDisc with 1.0 (maximum)."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 10})")
        gf.execute("CREATE (:Value {num: 20})")
        gf.execute("CREATE (:Value {num: 30})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileDisc(v.num, 1.0) AS max_val
            """
        )
        assert results[0]["max_val"].value == 30.0

    def test_percentile_disc_quartiles(self):
        """Test percentileDisc with quartiles."""
        gf = GraphForge()
        for i in range(1, 11):
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN
                percentileDisc(v.num, 0.25) AS q1,
                percentileDisc(v.num, 0.75) AS q3
            """
        )
        assert results[0]["q1"].value == 3.0  # int(0.25 * 10) = 2 -> value at index 2
        assert results[0]["q3"].value == 8.0  # int(0.75 * 10) = 7 -> value at index 7

    def test_percentile_disc_empty_result(self):
        """Test percentileDisc with no matching values."""
        gf = GraphForge()
        results = gf.execute(
            """
            MATCH (v:NonExistent)
            RETURNpercentileDisc(v.num, 0.5) AS result
            """
        )
        # Aggregations with no matches return 1 row with NULL
        assert len(results) == 1
        assert results[0]["result"].value is None

    def test_percentile_disc_null_values_ignored(self):
        """Test percentileDisc ignores NULL values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")
        gf.execute("CREATE (:Value {num: 2})")
        gf.execute("CREATE (:Value)")  # No num property

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileDisc(v.num, 0.5) AS median
            """
        )
        # Should only consider 1 and 2
        assert results[0]["median"].value in [1.0, 2.0]

    def test_percentile_disc_invalid_percentile_too_high(self):
        """Test percentileDisc with percentile > 1.0."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURNpercentileDisc(v.num, 1.5) AS result
                """
            )

    def test_percentile_disc_invalid_percentile_negative(self):
        """Test percentileDisc with negative percentile."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
            gf.execute(
                """
                MATCH (v:Value)
                RETURNpercentileDisc(v.num, -0.1) AS result
                """
            )

    def test_percentile_disc_null_percentile(self):
        """Test percentileDisc with NULL percentile returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileDisc(v.num, null) AS result
            """
        )
        assert results[0]["result"].value is None


class TestPercentileContFunction:
    """Tests for percentileCont() function."""

    def test_percentile_cont_median_odd_count(self):
        """Test percentileCont with median (odd number of values)."""
        gf = GraphForge()
        for i in [1, 2, 3, 4, 5]:
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileCont(v.num, 0.5) AS median
            """
        )
        # For [1,2,3,4,5], median is exactly 3.0
        assert results[0]["median"].value == 3.0

    def test_percentile_cont_median_even_count(self):
        """Test percentileCont with median (even number of values)."""
        gf = GraphForge()
        for i in [1, 2, 3, 4]:
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileCont(v.num, 0.5) AS median
            """
        )
        # For [1,2,3,4], position = 0.5 * 3 = 1.5
        # Interpolate between index 1 (value 2) and index 2 (value 3)
        # result = 2 + 0.5 * (3 - 2) = 2.5
        assert results[0]["median"].value == 2.5

    def test_percentile_cont_interpolation(self):
        """Test percentileCont performs linear interpolation."""
        gf = GraphForge()
        for i in [10, 20, 30, 40]:
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileCont(v.num, 0.25) AS p25
            """
        )
        # position = 0.25 * 3 = 0.75
        # Between index 0 (10) and index 1 (20)
        # result = 10 + 0.75 * (20 - 10) = 17.5
        assert results[0]["p25"].value == 17.5

    def test_percentile_cont_min_max(self):
        """Test percentileCont at boundaries."""
        gf = GraphForge()
        for i in [5, 10, 15]:
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN
                percentileCont(v.num, 0.0) AS min_val,
                percentileCont(v.num, 1.0) AS max_val
            """
        )
        assert results[0]["min_val"].value == 5.0
        assert results[0]["max_val"].value == 15.0

    def test_percentile_cont_95th(self):
        """Test percentileCont with 95th percentile."""
        gf = GraphForge()
        for i in range(1, 101):
            gf.execute(f"CREATE (:Value {{num: {i}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNpercentileCont(v.num, 0.95) AS p95
            """
        )
        # Should be close to 95 (with some interpolation)
        assert 94.0 <= results[0]["p95"].value <= 96.0


class TestStDevFunction:
    """Tests for stDev() (sample standard deviation) function."""

    def test_stdev_basic(self):
        """Test stDev with basic values."""
        gf = GraphForge()
        # Sample: [2, 4, 6, 8]
        # Mean = 5
        # Variance = [(2-5)^2 + (4-5)^2 + (6-5)^2 + (8-5)^2] / 3 = (9+1+1+9)/3 = 20/3
        # StDev = sqrt(20/3) ≈ 2.582
        for val in [2, 4, 6, 8]:
            gf.execute(f"CREATE (:Value {{num: {val}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDev(v.num) AS std
            """
        )
        expected = math.sqrt(20 / 3)
        assert abs(results[0]["std"].value - expected) < 0.001

    def test_stdev_single_value_returns_null(self):
        """Test stDev with single value returns NULL."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 42})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDev(v.num) AS std
            """
        )
        assert results[0]["std"].value is None

    def test_stdev_two_values(self):
        """Test stDev with two values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 10})")
        gf.execute("CREATE (:Value {num: 20})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDev(v.num) AS std
            """
        )
        # Mean = 15, variance = [(10-15)^2 + (20-15)^2] / 1 = 50
        # StDev = sqrt(50) ≈ 7.071
        expected = math.sqrt(50)
        assert abs(results[0]["std"].value - expected) < 0.001

    def test_stdev_ignores_null(self):
        """Test stDev ignores NULL values."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")
        gf.execute("CREATE (:Value {num: 2})")
        gf.execute("CREATE (:Value {num: 3})")
        gf.execute("CREATE (:Value)")  # NULL

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDev(v.num) AS std
            """
        )
        # Should compute on [1, 2, 3] only
        # Mean = 2, variance = [(1-2)^2 + (2-2)^2 + (3-2)^2] / 2 = 2/2 = 1
        # StDev = 1
        assert abs(results[0]["std"].value - 1.0) < 0.001


class TestStDevPFunction:
    """Tests for stDevP() (population standard deviation) function."""

    def test_stdevp_basic(self):
        """Test stDevP with basic values."""
        gf = GraphForge()
        # Population: [2, 4, 6, 8]
        # Mean = 5
        # Variance = [(2-5)^2 + (4-5)^2 + (6-5)^2 + (8-5)^2] / 4 = 20/4 = 5
        # StDev = sqrt(5) ≈ 2.236
        for val in [2, 4, 6, 8]:
            gf.execute(f"CREATE (:Value {{num: {val}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDevP(v.num) AS std
            """
        )
        expected = math.sqrt(5)
        assert abs(results[0]["std"].value - expected) < 0.001

    def test_stdevp_single_value(self):
        """Test stDevP with single value returns 0."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 42})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDevP(v.num) AS std
            """
        )
        # Single value has 0 deviation
        assert results[0]["std"].value == 0.0

    def test_stdevp_vs_stdev(self):
        """Test that stDevP < stDev for same data."""
        gf = GraphForge()
        for val in [1, 2, 3, 4, 5]:
            gf.execute(f"CREATE (:Value {{num: {val}}})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDev(v.num) AS sample_std,
                   stDevP(v.num) AS pop_std
            """
        )
        # Population std dev should be smaller than sample std dev
        assert results[0]["pop_std"].value < results[0]["sample_std"].value

    def test_stdevp_identical_values(self):
        """Test stDevP with all identical values."""
        gf = GraphForge()
        for _ in range(5):
            gf.execute("CREATE (:Value {num: 10})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURNstDevP(v.num) AS std
            """
        )
        # No variation = 0 standard deviation
        assert results[0]["std"].value == 0.0


class TestAggregationFunctionsWithGrouping:
    """Tests for advanced aggregation with grouping."""

    def test_stdev_by_category(self):
        """Test stDev grouped by category."""
        gf = GraphForge()
        gf.execute("CREATE (:Product {category: 'A', price: 10})")
        gf.execute("CREATE (:Product {category: 'A', price: 20})")
        gf.execute("CREATE (:Product {category: 'B', price: 100})")
        gf.execute("CREATE (:Product {category: 'B', price: 200})")

        results = gf.execute(
            """
            MATCH (p:Product)
            RETURNp.category AS category,
                   stDev(p.price) AS price_std
            """
        )
        assert len(results) == 2
        # Both groups should have same std dev due to symmetry
        assert results[0]["price_std"].value > 0
        assert results[1]["price_std"].value > 0
