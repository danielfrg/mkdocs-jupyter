# mkdocs-jupyter: Use Jupyter Notebooks in mkdocs

[![pypi](https://badge.fury.io/py/mkdocs-jupyter.svg)](https://pypi.org/project/mkdocs-jupyter/)
[![build](https://github.com/danielfrg/mkdocs-jupyter/workflows/test/badge.svg)](https://github.com/danielfrg/mkdocs-jupyter/actions/workflows/test.yml)
[![coverage](https://codecov.io/gh/danielfrg/mkdocs-jupyter/branch/master/graph/badge.svg)](https://codecov.io/gh/danielfrg/mkdocs-jupyter?branch=master)
[![license](https://img.shields.io/:license-Apache%202-blue.svg)](https://github.com/danielfrg/mkdocs-jupyter/blob/master/LICENSE.txt)

- Add Jupyter Notebooks directly to the mkdocs navigation
- Support for multiple formats:
    - `.ipynb` and `.py` files (using [jupytext](https://github.com/mwouts/jupytext))
- Same style as regular Jupyter Notebooks
- Option to execute the notebook before converting
- Support for [ipywidgets](https://github.com/jupyter-widgets/ipywidgets)
- Support for mkdocs TOC
- Option to include notebook source

<a href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png"><img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png" alt="mkdocs-jupyter default theme"  width="410"></a>
<a href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png"><img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png" alt="mkdocs-jupyter material theme"  width="410"></a>

## Usage

```
pip install mkdocs-jupyter
```

In your `mkdocs.yml`:

```
nav:
- Home: index.md
- Notebook page: notebook.ipynb
- Python file: python_script.py

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

### Kernel Name

By default the plugin will use the kernel specified in the notebook to execute it. You can specify a custom kernel name to use for all the notebooks:

```
plugins:
  - mkdocs-jupyter:
      kernel_name: python3
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

For example in `mkdocs-material`
(see [customization](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks)),
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

![Download Noteboon button](https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/download-button.png)

## Styles

This extensions includes some CSS styles to make the Notebook look "decent" inside a generic
mkdoc theme but in general some extra customization needs to be done to make
the Jupyter Notebook based pages look as good and native as the markdown ones.
This is usually simple CSS tweaks.

### Material theme

For popular the `mkdocs-material` please take a look at their [customization docs](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks))

Create a `main.html` file like:

```
{% extends "base.html" %}

{% block content %}
{{ super() }}

<style>
    .jp-RenderedHTMLCommon p {
        font-size: .8rem;
        line-height: 1.6;
    }

    .jp-RenderedHTMLCommon li {
        font-size: .8rem;
        line-height: 1.6;
    }

    .jp-RenderedHTMLCommon h1 {
        margin: 0 0 1.25em;
        color: var(--md-default-fg-color--light);
        font-weight: 300;
        font-size: 2em;
        line-height: 1.3;
        letter-spacing: -0.01em;
    }

    .jp-RenderedHTMLCommon h2 {
        margin: 1.6em 0 .64em;
        font-weight: 300;
        font-size: 1.965em;
        line-height: 1.4;
        letter-spacing: -0.01em;
    }

    .jp-RenderedHTMLCommon h3 {
        margin: 1.6em 0 .8em;
        font-weight: 400;
        font-size: 1.57em;
        line-height: 1.5;
        letter-spacing: -0.01em;
    }

    .jp-RenderedHTMLCommon hr {
        border: none;
    }
</style>
{% endblock content %}
```
