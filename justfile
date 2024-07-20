default:
  just --list

build:
  rye build

check:
  isort . --check-only --diff
  black . --check
  ruff check mkdocs_jupyter
  flake8

fmt:
  isort .
  black .
  ruff check --fix mkdocs_jupyter

test FILTER="":
  rye run pytest -k "{{FILTER}}"

test-all:
  rye run pytest .

report:
  coverage xml
  coverage html

publish:
  rye publish

docs-build:
  mkdocs build

# ------------------------------------------------------------------------------
# Javascript

js-install:
  cd js; pnpm install

js-build:
  cd js; pnpm run build

js-dev:
  cd js; pnpm run dev

js-clean:
  cd js; pnpm run clean

