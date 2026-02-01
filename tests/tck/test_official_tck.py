"""Bind ALL official openCypher TCK feature files to step definitions.

This discovers and runs ALL valid TCK feature files to measure true compliance.

Note: Some feature files (Match5, Match7) have Gherkin syntax issues (scenarios
starting with 'And' steps) that pytest-bdd cannot parse. These are skipped.
"""

from pytest_bdd import scenarios

# Bind ALL clause features
scenarios("features/official/clauses/call/")
scenarios("features/official/clauses/create/")
scenarios("features/official/clauses/delete/")
scenarios("features/official/clauses/match-where/")

# Match features (skip Match5, Match7 - they have 'And' as first step)
scenarios("features/official/clauses/match/Match1.feature")
scenarios("features/official/clauses/match/Match2.feature")
scenarios("features/official/clauses/match/Match3.feature")
scenarios("features/official/clauses/match/Match4.feature")
# Match5 - SKIPPED (parser error: And as first step)
scenarios("features/official/clauses/match/Match6.feature")
# Match7 - SKIPPED (parser error: And as first step)
scenarios("features/official/clauses/match/Match8.feature")
scenarios("features/official/clauses/match/Match9.feature")

scenarios("features/official/clauses/merge/")
scenarios("features/official/clauses/remove/")
scenarios("features/official/clauses/return/")
scenarios("features/official/clauses/return-orderby/")
scenarios("features/official/clauses/return-skip-limit/")
scenarios("features/official/clauses/set/")
scenarios("features/official/clauses/union/")
scenarios("features/official/clauses/unwind/")
scenarios("features/official/clauses/with/")
scenarios("features/official/clauses/with-orderBy/")
scenarios("features/official/clauses/with-skip-limit/")
scenarios("features/official/clauses/with-where/")

# Bind ALL expression features
scenarios("features/official/expressions/aggregation/")
scenarios("features/official/expressions/boolean/")
scenarios("features/official/expressions/comparison/")
scenarios("features/official/expressions/conditional/")
scenarios("features/official/expressions/existentialSubqueries/")
scenarios("features/official/expressions/graph/")
scenarios("features/official/expressions/list/")
scenarios("features/official/expressions/literals/")
scenarios("features/official/expressions/map/")
scenarios("features/official/expressions/mathematical/")
scenarios("features/official/expressions/null/")
scenarios("features/official/expressions/path/")
scenarios("features/official/expressions/pattern/")
scenarios("features/official/expressions/precedence/")
scenarios("features/official/expressions/quantifier/")
scenarios("features/official/expressions/string/")
scenarios("features/official/expressions/temporal/")
scenarios("features/official/expressions/typeConversion/")

# Bind use case features
scenarios("features/official/useCases/")
