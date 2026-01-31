"""Bind official openCypher TCK feature files to step definitions.

Due to some syntax issues in some TCK feature files (Match5, Match7 start with
'And' steps), we bind features we know work. More will be added as issues are resolved.
"""
from pytest_bdd import scenarios

# Bind well-formed TCK scenarios
scenarios('features/official/clauses/match/Match1.feature')
scenarios('features/official/clauses/create/Create1.feature')
scenarios('features/official/clauses/delete/Delete1.feature')
scenarios('features/official/clauses/set/Set1.feature')
