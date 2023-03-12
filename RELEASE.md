# Releasing

## Upload to PyPI

- Update version on `__about__.py`
- Update `CHANGELOG.md`

```shell
export VERSION=1.0.0

# Build
task npm-build pkg
task upload-pypi

git commit -am "Release ${VERSION}" --allow-empty
git tag ${VERSION}

git push origin ${VERSION}
git push
```
