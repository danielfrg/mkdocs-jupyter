default:
  just --list

build:
  uv run pyproject-build --installer uv

check:
  uv run isort . --check-only --diff
  uv run ruff check
  uv run flake8

fmt:
  uv run isort .
  uv run ruff format

test FILTER="":
  uv run pytest -k "{{FILTER}}"

report:
  uv run coverage xml
  uv run coverage html

publish:
  uv publish

docs-build:
  cd demo; uv run mkdocs build

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

