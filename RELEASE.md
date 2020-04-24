# Release

```
export VERSION=1.0.0

git commit --allow-empty -am "Release drivers version: ${VERSION}"
git tag -a ${VERSION} -m "${VERSION}"

make build
make upload-pypi

git push origin ${VERSION}
git push
```
