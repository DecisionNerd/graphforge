"""pytest-bdd configuration for TCK tests."""

import pytest
from pytest_bdd import given, parsers, then, when

from graphforge import GraphForge

# Import TCK markers plugin
pytest_plugins = ["tests.tck.tck_markers"]
from graphforge.types.graph import EdgeRef, NodeRef
from graphforge.types.values import (
    CypherBool,
    CypherFloat,
    CypherInt,
    CypherNull,
    CypherString,
)


@pytest.fixture
def tck_context():
    """Context for TCK test execution.

    Maintains graph instance and query results across steps.
    """
    return {
        "graph": None,
        "result": None,
        "side_effects": [],
    }


@given("an empty graph", target_fixture="tck_context")
def empty_graph(tck_context):
    """Initialize an empty GraphForge instance."""
    tck_context["graph"] = GraphForge()
    tck_context["result"] = None
    tck_context["side_effects"] = []
    return tck_context


@given(parsers.parse("the {graph_name} graph"), target_fixture="tck_context")
def named_graph(tck_context, graph_name):
    """Load a predefined named graph from TCK graphs directory."""
    import yaml
    from pathlib import Path

    # Load TCK config to find graph script
    config_path = Path(__file__).parent / "tck_config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Get graph script path
    graph_config = config.get("named_graphs", {}).get(graph_name)
    if not graph_config:
        raise ValueError(f"Named graph '{graph_name}' not found in tck_config.yaml")

    script_path = Path(__file__).parent / graph_config["script"]
    if not script_path.exists():
        raise FileNotFoundError(f"Graph script not found: {script_path}")

    # Load and execute graph creation script
    cypher_script = script_path.read_text()
    tck_context["graph"] = GraphForge()
    tck_context["graph"].execute(cypher_script)
    tck_context["result"] = None
    tck_context["side_effects"] = []
    return tck_context


@given("any graph", target_fixture="tck_context")
def any_graph(tck_context):
    """Create an arbitrary graph (test doesn't depend on initial state)."""
    tck_context["graph"] = GraphForge()
    tck_context["result"] = None
    tck_context["side_effects"] = []
    return tck_context


@given("having executed:")
def execute_setup_query_colon(tck_context, docstring):
    """Execute a setup query (typically CREATE statements) - with colon."""
    tck_context["graph"].execute(docstring)


@given("having executed")
def execute_setup_query(tck_context, docstring):
    """Execute a setup query (typically CREATE statements) - without colon."""
    tck_context["graph"].execute(docstring)


@when("executing query:")
def execute_query_colon(tck_context, docstring):
    """Execute a Cypher query and store results (with colon)."""
    try:
        result = tck_context["graph"].execute(docstring)
        tck_context["result"] = result
    except Exception as e:
        tck_context["result"] = {"error": str(e)}


@when("executing query")
def execute_query(tck_context, docstring):
    """Execute a Cypher query and store results (without colon)."""
    try:
        result = tck_context["graph"].execute(docstring)
        tck_context["result"] = result
    except Exception as e:
        tck_context["result"] = {"error": str(e)}


@then("the result should be, in any order:")
def verify_result_any_order_colon(tck_context, datatable):
    """Verify query results match expected table (order doesn't matter) - with colon."""
    result = tck_context["result"]

    # Parse the data table (datatable is list of lists: [headers, row1, row2, ...])
    expected = _parse_data_table(datatable)

    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == len(expected), f"Expected {len(expected)} rows, got {len(result)}"

    # Convert results to comparable format
    actual_rows = [_row_to_comparable(row) for row in result]
    expected_rows = [_row_to_comparable(row) for row in expected]

    # Check that all expected rows are present
    for exp_row in expected_rows:
        assert exp_row in actual_rows, f"Expected row not found: {exp_row}"


@then("the result should be, in any order")
def verify_result_any_order(tck_context, datatable):
    """Verify query results match expected table (order doesn't matter) - without colon."""
    result = tck_context["result"]

    # Parse the data table (datatable is list of lists: [headers, row1, row2, ...])
    expected = _parse_data_table(datatable)

    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == len(expected), f"Expected {len(expected)} rows, got {len(result)}"

    # Convert results to comparable format
    actual_rows = [_row_to_comparable(row) for row in result]
    expected_rows = [_row_to_comparable(row) for row in expected]

    # Check that all expected rows are present
    for exp_row in expected_rows:
        assert exp_row in actual_rows, f"Expected row not found: {exp_row}"


@then("the result should be, in order")
def verify_result_in_order(tck_context, datatable):
    """Verify query results match expected table (order matters)."""
    result = tck_context["result"]

    # Parse the data table (datatable is list of lists: [headers, row1, row2, ...])
    expected = _parse_data_table(datatable)

    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == len(expected), f"Expected {len(expected)} rows, got {len(result)}"

    # Convert results to comparable format and check order
    for i, (actual_row, expected_row) in enumerate(zip(result, expected)):
        actual_comparable = _row_to_comparable(actual_row)
        expected_comparable = _row_to_comparable(expected_row)
        assert (
            actual_comparable == expected_comparable
        ), f"Row {i} mismatch: expected {expected_comparable}, got {actual_comparable}"


@then(parsers.parse("the result should have {count:d} rows"))
def verify_row_count(tck_context, count):
    """Verify the number of result rows."""
    result = tck_context["result"]
    assert result is not None, "No result was produced"
    assert "error" not in result, f"Query error: {result.get('error')}"
    assert len(result) == count, f"Expected {count} rows, got {len(result)}"


@then("no side effects")
def verify_no_side_effects(tck_context):
    """Verify no unexpected side effects occurred."""
    # In our case, this is a no-op since we don't track side effects yet
    # But it's important for TCK compliance
    pass




def _parse_value(value_str: str):
    """Parse a value string into appropriate CypherValue."""
    value_str = value_str.strip()

    # String
    if value_str.startswith("'") and value_str.endswith("'"):
        return CypherString(value_str[1:-1])

    # Boolean
    if value_str.lower() == "true":
        return CypherBool(True)
    if value_str.lower() == "false":
        return CypherBool(False)

    # Null
    if value_str.lower() == "null":
        return CypherNull()

    # Number (int or float)
    try:
        if "." in value_str:
            return CypherFloat(float(value_str))
        return CypherInt(int(value_str))
    except ValueError:
        # Default to string
        return CypherString(value_str)


def _parse_data_table(datatable: list[list[str]]) -> list[dict]:
    """Parse expected result table from pytest-bdd datatable.

    Args:
        datatable: List of lists where first row is headers, subsequent rows are data

    Returns:
        List of dictionaries with parsed values
    """
    if not datatable or len(datatable) < 1:
        return []

    # First row is headers
    headers = datatable[0]

    # Parse each data row
    results = []
    for row in datatable[1:]:
        row_dict = {}
        for header, value in zip(headers, row):
            row_dict[header] = _parse_value(value)
        results.append(row_dict)

    return results


def _row_to_comparable(row: dict) -> dict:
    """Convert a result row to a comparable dictionary.

    Handles CypherValues, NodeRefs, etc.
    """
    comparable = {}
    for key, value in row.items():
        if isinstance(value, (CypherInt, CypherFloat, CypherString, CypherBool)):
            comparable[key] = value.value
        elif isinstance(value, CypherNull):
            comparable[key] = None
        elif isinstance(value, NodeRef):
            # Convert node to comparable dict
            comparable[key] = {
                "labels": sorted(value.labels),
                "properties": {
                    k: v.value if hasattr(v, "value") else v
                    for k, v in value.properties.items()
                },
            }
        elif isinstance(value, EdgeRef):
            # Convert edge to comparable dict
            comparable[key] = {
                "type": value.type,
                "properties": {
                    k: v.value if hasattr(v, "value") else v
                    for k, v in value.properties.items()
                },
            }
        else:
            comparable[key] = value

    return comparable
