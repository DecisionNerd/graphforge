.PHONY: help lint format type-check test pre-push clean

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

test:  ## Run all tests
	uv run pytest tests/

test-unit:  ## Run unit tests only
	uv run pytest tests/unit -v

test-integration:  ## Run integration tests only
	uv run pytest tests/integration -v

pre-push: format-check lint type-check test-unit test-integration  ## Run all pre-push checks (mirrors CI)
	@echo "✅ All pre-push checks passed!"

clean:  ## Clean up cache files
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
