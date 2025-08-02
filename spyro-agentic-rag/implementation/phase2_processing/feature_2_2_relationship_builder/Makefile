.PHONY: install test test-coverage lint format clean run-example

# Install dependencies
install:
	pip install -r requirements.txt
	python -m spacy download en_core_web_sm || true

# Run tests
test:
	python -m pytest

# Run tests with coverage
test-coverage:
	python -m pytest --cov=src --cov-report=html --cov-report=term

# Run linting
lint:
	flake8 src tests --max-line-length=100 --ignore=E501,W503
	mypy src --ignore-missing-imports

# Format code
format:
	black src tests
	isort src tests

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

# Run example
run-example:
	python examples/basic_usage.py

# Development setup
dev: install
	pip install -r requirements-dev.txt

# Build documentation
docs:
	cd docs && make html

# Run all checks
check: lint test

# Create distribution
dist: clean
	python setup.py sdist bdist_wheel