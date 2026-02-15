"""Unit tests for predicate utility functions."""

from graphforge.ast.expression import BinaryOp, Literal, PropertyAccess, UnaryOp, Variable
from graphforge.optimizer.predicate_utils import PredicateAnalysis


class TestExtractConjuncts:
    """Test PredicateAnalysis.extract_conjuncts()."""

    def test_single_predicate(self):
        """Single predicate returns list with one element."""
        pred = BinaryOp(
            op="=",
            left=PropertyAccess(variable="a", property="name"),
            right=Literal(value="Alice"),
        )
        conjuncts = PredicateAnalysis.extract_conjuncts(pred)
        assert len(conjuncts) == 1
        assert conjuncts[0] == pred

    def test_simple_and_chain(self):
        """Simple AND chain is split into two conjuncts."""
        pred = BinaryOp(
            op="AND",
            left=BinaryOp(
                op="=",
                left=PropertyAccess(variable="a", property="name"),
                right=Literal(value="Alice"),
            ),
            right=BinaryOp(
                op=">",
                left=PropertyAccess(variable="a", property="age"),
                right=Literal(value=25),
            ),
        )
        conjuncts = PredicateAnalysis.extract_conjuncts(pred)
        assert len(conjuncts) == 2

    def test_nested_and_chain(self):
        """Nested AND chain is flattened."""
        # (a AND b) AND c → [a, b, c]
        pred = BinaryOp(
            op="AND",
            left=BinaryOp(
                op="AND",
                left=BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1)),
                right=BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2)),
            ),
            right=BinaryOp(op="=", left=Variable(name="c"), right=Literal(value=3)),
        )
        conjuncts = PredicateAnalysis.extract_conjuncts(pred)
        assert len(conjuncts) == 3

    def test_or_predicate_not_split(self):
        """OR predicates are not split (must evaluate together)."""
        pred = BinaryOp(
            op="OR",
            left=BinaryOp(
                op="=",
                left=PropertyAccess(variable="a", property="city"),
                right=Literal(value="NYC"),
            ),
            right=BinaryOp(
                op="=",
                left=PropertyAccess(variable="a", property="city"),
                right=Literal(value="LA"),
            ),
        )
        conjuncts = PredicateAnalysis.extract_conjuncts(pred)
        assert len(conjuncts) == 1
        assert conjuncts[0] == pred

    def test_and_with_or_branches(self):
        """AND with OR branches splits correctly."""
        # (a OR b) AND c → [a OR b, c]
        or_pred = BinaryOp(
            op="OR",
            left=BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1)),
            right=BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2)),
        )
        pred = BinaryOp(
            op="AND",
            left=or_pred,
            right=BinaryOp(op="=", left=Variable(name="c"), right=Literal(value=3)),
        )
        conjuncts = PredicateAnalysis.extract_conjuncts(pred)
        assert len(conjuncts) == 2
        assert conjuncts[0] == or_pred


class TestCombineWithAnd:
    """Test PredicateAnalysis.combine_with_and()."""

    def test_empty_list(self):
        """Empty list returns None."""
        result = PredicateAnalysis.combine_with_and([])
        assert result is None

    def test_single_predicate(self):
        """Single predicate returns unchanged."""
        pred = BinaryOp(
            op="=",
            left=PropertyAccess(variable="a", property="name"),
            right=Literal(value="Alice"),
        )
        result = PredicateAnalysis.combine_with_and([pred])
        assert result == pred

    def test_two_predicates(self):
        """Two predicates combined with AND."""
        pred1 = BinaryOp(
            op="=", left=PropertyAccess(variable="a", property="name"), right=Literal(value="Alice")
        )
        pred2 = BinaryOp(
            op=">", left=PropertyAccess(variable="a", property="age"), right=Literal(value=25)
        )
        result = PredicateAnalysis.combine_with_and([pred1, pred2])

        assert isinstance(result, BinaryOp)
        assert result.op == "AND"
        assert result.left == pred1
        assert result.right == pred2

    def test_three_predicates(self):
        """Three predicates form right-associative chain."""
        # [a, b, c] → a AND (b AND c)
        pred_a = BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1))
        pred_b = BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2))
        pred_c = BinaryOp(op="=", left=Variable(name="c"), right=Literal(value=3))

        result = PredicateAnalysis.combine_with_and([pred_a, pred_b, pred_c])

        assert isinstance(result, BinaryOp)
        assert result.op == "AND"
        assert result.left == pred_a
        assert isinstance(result.right, BinaryOp)
        assert result.right.op == "AND"
        assert result.right.left == pred_b
        assert result.right.right == pred_c

    def test_roundtrip_extract_combine(self):
        """Extract then combine should preserve structure."""
        # Original: a AND b
        original = BinaryOp(
            op="AND",
            left=BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1)),
            right=BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2)),
        )

        conjuncts = PredicateAnalysis.extract_conjuncts(original)
        reconstructed = PredicateAnalysis.combine_with_and(conjuncts)

        # Should have same structure
        assert isinstance(reconstructed, BinaryOp)
        assert reconstructed.op == "AND"


class TestGetReferencedVariables:
    """Test PredicateAnalysis.get_referenced_variables()."""

    def test_variable_reference(self):
        """Variable reference is detected."""
        expr = Variable(name="n")
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == {"n"}

    def test_property_access(self):
        """Property access references the variable."""
        expr = PropertyAccess(variable="n", property="name")
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == {"n"}

    def test_literal_no_variables(self):
        """Literal has no variable references."""
        expr = Literal(value=42)
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == set()

    def test_binary_op_two_variables(self):
        """Binary op with two different variables."""
        expr = BinaryOp(
            op=">",
            left=PropertyAccess(variable="a", property="age"),
            right=PropertyAccess(variable="b", property="age"),
        )
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == {"a", "b"}

    def test_binary_op_same_variable(self):
        """Binary op with same variable twice."""
        expr = BinaryOp(
            op="AND",
            left=BinaryOp(
                op="=",
                left=PropertyAccess(variable="n", property="name"),
                right=Literal(value="Alice"),
            ),
            right=BinaryOp(
                op=">",
                left=PropertyAccess(variable="n", property="age"),
                right=Literal(value=25),
            ),
        )
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == {"n"}

    def test_unary_op(self):
        """Unary op with variable reference."""
        expr = UnaryOp(op="IS NULL", operand=PropertyAccess(variable="n", property="email"))
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == {"n"}

    def test_complex_expression_multiple_variables(self):
        """Complex expression with multiple variables."""
        # (a.age > b.age) AND (c.active = true)
        expr = BinaryOp(
            op="AND",
            left=BinaryOp(
                op=">",
                left=PropertyAccess(variable="a", property="age"),
                right=PropertyAccess(variable="b", property="age"),
            ),
            right=BinaryOp(
                op="=",
                left=PropertyAccess(variable="c", property="active"),
                right=Literal(value=True),
            ),
        )
        vars = PredicateAnalysis.get_referenced_variables(expr)
        assert vars == {"a", "b", "c"}


class TestEstimateSelectivity:
    """Test PredicateAnalysis.estimate_selectivity()."""

    def test_equality_high_selectivity(self):
        """Equality operator is highly selective (0.1)."""
        pred = BinaryOp(
            op="=",
            left=PropertyAccess(variable="a", property="name"),
            right=Literal(value="Alice"),
        )
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.1

    def test_not_equals_low_selectivity(self):
        """Not equals operator is not selective (0.9)."""
        pred = BinaryOp(
            op="<>",
            left=PropertyAccess(variable="a", property="name"),
            right=Literal(value="Alice"),
        )
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.9

    def test_inequality_moderate_selectivity(self):
        """Inequality operators have moderate selectivity (0.5)."""
        for op in ["<", ">", "<=", ">="]:
            pred = BinaryOp(
                op=op,
                left=PropertyAccess(variable="a", property="age"),
                right=Literal(value=25),
            )
            sel = PredicateAnalysis.estimate_selectivity(pred)
            assert sel == 0.5, f"Operator {op} should have selectivity 0.5"

    def test_is_null_high_selectivity(self):
        """IS NULL is highly selective (0.1)."""
        pred = UnaryOp(op="IS NULL", operand=PropertyAccess(variable="a", property="email"))
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.1

    def test_is_not_null_low_selectivity(self):
        """IS NOT NULL is not selective (0.9)."""
        pred = UnaryOp(op="IS NOT NULL", operand=PropertyAccess(variable="a", property="email"))
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.9

    def test_or_takes_max_selectivity(self):
        """OR takes maximum (least selective) of branches."""
        # Equality (0.1) OR Inequality (0.5) → 0.5
        pred = BinaryOp(
            op="OR",
            left=BinaryOp(
                op="=",
                left=PropertyAccess(variable="a", property="city"),
                right=Literal(value="NYC"),
            ),
            right=BinaryOp(
                op=">",
                left=PropertyAccess(variable="a", property="age"),
                right=Literal(value=25),
            ),
        )
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.5  # max(0.1, 0.5)

    def test_and_takes_min_selectivity(self):
        """AND takes minimum (most selective) of branches."""
        # Equality (0.1) AND Not Equals (0.9) → 0.1
        pred = BinaryOp(
            op="AND",
            left=BinaryOp(
                op="=",
                left=PropertyAccess(variable="a", property="name"),
                right=Literal(value="Alice"),
            ),
            right=BinaryOp(
                op="<>",
                left=PropertyAccess(variable="a", property="city"),
                right=Literal(value="NYC"),
            ),
        )
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.1  # min(0.1, 0.9)

    def test_literal_default_selectivity(self):
        """Non-operator expressions have default selectivity (0.5)."""
        pred = Literal(value=True)
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.5

    def test_nested_and_or_selectivity(self):
        """Nested AND/OR computes selectivity correctly."""
        # (a = 1 OR b = 2) AND (c > 3) →  max(0.1, 0.1) AND 0.5 → min(0.1, 0.5) → 0.1
        or_pred = BinaryOp(
            op="OR",
            left=BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1)),
            right=BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2)),
        )
        pred = BinaryOp(
            op="AND",
            left=or_pred,
            right=BinaryOp(op=">", left=Variable(name="c"), right=Literal(value=3)),
        )
        sel = PredicateAnalysis.estimate_selectivity(pred)
        assert sel == 0.1  # min(max(0.1, 0.1), 0.5) = min(0.1, 0.5) = 0.1


class TestSelectivityOrdering:
    """Test that selectivity estimates produce correct ordering."""

    def test_equality_before_inequality(self):
        """Equality should be evaluated before inequality."""
        eq_pred = BinaryOp(op="=", left=Variable(name="a"), right=Literal(value=1))
        ineq_pred = BinaryOp(op=">", left=Variable(name="b"), right=Literal(value=5))

        eq_sel = PredicateAnalysis.estimate_selectivity(eq_pred)
        ineq_sel = PredicateAnalysis.estimate_selectivity(ineq_pred)

        assert eq_sel < ineq_sel, "Equality should be more selective than inequality"

    def test_is_null_before_not_equals(self):
        """IS NULL should be evaluated before NOT EQUALS."""
        null_pred = UnaryOp(op="IS NULL", operand=Variable(name="a"))
        ne_pred = BinaryOp(op="<>", left=Variable(name="b"), right=Literal(value=1))

        null_sel = PredicateAnalysis.estimate_selectivity(null_pred)
        ne_sel = PredicateAnalysis.estimate_selectivity(ne_pred)

        assert null_sel < ne_sel, "IS NULL should be more selective than <>"

    def test_ordering_example(self):
        """Test realistic predicate ordering scenario."""
        predicates = [
            ("NOT EQUALS", BinaryOp(op="<>", left=Variable(name="a"), right=Literal(value=1))),
            ("EQUALITY", BinaryOp(op="=", left=Variable(name="b"), right=Literal(value=2))),
            ("INEQUALITY", BinaryOp(op=">", left=Variable(name="c"), right=Literal(value=3))),
        ]

        # Sort by selectivity (lower = more selective = evaluate first)
        sorted_preds = sorted(
            predicates, key=lambda p: PredicateAnalysis.estimate_selectivity(p[1])
        )

        # Expected order: EQUALITY (0.1), INEQUALITY (0.5), NOT EQUALS (0.9)
        assert sorted_preds[0][0] == "EQUALITY"
        assert sorted_preds[1][0] == "INEQUALITY"
        assert sorted_preds[2][0] == "NOT EQUALS"
