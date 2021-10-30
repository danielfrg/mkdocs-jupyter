# Contributing

## Development environment

Create Python env

```shell
make env
```

## JupyterLab styles

We use the JuptyerLab styles with some minor modifications
to make them more integrated with the mkdocs themes.

We wrap those styles into the `.jupyter-wrapper` CSS class
to make not break regular theme CSS.

To update the original styles:

- Install `jupyterlab` Python package
- Copy the nbconvert CSS to `js/src/jupyter-lab.scss`
- Look at the `CHANGE:` comments in that file and update accordingly

## Dev cycle

To change the styles

- `cd js`
- `npm install`
- `npm run dev`

In another terminal run `mkdocs`, for example one of the tests

- `cd mkdocs_jupyter/tests/mkdocs/`
- `mkdocs serve -f material-with-nbs.yml`
- Change styles and rebuild the site to see the changes

## Tests

```shell
make test
```

Check linting and format

```shell
make check
make fmt
```
