"""Fixtures and utilities for TCK tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tck_coverage():
    """Loads TCK coverage matrix.

    Returns a dictionary mapping TCK features to their support status.
    """
    matrix_path = Path(__file__).parent / "coverage_matrix.json"
    if not matrix_path.exists():
        pytest.skip("TCK coverage matrix not yet created")

    with open(matrix_path) as f:
        return json.load(f)


@pytest.fixture
def tck_runner(db):
    """Provides TCK scenario runner.

    This fixture will be implemented once the TCK runner utility is created.
    """
    # TODO: Implement TCK runner
    pytest.skip("TCK runner not yet implemented")
