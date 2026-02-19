"""Integration tests for advanced aggregation functions (v0.4.0)."""

import math

from graphforge.api import GraphForge


class TestAdvancedAggregationIntegration:
    """Integration tests for percentileDisc, percentileCont, stDev, stDevP."""

    def test_percentile_disc_with_data(self):
        """Test percentileDisc in real query."""
        gf = GraphForge()
        # Create test data
        for age in [20, 25, 30, 35, 40, 45, 50]:
            gf.execute(f"CREATE (:Person {{age: {age}}})")

        results = gf.execute(
            """
            MATCH (p:Person)
            RETURN percentileDisc(p.age, 0.5) AS median_age
            """
        )
        assert len(results) == 1
        # Median of 7 values at position int(0.5*7) = 3 -> 4th value (35)
        assert results[0]["median_age"].value == 35.0

    def test_percentile_cont_with_data(self):
        """Test percentileCont in real query."""
        gf = GraphForge()
        for age in [20, 25, 30, 35, 40, 45, 50]:
            gf.execute(f"CREATE (:Person {{age: {age}}})")

        results = gf.execute(
            """
            MATCH (p:Person)
            RETURN percentileCont(p.age, 0.5) AS median_age
            """
        )
        assert len(results) == 1
        # True median with interpolation
        assert results[0]["median_age"].value == 35.0

    def test_stdev_salary_analysis(self):
        """Test stDev for salary analysis."""
        gf = GraphForge()
        salaries = [50000, 55000, 60000, 65000, 70000]
        for salary in salaries:
            gf.execute(f"CREATE (:Employee {{salary: {salary}}})")

        results = gf.execute(
            """
            MATCH (e:Employee)
            RETURN
                avg(e.salary) AS avg_salary,
                stDev(e.salary) AS salary_std_dev,
                stDevP(e.salary) AS salary_std_dev_pop
            """
        )
        assert results[0]["avg_salary"].value == 60000.0
        # Sample std dev should be > population std dev
        assert results[0]["salary_std_dev"].value > results[0]["salary_std_dev_pop"].value
        # Both should be > 0
        assert results[0]["salary_std_dev"].value > 0
        assert results[0]["salary_std_dev_pop"].value > 0

    def test_combined_aggregations(self):
        """Test multiple aggregations together."""
        gf = GraphForge()
        values = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for val in values:
            gf.execute(f"CREATE (:Data {{value: {val}}})")

        results = gf.execute(
            """
            MATCH (d:Data)
            RETURN
                count(d.value) AS count,
                min(d.value) AS min_val,
                max(d.value) AS max_val,
                avg(d.value) AS avg_val,
                percentileDisc(d.value, 0.25) AS q1,
                percentileDisc(d.value, 0.5) AS median,
                percentileDisc(d.value, 0.75) AS q3,
                stDev(d.value) AS std_dev
            """
        )
        assert results[0]["count"].value == 10
        assert results[0]["min_val"].value == 10
        assert results[0]["max_val"].value == 100
        assert results[0]["avg_val"].value == 55.0
        assert results[0]["median"].value == 60.0  # int(0.5*10)=5 -> index 5 = 60
        assert results[0]["std_dev"].value > 0

    def test_percentile_with_where_clause(self):
        """Test percentile with filtering."""
        gf = GraphForge()
        for i in range(1, 21):
            category = "A" if i <= 10 else "B"
            gf.execute(f"CREATE (:Item {{value: {i}, category: '{category}'}})")

        results = gf.execute(
            """
            MATCH (i:Item)
            WHERE i.category = 'A'
            RETURN percentileDisc(i.value, 0.5) AS median_a
            """
        )
        # Median of [1..10] at position int(0.5*10)=5 -> 6th value
        assert results[0]["median_a"].value == 6.0

    def test_stdev_with_null_handling(self):
        """Test stDev properly ignores NULL values."""
        gf = GraphForge()
        gf.execute("CREATE (:Measurement {value: 10})")
        gf.execute("CREATE (:Measurement {value: 20})")
        gf.execute("CREATE (:Measurement {value: 30})")
        gf.execute("CREATE (:Measurement)")  # No value property

        results = gf.execute(
            """
            MATCH (m:Measurement)
            RETURN
                count(m.value) AS count_values,
                stDev(m.value) AS std_dev
            """
        )
        # Should only count non-NULL values
        assert results[0]["count_values"].value == 3
        # Mean = 20, variance = [(10-20)^2 + (20-20)^2 + (30-20)^2] / 2 = 100
        expected_std = math.sqrt(100)
        assert abs(results[0]["std_dev"].value - expected_std) < 0.001

    def test_percentile_95th_for_monitoring(self):
        """Test 95th percentile for performance monitoring use case."""
        gf = GraphForge()
        # Simulate response times in milliseconds
        response_times = [50, 60, 70, 80, 90, 100, 110, 120, 500, 1000]
        for rt in response_times:
            gf.execute(f"CREATE (:Request {{response_time: {rt}}})")

        results = gf.execute(
            """
            MATCH (r:Request)
            RETURN
                avg(r.response_time) AS avg_response,
                percentileDisc(r.response_time, 0.95) AS p95_response,
                percentileCont(r.response_time, 0.95) AS p95_response_cont
            """
        )
        # Average is skewed by outliers
        assert results[0]["avg_response"].value > 200
        # 95th percentile should be high but not as high as max
        assert results[0]["p95_response"].value >= 500
        assert results[0]["p95_response_cont"].value >= 500

    def test_aggregation_with_distinct(self):
        """Test aggregations handle distinct values."""
        gf = GraphForge()
        # Create duplicate values
        for val in [1, 1, 2, 2, 3, 3, 4, 4, 5, 5]:
            gf.execute(f"CREATE (:Number {{val: {val}}})")

        results = gf.execute(
            """
            MATCH (n:Number)
            RETURN
                count(n.val) AS total_count,
                count(DISTINCT n.val) AS distinct_count,
                stDev(n.val) AS std_all
            """
        )
        assert results[0]["total_count"].value == 10
        assert results[0]["distinct_count"].value == 5
        # StDev computed on all values including duplicates
        assert results[0]["std_all"].value > 0

    def test_percentile_single_group(self):
        """Test percentile with single aggregation (no grouping)."""
        gf = GraphForge()
        for score in [75, 80, 85, 90, 95]:
            gf.execute(f"CREATE (:Student {{score: {score}}})")

        results = gf.execute(
            """
            MATCH (s:Student)
            RETURN
                percentileDisc(s.score, 0.0) AS min_score,
                percentileDisc(s.score, 0.25) AS q1_score,
                percentileDisc(s.score, 0.5) AS median_score,
                percentileDisc(s.score, 0.75) AS q3_score,
                percentileDisc(s.score, 1.0) AS max_score
            """
        )
        assert results[0]["min_score"].value == 75.0
        assert results[0]["max_score"].value == 95.0
        assert results[0]["median_score"].value == 85.0

    def test_float_and_int_mix(self):
        """Test aggregations handle mix of floats and integers."""
        gf = GraphForge()
        gf.execute("CREATE (:Value {num: 1})")
        gf.execute("CREATE (:Value {num: 2.5})")
        gf.execute("CREATE (:Value {num: 3})")
        gf.execute("CREATE (:Value {num: 4.5})")

        results = gf.execute(
            """
            MATCH (v:Value)
            RETURN
                avg(v.num) AS avg_val,
                stDev(v.num) AS std_val,
                percentileCont(v.num, 0.5) AS median
            """
        )
        # Average of [1, 2.5, 3, 4.5] = 11/4 = 2.75
        assert results[0]["avg_val"].value == 2.75
        assert results[0]["std_val"].value > 0
        assert results[0]["median"].value > 0
