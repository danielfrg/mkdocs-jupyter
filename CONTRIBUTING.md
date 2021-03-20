# Contrinuting

## Dev environment

The development is based on conda on the `environment.yml` file.
To createand activate the environment:

```
make env
conda activate mkdocs-jupyter
```

After that install the package in editable mode using:

```
make develop
```

## Testing

```
# Check linting and format
make check
make fmt

# Run tests
make test
```
