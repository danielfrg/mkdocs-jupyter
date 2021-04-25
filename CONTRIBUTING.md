# Contributing

## Development environment

Create Python env

```
make env
conda activate mkdocs-jupyter
```

Install package for developmentt

```
make develop
```

## JupyterLab theme

The way this work is that we use the original JupyterLab nbconvert theme
and wrap it into a `.jupyter-wrapper` class using SCSS.

To update the theme:

-   Install `jupyterlab` Python package
-   Copy the nbconvert templates to `js/src/jlab/`
-   Rename the `.css` files to `.scss`

To run this in dev mode, cd to `js`:

-   `npm install`
-   `npm run dev`

## Tests

````
make test
```

Check linting and format

```
make check
make fmt
```
````
