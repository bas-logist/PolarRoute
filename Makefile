.PHONY: install test test-all lint format type-check coverage clean docs docs-clean help

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install:  ## Install package with all dependencies
	pip install -e .
	@echo "PolarRoute installed in development mode."

test:  ## Run fast tests only
	pytest -m "not slow"

test-all:  ## Run all tests including slow ones
	pytest

lint:  ## Run linting checks
	ruff check polar_route/ tests/

format:  ## Format code with ruff
	ruff format polar_route/ tests/
	ruff check --fix polar_route/ tests/

coverage:  ## Generate coverage report (terminal and HTML)
	pytest --cov=polar_route --cov-report=term-missing --cov-report=html --cov-report=xml -m "not slow"
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
