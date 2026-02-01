"""Bind official openCypher TCK feature files to step definitions."""

from pytest_bdd import scenarios

# Bind official TCK scenarios
# This will discover all .feature files in features/official/ and create
# test functions for each scenario, which will then be marked by tck_markers.py
scenarios("features/official/")
