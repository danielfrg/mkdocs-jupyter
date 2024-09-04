# Contributing

## Development environment

Requirements:

- Python and uv
- NodeJS and pnpm

Create Python env and activate it:

```shell
uv sync
```

## Dev cycle

To change the styles

- `cd js`
- `pnpm install`
- `pnpm run build` or `npm run dev` for continuous build

Python:

Run `mkdocs` in one of the tests configurations:

- `cd src/mkdocs_jupyter/tests/mkdocs/`
- `uv run mkdocs serve -f material-with-nbs.yml`

Change styles and rebuild the site to see the changes

## Tests

```shell
just test
```

Check linting and format

```shell
just check
just fmt
```

## JupyterLab styles

We start from the JupyterLab styles with some minor modifications
to make them more integrated with the mkdocs themes.

We wrap those styles into the `.jupyter-wrapper` CSS class
to try to adapt with mkdocs theme specific CSS.

To update the original styles:

- Install `jupyterlab` Python package
- Copy the nbconvert CSS to `js/src/styles/`
- Look at the `CHANGE:` comments in that file and update accordingly
