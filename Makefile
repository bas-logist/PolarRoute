.PHONY: install test test-all benchmark benchmark-check benchmark-update-baseline lint format type-check coverage clean docs docs-clean help

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package with all dependencies
	pip install -e .
	@echo "PolarRoute installed in development mode."

test:  ## Run fast tests only
	pytest -m "not slow and not benchmark"

test-all:  ## Run all tests including slow ones
	pytest -m "not benchmark"

benchmark:  ## Run performance benchmark tests
	pytest -m benchmark --benchmark-only

benchmark-check:  ## Run benchmarks and compare against the committed baseline (.github/benchmark-baseline.json), failing on regression (use THRESHOLD=10 for 10%). Same check CI runs.
	@if [ -f .github/benchmark-baseline.json ]; then \
		pytest -m benchmark --benchmark-only --benchmark-json=benchmark-result.json \
			--benchmark-compare=.github/benchmark-baseline.json \
			--benchmark-compare-fail=mean:$(or $(THRESHOLD),10)% ; \
	else \
		pytest -m benchmark --benchmark-only --benchmark-json=benchmark-result.json ; \
	fi

benchmark-update-baseline:  ## Regenerate .github/benchmark-baseline.json from a fresh benchmark run (commit the result)
	pytest -m benchmark --benchmark-only --benchmark-json=.github/benchmark-baseline.json
	@echo "Updated .github/benchmark-baseline.json - review and commit it."

lint:  ## Run linting checks
	ruff check polar_route/ tests/

format:  ## Format code with ruff
	ruff format polar_route/ tests/
	ruff check --fix polar_route/ tests/

coverage:  ## Generate coverage report (terminal and HTML)
	pytest --cov=polar_route --cov-report=term-missing --cov-report=html --cov-report=xml -m "not slow and not benchmark"
	@echo "\nCoverage report generated. Open htmlcov/index.html to view the HTML report."

clean:  ## Clean build artifacts and cache
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf coverage.xml
	rm -rf site/
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Clean complete."

docs:  ## Build documentation
	mkdocs build
	@echo "Documentation built in site/"

docs-clean:  ## Clean documentation build artifacts
	rm -rf site/
	@echo "Documentation build artifacts cleaned."
