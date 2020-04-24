SHELL := bash
.ONESHELL:
.SHELLFLAGS := -eu -o pipefail -c
.DELETE_ON_ERROR:
MAKEFLAGS += --warn-undefined-variables
MAKEFLAGS += --no-builtin-rules

all: help

.PHONY: build
build:  ## Build Python package
	python setup.py sdist

.PHONY: upload-pypi
upload-pypi:  ## Upload package to pypi
	twine upload dist/*.tar.gz

.PHONY: upload-test
upload-test:  ## Upload package to pypi test repository
	twine upload --repository testpypi dist/*.tar.gz

.PHONY: clean
clean:  ## Clean build files
	@rm -rf dist __pycache__

.PHONY: cleanall
cleanall: clean  ## Clean build files
	@rm -rf *.egg-info

.PHONY: env
env:  ## Create virtualenv
	conda env create

.PHONY: help
help:  ## Show this help menu
	@grep -E '^[0-9a-zA-Z_-]+:.*?##.*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?##"; OFS="\t\t"}; {printf "\033[36m%-30s\033[0m %s\n", $$1, ($$2==""?"":$$2)}'
