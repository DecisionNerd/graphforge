#!/usr/bin/env python
"""Debug script to diagnose dataset registration issues."""

from pathlib import Path
import sys

print("=" * 60)
print("Python version:", sys.version)
print("Python executable:", sys.executable)
print("=" * 60)

try:
    import graphforge

    print(f"graphforge imported from: {graphforge.__file__}")
    print(f"graphforge.__version__: {graphforge.__version__}")
except Exception as e:
    print(f"ERROR importing graphforge: {e}")
    sys.exit(1)

print("=" * 60)

try:
    import graphforge.datasets

    print(f"graphforge.datasets imported from: {graphforge.datasets.__file__}")
except Exception as e:
    print(f"ERROR importing graphforge.datasets: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("=" * 60)

# Check if data directory exists
try:
    datasets_path = Path(graphforge.datasets.__file__).parent
    data_dir = datasets_path / "data"
    print(f"Datasets path: {datasets_path}")
    print(f"Data directory: {data_dir}")
    print(f"Data directory exists: {data_dir.exists()}")

    if data_dir.exists():
        print(f"Data directory contents: {list(data_dir.iterdir())}")
        snap_json = data_dir / "snap.json"
        print(f"snap.json exists: {snap_json.exists()}")
        if snap_json.exists():
            print(f"snap.json size: {snap_json.stat().st_size} bytes")
except Exception as e:
    print(f"ERROR checking data directory: {e}")
    import traceback

    traceback.print_exc()

print("=" * 60)

try:
    import graphforge.datasets.sources

    print("graphforge.datasets.sources imported successfully")
except Exception as e:
    print(f"ERROR importing graphforge.datasets.sources: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("=" * 60)

try:
    from graphforge.datasets import list_datasets

    datasets = list_datasets()
    print(f"Total datasets registered: {len(datasets)}")

    snap_datasets = [d for d in datasets if d.name.startswith("snap-")]
    print(f"SNAP datasets registered: {len(snap_datasets)}")
    if snap_datasets:
        print(f"First 5 SNAP datasets: {[d.name for d in snap_datasets[:5]]}")
    else:
        print("ERROR: No SNAP datasets found!")

except Exception as e:
    print(f"ERROR listing datasets: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

print("=" * 60)
print("SUCCESS: All checks passed")
