.PHONY: help lint format type-check security test pre-push clean

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

lint:  ## Run ruff linter
	uv run ruff check .

format:  ## Format code with ruff
	uv run ruff format .

format-check:  ## Check code formatting
	uv run ruff format --check .

type-check:  ## Run mypy type checker
	uv run mypy src/graphforge --strict-optional --show-error-codes

security:  ## Run Bandit security scanner
	uv run bandit -c pyproject.toml -r src/

test:  ## Run all tests
	uv run pytest tests/

test-unit:  ## Run unit tests only
	uv run pytest tests/unit -v

test-integration:  ## Run integration tests only
	uv run pytest tests/integration -v

coverage:  ## Run tests with coverage measurement
	@echo "Running tests with coverage..."
	uv run pytest tests/unit tests/integration \
		--cov=src \
		--cov-branch \
		--cov-report=term-missing \
		--cov-report=xml \
		--cov-report=html \
		-n auto

test-analytics:  ## Run tests with analytics output (JUnit XML)
	@echo "Running tests with analytics output..."
	uv run pytest tests/unit tests/integration \
		--junitxml=test-results-local.xml \
		-v

check-coverage:  ## Validate coverage meets 85% threshold
	@echo "Checking coverage thresholds..."
	@uv run coverage report --fail-under=85 || \
		(echo "❌ Coverage below 85% threshold" && exit 1)
	@echo "✅ Coverage meets threshold"

coverage-strict:  ## Strict 90% coverage check for new features
	@echo "Checking strict coverage (90%)..."
	@uv run coverage report --fail-under=90 || \
		(echo "❌ Coverage below 90% - consider adding more tests" && exit 1)
	@echo "✅ Coverage meets strict threshold"

coverage-report:  ## Open HTML coverage report in browser
	@echo "Opening coverage report in browser..."
	@open htmlcov/index.html || xdg-open htmlcov/index.html || \
		echo "Coverage report generated at htmlcov/index.html"

coverage-diff:  ## Show coverage for changed files only
	@echo "Showing coverage for changed files..."
	@CHANGED_FILES=$$(git diff --name-only origin/main... | grep '\.py$$' || true); \
	if [ -z "$$CHANGED_FILES" ]; then \
		echo "ℹ️  No Python files changed"; \
	else \
		INCLUDE_PATTERN=$$(echo "$$CHANGED_FILES" | tr '\n' ',' | sed 's/,$$//'); \
		uv run coverage report --include="$$INCLUDE_PATTERN"; \
	fi

check-patch-coverage:  ## Validate patch coverage for changed files (90% threshold)
	@echo "Checking patch coverage for changed files..."
	@CHANGED_FILES=$$(git diff --name-only origin/main... | grep '^src/.*\.py$$' || true); \
	if [ -z "$$CHANGED_FILES" ]; then \
		echo "ℹ️  No source files changed - skipping patch coverage check"; \
	else \
		echo "Changed files:"; \
		echo "$$CHANGED_FILES" | sed 's/^/  - /'; \
		INCLUDE_PATTERN=$$(echo "$$CHANGED_FILES" | tr '\n' ',' | sed 's/,$$//'); \
		uv run coverage report --include="$$INCLUDE_PATTERN" --fail-under=90 || \
			(echo "❌ Patch coverage below 90% for changed files" && \
			 echo "   Run 'make coverage-report' to see detailed coverage" && \
			 exit 1); \
		echo "✅ Patch coverage meets 90% threshold"; \
	fi

pre-push: format-check lint type-check security coverage check-coverage check-patch-coverage  ## Run all pre-push checks (mirrors CI)
	@echo "✅ All pre-push checks passed!"

clean:  ## Clean up cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -f test-results*.xml coverage.xml 2>/dev/null || true
	rm -rf htmlcov/ 2>/dev/null || true
