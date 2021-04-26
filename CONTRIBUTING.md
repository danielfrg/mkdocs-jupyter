# Contributing

## Development environment

Create Python env

```
make env
conda activate mkdocs-jupyter
```

Install package for development

```
make develop
```

## JupyterLab styles

We use the original JuptyerLab styles for the notebook plus some modifications
to make them more integrated with the mkdocs themes.

We also wrap all notebook content and styles into a `.jupyter-wrapper` CSS class
to make not break other theme features/CSS.

To update the original styles:

-   Install `jupyterlab` Python package
-   Copy the nbconvert templates to `js/src/jlab/`
-   Rename the `.css` files to `.scss`
-   Look at the `CHANGES` comments in styles we have here and update accordingly

## Dev cycle

To change the styles

-   `cd js`
-   `npm install`
-   `npm run dev`

In another terminal run `mkdocs`, for example one of the tests

-   `cd mkdocs_jupyter/tests/mkdocs/`
-   `mkdocs serve -f material-with-nbs.yml`
-   Change styles and rebuild the site to see the changes

## Tests

```
make test
```

Check linting and format

```
make check
make fmt
```
