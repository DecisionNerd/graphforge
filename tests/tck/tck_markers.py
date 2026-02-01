"""Pytest plugin for TCK compliance testing with supported/unsupported scenario marking.

This plugin:
1. Reads tck_config.yaml to determine which scenarios are supported
2. Marks scenarios as 'tck_supported' or 'tck_unsupported'
3. Applies xfail marker to unsupported scenarios (allow them to fail)
4. Collects statistics on TCK compliance

Usage:
    pytest tests/tck/ --tck-report
"""

from pathlib import Path

import pytest
import yaml


class TCKConfig:
    """TCK configuration manager."""

    def __init__(self, config_path: Path):
        """Load TCK configuration from YAML file."""
        with open(config_path) as f:
            self.config = yaml.safe_load(f)

        self.supported = self.config.get("supported", {})
        self.unsupported = self.config.get("unsupported", {})

    def is_supported(self, feature_path: str, scenario_name: str) -> bool:
        """Check if a scenario is marked as supported."""
        # Normalize feature path to relative path from features/official/
        if "/features/official/" in feature_path:
            relative_path = feature_path.split("/features/official/")[1]
        else:
            relative_path = Path(feature_path).name

        # Check if feature is in supported list
        feature_scenarios = self.supported.get(relative_path, [])

        if feature_scenarios == "*":
            # All scenarios in this feature are supported
            return True

        if isinstance(feature_scenarios, list):
            # Check if this specific scenario is supported
            return scenario_name in feature_scenarios

        return False

    def is_unsupported(self, feature_path: str, scenario_name: str) -> bool:
        """Check if a scenario is explicitly marked as unsupported."""
        if "/features/official/" in feature_path:
            relative_path = feature_path.split("/features/official/")[1]
        else:
            relative_path = Path(feature_path).name

        feature_scenarios = self.unsupported.get(relative_path, [])

        if feature_scenarios == "*":
            return True

        if isinstance(feature_scenarios, list):
            return scenario_name in feature_scenarios

        return False


class TCKReporter:
    """Collect and report TCK compliance statistics."""

    def __init__(self):
        """Initialize reporter."""
        self.total_scenarios = 0
        self.supported_scenarios = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.xfailed = 0
        self.supported_passed = 0
        self.supported_failed = 0

    def update_from_report(self, report: pytest.TestReport, is_supported: bool):
        """Update statistics from test report."""
        if report.when != "call":
            return

        self.total_scenarios += 1

        if is_supported:
            self.supported_scenarios += 1

        if report.passed:
            self.passed += 1
            if is_supported:
                self.supported_passed += 1
        elif report.failed:
            self.failed += 1
            if is_supported:
                self.supported_failed += 1
        elif report.skipped:
            if hasattr(report, "wasxfail"):
                self.xfailed += 1
            else:
                self.skipped += 1

    def get_summary(self) -> str:
        """Generate summary report."""
        lines = []
        lines.append("")
        lines.append("=" * 70)
        lines.append("openCypher TCK Compliance Report")
        lines.append("=" * 70)
        lines.append("")

        # Overall compliance
        if self.total_scenarios > 0:
            overall_pct = (self.passed / self.total_scenarios) * 100
        else:
            overall_pct = 0.0

        lines.append("Overall TCK Compliance:")
        lines.append(f"  Total scenarios:   {self.total_scenarios}")
        lines.append(f"  Passed:            {self.passed} ({overall_pct:.1f}%)")
        lines.append(f"  Failed:            {self.failed}")
        lines.append(f"  Expected failures: {self.xfailed}")
        lines.append(f"  Skipped:           {self.skipped}")
        lines.append("")

        # Supported scenarios compliance
        if self.supported_scenarios > 0:
            supported_pct = (self.supported_passed / self.supported_scenarios) * 100
        else:
            supported_pct = 0.0

        lines.append("Supported Scenarios (GraphForge Claims):")
        lines.append(f"  Total supported:   {self.supported_scenarios}")
        lines.append(f"  Passed:            {self.supported_passed} ({supported_pct:.1f}%)")
        lines.append(f"  Failed:            {self.supported_failed}")
        lines.append("")

        if self.supported_failed > 0:
            lines.append("⚠️  WARNING: Some supported scenarios failed!")
            lines.append("   GraphForge is not meeting its claimed compliance.")
        elif self.supported_scenarios > 0:
            lines.append(f"✓ All {self.supported_scenarios} supported scenarios passing!")

        lines.append("=" * 70)

        return "\n".join(lines)


# Global instances
_tck_config = None
_tck_reporter = None


def pytest_configure(config):
    """Initialize TCK markers and configuration."""
    config.addinivalue_line(
        "markers", "tck_supported: TCK scenario that GraphForge claims to support"
    )
    config.addinivalue_line(
        "markers", "tck_unsupported: TCK scenario that GraphForge does not support"
    )
    config.addinivalue_line("markers", "tck: openCypher TCK compliance test")

    # Load TCK configuration
    global _tck_config, _tck_reporter
    tck_dir = Path(__file__).parent
    config_path = tck_dir / "tck_config.yaml"

    if config_path.exists():
        _tck_config = TCKConfig(config_path)
        _tck_reporter = TCKReporter()
    else:
        print(f"Warning: TCK config not found at {config_path}")


def pytest_collection_modifyitems(config, items):
    """Mark TCK scenarios as supported/unsupported based on configuration."""
    if not _tck_config:
        return

    for item in items:
        # Only process items in the TCK directory
        if "/tests/tck/" not in str(item.fspath):
            continue

        # Get feature file path and scenario name
        feature_path = str(item.fspath)
        scenario_name = item.name

        # Clean up scenario name (pytest-bdd adds test_ prefix)
        if scenario_name.startswith("test_"):
            scenario_name = scenario_name[5:].replace("_", " ")

        # Mark all TCK tests
        item.add_marker(pytest.mark.tck)

        # Check if supported or unsupported
        if _tck_config.is_supported(feature_path, scenario_name):
            item.add_marker(pytest.mark.tck_supported)
        elif _tck_config.is_unsupported(feature_path, scenario_name):
            item.add_marker(pytest.mark.tck_unsupported)
            # Apply xfail to unsupported scenarios (allow them to fail)
            item.add_marker(
                pytest.mark.xfail(reason="Not yet supported by GraphForge", strict=False)
            )


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Collect statistics from test execution."""
    outcome = yield
    report = outcome.get_result()

    if not _tck_reporter:
        return

    # Only process TCK tests
    if not any(marker.name == "tck" for marker in item.iter_markers()):
        return

    # Check if this is a supported scenario
    is_supported = any(marker.name == "tck_supported" for marker in item.iter_markers())

    # Update statistics
    _tck_reporter.update_from_report(report, is_supported)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Display TCK compliance report at end of test run."""
    if not _tck_reporter:
        return

    # Only show report if we ran TCK tests
    if _tck_reporter.total_scenarios > 0:
        summary = _tck_reporter.get_summary()
        terminalreporter.write(summary)

        # Fail CI if supported scenarios failed
        if _tck_reporter.supported_failed > 0:
            terminalreporter.write_line(
                "\n❌ CI Status: FAILURE - Supported TCK scenarios failing\n", red=True, bold=True
            )
        elif _tck_reporter.supported_scenarios > 0:
            terminalreporter.write_line(
                "\n✓ CI Status: SUCCESS - All supported scenarios passing\n", green=True, bold=True
            )
