"""Shared pytest fixtures for all test categories."""

from pathlib import Path
import tempfile

import pytest

# TCK test markers plugin (must be at top level)
pytest_plugins = ["tests.tck.tck_markers"]


@pytest.fixture
def tmp_db_path():
    """Provides a temporary database path that's cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "test.db"


@pytest.fixture
def db(tmp_db_path):
    """Provides a fresh GraphForge instance with temporary storage.

    This fixture will be updated once the GraphForge class is implemented.
    """
    # TODO: Implement once GraphForge class exists
    # from graphforge import GraphForge
    # return GraphForge(tmp_db_path)
    pytest.skip("GraphForge class not yet implemented")


@pytest.fixture
def memory_db():
    """Provides an in-memory GraphForge instance (no persistence).

    This fixture will be updated once the GraphForge class is implemented.
    """
    # TODO: Implement once GraphForge class exists
    # from graphforge import GraphForge
    # return GraphForge(":memory:")
    pytest.skip("GraphForge class not yet implemented")


@pytest.fixture
def sample_graph(db):
    """Provides a database with sample data for testing.

    The sample graph contains:
    - 3 Person nodes with properties (name, age)
    - 2 KNOWS relationships
    """
    # TODO: Populate with standard test data once API is available
    return db
