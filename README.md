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
- Include notebook source

<a href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png"><img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png" alt="mkdocs-jupyter default theme"  width="410"></a>
<a href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png"><img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png" alt="mkdocs-jupyter material theme"  width="410"></a>

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

## Options

### Execute Notebook

You can tell the plugin to execute the notebook before converting, default is `False`:

```
plugins:
  - mkdocs-jupyter:
      execute: True
```

### Download notebook link

You can tell the plugin to include the notebook source to make it easy to show
a download button in the theme, default is `False`:

```
plugins:
  - mkdocs-jupyter:
      include_source: True
```

This setting will also create a `page.nb_url` value that you can use in your theme
to make a link in each page.

For example in `mkdocs-material` (see [customization](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks)),
you can create a `main.html` file like this:

```
{% extends "base.html" %}

{% block content %}
{% if page.nb_url %}
    <a href="{{ page.nb_url }}" title="Download Notebook" class="md-content__button md-icon">
        {% include ".icons/material/download.svg" %}
    </a>
{% endif %}

{{ super() }}
{% endblock content %}
```

With this result:

![Download Noteboon button](https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/download-button.png)
