<p align="center">
    <img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/main/docs/logo.png" width="450px">
</p>

<p align="center">
    <a href="https://pypi.org/project/mkdocs-jupyter/">
        <img src="https://badge.fury.io/py/mkdocs-jupyter.svg">
    </a>
    <a href="https://github.com/danielfrg/mkdocs-jupyter/actions/workflows/test.yml">
        <img src="https://github.com/danielfrg/mkdocs-jupyter/workflows/test/badge.svg">
    </a>
    <a href="https://codecov.io/gh/danielfrg/mkdocs-jupyter?branch=main">
        <img src="https://codecov.io/gh/danielfrg/mkdocs-jupyter/branch/main/graph/badge.svg">
    </a>
    <a href="http://github.com/danielfrg/mkdocs-jupyter/blob/main/LICENSE.txt">
        <img src="https://img.shields.io/:license-Apache%202-blue.svg">
    </a>
</p>


# mkdocs-jupyter: Use Jupyter Notebooks in mkdocs

- Add Jupyter Notebooks directly to the mkdocs navigation
- Support for multiple formats:
  - `.ipynb` and `.py` files (using [jupytext](https://github.com/mwouts/jupytext))
- Same style as regular Jupyter Notebooks
  - Support Jupyter Themes
- Option to execute the notebook before converting
- Support for [ipywidgets](https://github.com/jupyter-widgets/ipywidgets)
- Support for mkdocs TOC
- Option to include notebook source

<a href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png"><img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png" alt="mkdocs-jupyter default theme"  width="410"></a>
<a href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png"><img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png" alt="mkdocs-jupyter material theme"  width="410"></a>

## Installation

```shell
pip install mkdocs-jupyter
```

## Configuration

In the `mkdocs.yml` use Jupyter notebooks (`.ipynb`) or Python scripts (`.py`) as pages:

```yaml
nav:
- Home: index.md
- Notebook page: notebook.ipynb
- Python file: python_script.py

plugins:
  - mkdocs-jupyter
```

### Titles and Table of Contents

The first h1 header (`#`) in your notebook will be used as the title.

```md
# This H1 header will be the the title.
```

This can be turned off in the configuration (in which case the filename will be used as title):

```yaml
plugins:
  - mkdocs-jupyter:
      ignore_h1_titles: True
```

In order to see the table of contents you need to maintain a hierarchical headers structure in your notebooks.
You must use h2 headers (`##`) and not h1 (`#`)

```md
## This H2 title will show in the table of contents
```

If you want to **nest headers** in the TOC you need to add additional levels later
in the same markdown cell or new bottom markdown cells:

```md
## This header will show as top level in the table of contents

<content>

### This one will be displayed inside the above level
```

### Including or Ignoring Files

You can control which files are included or ignored via lists of glob patterns:

```yaml
plugins:
  - mkdocs-jupyter:
      include: ["*.ipynb"]  # Default: ["*.py", "*.ipynb"]
      ignore: ["some-irrelevant-files/*.ipynb"]
```

### Execute Notebook

You can tell the plugin to execute the notebook before converting, default is `False`:

```yaml
plugins:
  - mkdocs-jupyter:
      execute: True
```

You can tell the plugin to ignore the execution of some files (with glob matching):

```yaml
plugins:
  - mkdocs-jupyter:
      execute_ignore: "my-secret-files/*.ipynb"
```

#### Kernel

By default the plugin will use the kernel specified in the notebook to execute it.
You can specify a custom kernel name to use for all the notebooks:

```yaml
plugins:
  - mkdocs-jupyter:
      kernel_name: python3
```

### Jupyter themes

You can configure the different Jupyter themes.
For example if using material with `slate` color scheme you can use the Jupyter Lab `dark` theme:

```yml
plugins:
  - mkdocs-jupyter:
      theme: dark

theme:
  name: material
  palette:
    scheme: slate
```

### Download notebook link

You can tell the plugin to include the notebook source to make it easy to show
a download button in the theme, default is `False`:

```yml
plugins:
  - mkdocs-jupyter:
      include_source: True
```

This setting will also create a `page.nb_url` value that you can use in your theme
to make a link in each page.

For example in `mkdocs-material`
(see [customization](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks)),
you can create a `main.html` file like this:

```jinja
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

![Download Notebook button](https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/download-button.png)

### Styles

This extensions includes the Jupyter Lab nbconvert CSS styles and does some changes
to make it as generic as possible in order for it to work with a variety of mkdocs themes.
This is not always possible and the theme we test the most is [mkdocs-material](https://squidfunk.github.io/mkdocs-material).

It's possible you might need to do some CSS changes to make it look as good as you
want, for example for the material theme take a look at their [customization docs](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks).

Create a `main.html` file like:

```jinja
{% extends "base.html" %}

{% block content %}
{{ super() }}

<style>
// Do whatever changes you need here

.jp-RenderedHTMLCommon p {
    color: red
}

</style>
{% endblock content %}
```
