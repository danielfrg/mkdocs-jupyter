default:
  just --list

build:
  uv run pyproject-build --installer uv

check:
  uv run ruff check
  uv run ruff format --check

fmt:
  uv run ruff check --select I --fix
  uv run ruff format

test FILTER="":
  uv run pytest -k "{{FILTER}}"

report:
  uv run coverage xml
  uv run coverage html

publish:
  uv run twine upload dist/*

docs-build:
  cd demo; uv run mkdocs build

# ------------------------------------------------------------------------------
# Javascript

js-install:
  cd js; pnpm install --frozen-lockfile

js-build:
  cd js; pnpm run build

js-dev:
  cd js; pnpm run dev

js-clean:
  cd js; pnpm run clean

