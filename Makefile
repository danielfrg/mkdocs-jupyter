SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PYTEST_K ?= ""
PYTEST_MARKERS ?= ""


first: help


all: npm-build pkg  ## Build JS and Python


# ------------------------------------------------------------------------------
# Python

env:  ## Create Python env
	poetry install --with dev --with test


pkg:  ## Build package
	poetry build


check:  ## Check linting
	isort --check-only --diff .
	black --check --diff .
	flake8


fmt:  ## Format source
	isort .
	black .


test-%:  ## Run tests
	pytest -k $(PYTEST_K) -m $(subst test-,,$@)


test-all:  ## Run all tests
	pytest -k $(PYTEST_K) -m $(PYTEST_MARKERS)


report:  ## Generate coverage reports
	coverage xml
	coverage html


upload-pypi:  ## Upload package to PyPI
	twine upload dist/*.tar.gz


cleanpython:  ## Clean Python build files
	rm -rf .eggs .pytest_cache dist htmlcov test-results
	rm -f .coverage coverage.xml
	find . -type f -name '*.py[co]' -delete
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .ipynb_checkpoints -exec rm -rf {} +


resetpython: cleanpython  ## Reset Python
	rm -rf .venv


# ------------------------------------------------------------------------------
# Javascript

npm-install:  ## JS: Install dependencies
	cd $(CURDIR)/js; npm install
npm-i: npm-install


npm-build:  ## JS: Build
	cd $(CURDIR)/js; npm run build


npm-dev:  ## JS: Build dev mode
	cd $(CURDIR)/js; npm run dev


cleanjs:  ## JS: Clean build files
	cd $(CURDIR)/js; npm run clean
	cd $(CURDIR)/mkdocs_jupyter/templates/mkdocs_html/assets/; rm -rf mkdocs-jupyter.*


resetjs:  ## JS: Reset
	cd $(CURDIR)/js; npm run reset


# ------------------------------------------------------------------------------
# Other

cleanall: cleanjs cleanpython  ## Clean everything


help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
