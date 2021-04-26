SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

TEST_FILTER ?= ""
TEST_MARKERS ?= ""


first: help


# ------------------------------------------------------------------------------
# Build

env:  ## Create Python env
	mamba env create


develop:  ## Install package for development
	python -m pip install --no-build-isolation -e .


build:  ## Build package
	python setup.py sdist


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
	flake8
	isort . --project mkdocs_jupyter --check-only --diff
	black . --check


fmt:  ## Format source
	isort . --project mkdocs_jupyter
	black .


test:  ## Run tests
	pytest -k $(TEST_FILTER) -m $(TEST_MARKERS)


test-all:  ## Run all tests
	pytest -k $(TEST_FILTER)


report:  ## Generate coverage reports
	coverage xml
	coverage html


# ------------------------------------------------------------------------------
# Other

clean:  ## Clean build files
	rm -rf build dist site htmlcov .pytest_cache .eggs
	rm -f .coverage coverage.xml mkdocs_jupyter/_generated_version.py
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +
	rm -rf mkdocs_jupyter/tests/site


cleanall: clean   ## Clean everything
	rm -rf *.egg-info


help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
