SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

PWD := $(shell pwd)
TEST_FILTER ?= ""


first: help

.PHONY: clean
clean:  ## Clean build files
	@rm -rf build dist site htmlcov .pytest_cache .eggs
	@rm -f .coverage coverage.xml mkdocs_jupyter/_generated_version.py
	@find . -type f -name '*.py[co]' -delete
	@find . -type d -name __pycache__ -exec rm -rf {} +
	@find . -type d -name .ipynb_checkpoints -exec rm -rf {} +


.PHONY: cleanall
cleanall: clean   ## Clean everything
	@rm -rf *.egg-info


.PHONY: help
help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'


# ------------------------------------------------------------------------------
# Package build, test and docs

.PHONY: env  ## Create dev environment
env:
	conda env create


.PHONY: develop
develop:  ## Install package for development
	python -m pip install --no-build-isolation -e .


.PHONY: build
build: package  ## Build everything


.PHONY: package
package:  ## Build Python package (sdist)
	python setup.py sdist


.PHONY: check
check:  ## Check linting
	# @flake8 mkdocs_jupyter
	@isort --check-only --diff --recursive --project mkdocs_jupyter --section-default THIRDPARTY mkdocs_jupyter .
	@black --check mkdocs_jupyter .


.PHONY: fmt
fmt:  ## Format source
	@isort --recursive --project mkdocs_jupyter --section-default THIRDPARTY mkdocs_jupyter .
	@black mkdocs_jupyter .


.PHONY: upload-pypi
upload-pypi:  ## Upload package to PyPI
	twine upload dist/*.tar.gz


.PHONY: upload-test
upload-test:  ## Upload package to test PyPI
	twine upload --repository testpypi dist/*.tar.gz


.PHONY: test
test:  ## Run tests
	pytest -s -vv mkdocs_jupyter/tests -k $(TEST_FILTER)


.PHONY: docs
docs:  ## Build mkdocs
	mkdocs build --config-file $(CURDIR)/mkdocs.yml


.PHONY: serve-docs
serve-docs:  ## Serve docs
	mkdocs serve


.PHONY: netlify
netlify:  ## Build docs on Netlify
	$(MAKE) docs

# ------------------------------------------------------------------------------
# Project specific
