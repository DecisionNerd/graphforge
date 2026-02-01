#!/usr/bin/env python3
"""Download official openCypher TCK feature files and named graphs.

This script downloads the complete TCK test suite from the openCypher
repository and organizes it for local testing.
"""

import json
from pathlib import Path
import sys
from urllib.request import urlopen

GITHUB_API = "https://api.github.com"
GITHUB_RAW = "https://raw.githubusercontent.com"
REPO = "opencypher/openCypher"
BRANCH = "main"
TCK_PATH = "tck"


def download_file(url: str, dest: Path) -> None:
    """Download a file from URL to destination path."""
    print(f"Downloading: {dest.name}")
    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        with urlopen(url) as response:
            content = response.read()
            dest.write_bytes(content)
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        raise


def get_tree(path: str = "") -> list[dict]:
    """Get directory tree from GitHub API."""
    url = f"{GITHUB_API}/repos/{REPO}/contents/{TCK_PATH}/{path}"
    print(f"Fetching: {url}")

    try:
        with urlopen(url) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"  ERROR: {e}", file=sys.stderr)
        return []


def download_directory(remote_path: str, local_base: Path) -> int:
    """Recursively download a directory from the TCK repository."""
    count = 0
    items = get_tree(remote_path)

    for item in items:
        name = item["name"]
        item_type = item["type"]

        if item_type == "file":
            # Download file
            raw_url = f"{GITHUB_RAW}/{REPO}/{BRANCH}/{TCK_PATH}/{remote_path}/{name}"
            local_path = local_base / remote_path / name
            download_file(raw_url, local_path)
            count += 1

        elif item_type == "dir":
            # Recurse into subdirectory
            subdir_path = f"{remote_path}/{name}" if remote_path else name
            count += download_directory(subdir_path, local_base)

    return count


def main():
    """Download TCK feature files and named graphs."""
    script_dir = Path(__file__).parent
    official_dir = script_dir / "features" / "official"
    graphs_dir = script_dir / "graphs"

    print("=" * 70)
    print("Downloading openCypher TCK Test Suite")
    print("=" * 70)
    print()

    # Download feature files
    print("Downloading feature files...")
    feature_count = download_directory("features", official_dir.parent)
    print(f"\n✓ Downloaded {feature_count} feature files\n")

    # Download named graphs
    print("Downloading named graphs...")
    graph_count = download_directory("graphs", graphs_dir.parent)
    print(f"\n✓ Downloaded {graph_count} graph files\n")

    print("=" * 70)
    print("TCK download complete!")
    print(f"  Feature files: {official_dir}")
    print(f"  Named graphs: {graphs_dir}")
    print("=" * 70)


if __name__ == "__main__":
    main()
