# mkdocs-jupyter: Use Jupyter Notebooks in mkdocs

[![PyPI](https://badge.fury.io/py/mkdocs-jupyter.svg)](https://pypi.org/project/mkdocs-jupyter/)
[![Testing](https://github.com/danielfrg/mkdocs-jupyter/workflows/test/badge.svg)](https://github.com/danielfrg/mkdocs-jupyter/actions)
[![Coverage Status](https://codecov.io/gh/danielfrg/mkdocs-jupyter/branch/master/graph/badge.svg)](https://codecov.io/gh/danielfrg/mkdocs-jupyter?branch=master)
[![License](http://img.shields.io/:license-Apache%202-blue.svg)](https://github.com/danielfrg/mkdocs-jupyter/blob/master/LICENSE.txt)

- Add Jupyter Notebooks directly to the mkdocs navigation
- Feel and look the regular Jupyter Notebook style inside mkdocs pages
- Option to execute the notebook before converting
- Show ipywidgets (requires execution of the notebook)
- Support for mkdocs TOC

![mkdocs-jupyter](https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/screenshot.png)

## Usage

```
pip install mkdocs-jupyter
```

In your `mkdocs.yml`:

```
nav:
- Notebook: notebook.ipynb

plugins:
  - mkdocs-jupyter
```
