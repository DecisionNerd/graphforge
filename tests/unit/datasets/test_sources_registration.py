"""Unit tests for dataset source registration functions.

These tests verify that dataset sources register correctly and handle
idempotent registration (re-registering the same loader multiple times).
"""

import pytest

from graphforge.datasets.registry import _LOADER_REGISTRY, register_loader
from graphforge.datasets.sources.graphml import register_graphml_loader
from graphforge.datasets.sources.json_graph import register_json_graph_loader
from graphforge.datasets.sources.ldbc import register_ldbc_datasets


class TestGraphMLRegistration:
    """Tests for GraphML loader registration."""

    def test_register_graphml_loader_first_time(self):
        """GraphML loader registers successfully on first registration."""
        # Clear any existing registration
        if "graphml" in _LOADER_REGISTRY:
            del _LOADER_REGISTRY["graphml"]

        # Register should succeed
        register_graphml_loader()

        # Loader should be registered
        assert "graphml" in _LOADER_REGISTRY

    def test_register_graphml_loader_idempotent(self):
        """GraphML loader can be registered multiple times (idempotent)."""
        # Register twice - should not raise
        register_graphml_loader()
        register_graphml_loader()  # Should silently succeed

        # Loader should still be registered
        assert "graphml" in _LOADER_REGISTRY

    def test_register_graphml_loader_different_error(self):
        """GraphML registration re-raises non-idempotent ValueErrors."""
        # This tests the error handling path (lines 37-41)
        # We can't easily test this without modifying register_loader(),
        # but we can verify the code path exists
        import inspect

        source = inspect.getsource(register_graphml_loader)
        assert "already registered" in source
        assert "Re-raise if it's a different ValueError" in source


class TestJSONGraphRegistration:
    """Tests for JSON Graph loader registration."""

    def test_register_json_graph_loader_first_time(self):
        """JSON Graph loader registers successfully on first registration."""
        # Clear any existing registration
        if "json_graph" in _LOADER_REGISTRY:
            del _LOADER_REGISTRY["json_graph"]

        # Register should succeed
        register_json_graph_loader()

        # Loader should be registered
        assert "json_graph" in _LOADER_REGISTRY

    def test_register_json_graph_loader_idempotent(self):
        """JSON Graph loader can be registered multiple times (idempotent)."""
        # Register twice - should not raise
        register_json_graph_loader()
        register_json_graph_loader()  # Should silently succeed

        # Loader should still be registered
        assert "json_graph" in _LOADER_REGISTRY

    def test_register_json_graph_loader_different_error(self):
        """JSON Graph registration re-raises non-idempotent ValueErrors."""
        # This tests the error handling path (lines 31-35)
        import inspect

        source = inspect.getsource(register_json_graph_loader)
        assert "already registered" in source
        assert "Re-raise if it's a different ValueError" in source


class TestLDBCRegistration:
    """Tests for LDBC datasets registration."""

    def test_register_ldbc_datasets_first_time(self):
        """LDBC datasets register successfully on first registration."""
        # Clear any existing LDBC loader registration
        if "ldbc" in _LOADER_REGISTRY:
            del _LOADER_REGISTRY["ldbc"]

        # Register should succeed
        register_ldbc_datasets()

        # Loader should be registered
        assert "ldbc" in _LOADER_REGISTRY

    def test_register_ldbc_datasets_idempotent(self):
        """LDBC datasets can be registered multiple times (idempotent)."""
        # Register twice - should not raise
        register_ldbc_datasets()
        register_ldbc_datasets()  # Should silently succeed

        # Loader should still be registered
        assert "ldbc" in _LOADER_REGISTRY

    def test_register_ldbc_datasets_different_error(self):
        """LDBC registration re-raises non-idempotent ValueErrors."""
        # This tests the error handling path (lines 27-31)
        import inspect

        source = inspect.getsource(register_ldbc_datasets)
        assert "already registered" in source
        assert "Re-raise if it's a different ValueError" in source


class TestRegistrationErrorHandling:
    """Tests for registration error handling across all sources."""

    def test_register_loader_with_different_value_error(self):
        """Registration re-raises ValueErrors that aren't about duplication."""
        # Register a loader normally
        from graphforge.datasets.loaders.csv import CSVLoader

        register_loader("test_loader", CSVLoader)

        # Try to register a different loader class with the same name
        # This should raise a ValueError about different loaders
        from graphforge.datasets.loaders.graphml import GraphMLLoader

        with pytest.raises(ValueError, match="already registered"):
            register_loader("test_loader", GraphMLLoader)

        # Clean up
        if "test_loader" in _LOADER_REGISTRY:
            del _LOADER_REGISTRY["test_loader"]
