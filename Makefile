SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTEST_K ?= ""
PYTEST_MARKERS ?= ""


first: help


# ------------------------------------------------------------------------------
# Build

env:  ## Create Python env
	poetry install


build:  ## Build package
	poetry build


upload-pypi:  ## Upload package to PyPI
	twine upload dist/*.tar.gz


upload-test:  ## Upload package to test PyPI
	twine upload --repository test dist/*.tar.gz


npm-install:  ##
	cd js; npm install


npm-dev:  ##
	cd js; npm run dev


npm-build:  ##
	cd js; npm run build


npm-clean:  ##
	cd js; npm run clean

# ------------------------------------------------------------------------------
# Testing

check:  ## Check linting
	isort --check-only --diff .
	black --check --diff .
	flake8


fmt:  ## Format source
	isort .
	black .


test:  ## Run tests
	pytest -k $(PYTEST_K) -m $(PYTEST_MARKERS)


test-all:  ## Run all tests
	pytest -k $(PYTEST_K)


report:  ## Generate coverage reports
	coverage xml
	coverage html

# ------------------------------------------------------------------------------
# Other


clean: npm-clean  ## Clean build files
	rm -rf build dist site htmlcov .pytest_cache .eggs
	rm -f .coverage coverage.xml
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
	rm -rf mkdocs_jupyter/tests/mkdocs/site


cleanall: clean  ## Clean everything


help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
