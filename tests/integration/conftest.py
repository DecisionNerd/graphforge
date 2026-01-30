"""Fixtures specific to integration tests."""

import pytest


@pytest.fixture
def populated_db(db):
    """Provides a database with realistic test data for integration tests.

    This fixture will be implemented once the GraphForge API is available.
    """
    # TODO: Add realistic multi-node, multi-relationship graph
    return db
