"""Bind official openCypher TCK feature files to step definitions."""

from pathlib import Path

from pytest_bdd import exceptions, scenarios

# List of feature files with Gherkin syntax issues (upstream TCK problems)
PROBLEMATIC_FEATURES = {
    "clauses/match/Match5.feature",  # Has "And" as first step (invalid Gherkin)
}

# Get all feature files
features_dir = Path(__file__).parent / "features" / "official"
all_features = [
    f"features/official/{f.relative_to(features_dir)}"
    for f in features_dir.rglob("*.feature")
    if str(f.relative_to(features_dir)) not in PROBLEMATIC_FEATURES
]

# Bind official TCK scenarios (excluding problematic ones)
for feature_path in all_features:
    try:
        scenarios(feature_path)
    except (exceptions.NoScenariosFound, exceptions.StepError):
        # Skip files with no scenarios or Gherkin syntax errors
        pass
