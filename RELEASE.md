# Releasing

## Upload to PyPI

- Update version on `__init__.py`
- Update version on `pyproject.toml`
- Update `CHANGELOG.md`

```shell
export VERSION=1.0.0

# Optional reset
task cleanall resetjs
task npm-install

# Build
task npm-build pkg
task upload-pypi

git commit -am "Release ${VERSION}" --allow-empty
git tag ${VERSION}

git push origin ${VERSION}
git push
```
