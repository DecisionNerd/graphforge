"""Unit tests for _expressions_match helper method."""

from graphforge import GraphForge
from graphforge.ast.expression import FunctionCall, Literal, PropertyAccess, Variable


class TestExpressionsMatchDirect:
    """Test the _expressions_match helper method directly."""

    def test_same_object_returns_true(self):
        """Test that comparing an expression to itself returns True."""
        gf = GraphForge()
        executor = gf.executor
        expr = Variable(name="x")
        assert executor._expressions_match(expr, expr) is True

    def test_different_types_returns_false(self):
        """Test that expressions of different types return False."""
        gf = GraphForge()
        executor = gf.executor
        var = Variable(name="x")
        lit = Literal(value=5)
        assert executor._expressions_match(var, lit) is False

    def test_variables_same_name_returns_true(self):
        """Test that Variables with same name match."""
        gf = GraphForge()
        executor = gf.executor
        var1 = Variable(name="person")
        var2 = Variable(name="person")
        assert executor._expressions_match(var1, var2) is True

    def test_variables_different_name_returns_false(self):
        """Test that Variables with different names don't match."""
        gf = GraphForge()
        executor = gf.executor
        var1 = Variable(name="person")
        var2 = Variable(name="movie")
        assert executor._expressions_match(var1, var2) is False

    def test_literals_same_value_returns_true(self):
        """Test that Literals with same value match."""
        gf = GraphForge()
        executor = gf.executor
        lit1 = Literal(value=42)
        lit2 = Literal(value=42)
        assert executor._expressions_match(lit1, lit2) is True

    def test_literals_different_value_returns_false(self):
        """Test that Literals with different values don't match."""
        gf = GraphForge()
        executor = gf.executor
        lit1 = Literal(value=42)
        lit2 = Literal(value=99)
        assert executor._expressions_match(lit1, lit2) is False

    def test_property_access_same_returns_true(self):
        """Test that PropertyAccess with same variable and property match."""
        gf = GraphForge()
        executor = gf.executor
        prop1 = PropertyAccess(variable="p", property="name")
        prop2 = PropertyAccess(variable="p", property="name")
        assert executor._expressions_match(prop1, prop2) is True

    def test_property_access_different_property_returns_false(self):
        """Test that PropertyAccess with different properties don't match."""
        gf = GraphForge()
        executor = gf.executor
        prop1 = PropertyAccess(variable="p", property="name")
        prop2 = PropertyAccess(variable="p", property="age")
        assert executor._expressions_match(prop1, prop2) is False

    def test_property_access_different_variable_returns_false(self):
        """Test that PropertyAccess with different variables don't match."""
        gf = GraphForge()
        executor = gf.executor
        prop1 = PropertyAccess(variable="p", property="name")
        prop2 = PropertyAccess(variable="m", property="name")
        assert executor._expressions_match(prop1, prop2) is False

    def test_function_call_same_name_and_args_returns_true(self):
        """Test that FunctionCall with same name and args match."""
        gf = GraphForge()
        executor = gf.executor
        func1 = FunctionCall(name="count", args=[Variable(name="n")])
        func2 = FunctionCall(name="count", args=[Variable(name="n")])
        assert executor._expressions_match(func1, func2) is True

    def test_function_call_different_name_returns_false(self):
        """Test that FunctionCall with different names don't match."""
        gf = GraphForge()
        executor = gf.executor
        func1 = FunctionCall(name="count", args=[Variable(name="n")])
        func2 = FunctionCall(name="sum", args=[Variable(name="n")])
        assert executor._expressions_match(func1, func2) is False

    def test_function_call_different_arg_count_returns_false(self):
        """Test that FunctionCall with different arg counts don't match."""
        gf = GraphForge()
        executor = gf.executor
        func1 = FunctionCall(name="count", args=[Variable(name="n")])
        func2 = FunctionCall(name="count", args=[Variable(name="n"), Variable(name="m")])
        assert executor._expressions_match(func1, func2) is False

    def test_function_call_different_args_returns_false(self):
        """Test that FunctionCall with different args don't match."""
        gf = GraphForge()
        executor = gf.executor
        func1 = FunctionCall(name="count", args=[Variable(name="n")])
        func2 = FunctionCall(name="count", args=[Variable(name="m")])
        assert executor._expressions_match(func1, func2) is False

    def test_function_call_case_insensitive_name(self):
        """Test that FunctionCall names are case-insensitive."""
        gf = GraphForge()
        executor = gf.executor
        func1 = FunctionCall(name="COUNT", args=[Variable(name="n")])
        func2 = FunctionCall(name="count", args=[Variable(name="n")])
        assert executor._expressions_match(func1, func2) is True

    def test_function_call_nested_args(self):
        """Test that FunctionCall with nested expressions match correctly."""
        gf = GraphForge()
        executor = gf.executor
        # count(p.age)
        func1 = FunctionCall(name="count", args=[PropertyAccess(variable="p", property="age")])
        func2 = FunctionCall(name="count", args=[PropertyAccess(variable="p", property="age")])
        assert executor._expressions_match(func1, func2) is True

    def test_function_call_nested_args_different(self):
        """Test that FunctionCall with different nested expressions don't match."""
        gf = GraphForge()
        executor = gf.executor
        # count(p.age) vs count(p.name)
        func1 = FunctionCall(name="count", args=[PropertyAccess(variable="p", property="age")])
        func2 = FunctionCall(name="count", args=[PropertyAccess(variable="p", property="name")])
        assert executor._expressions_match(func1, func2) is False
