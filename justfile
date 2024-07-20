default:
  just --list

build:
  rye build

check:
  rye run isort . --check-only --diff
  rye run black . --check
  rye run ruff check mkdocs_jupyter
  rye run flake8

fmt:
  rye run isort .
  rye run ruff format

test FILTER="":
  rye run pytest -k "{{FILTER}}"

report:
  rye run coverage xml
  rue run coverage html

publish:
  rye publish

docs-build:
  cd demo; mkdocs build

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

