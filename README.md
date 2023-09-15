<p align="center">
    <img src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/main/docs/logo.png" width="450px">
</p>

<p align="center">
    <a href="https://pypi.org/project/mkdocs-jupyter/">
        <img src="https://img.shields.io/pypi/v/mkdocs-jupyter.svg">
    </a>
    <a href="https://pypi.org/project/mkdocs-jupyter/">
        <img src="https://img.shields.io/pypi/pyversions/mkdocs-jupyter.svg">
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

-   [Docs demo Site](https://mkdocs-jupyter.danielfrg.com/)
-   Add Jupyter Notebooks directly to the mkdocs navigation
-   Support for multiple formats:
    -   `.ipynb` and `.py` files (using
        [jupytext](https://github.com/mwouts/jupytext))
-   Same style as regular Jupyter Notebooks
    -   Support Jupyter Themes
-   Option to execute the notebook before converting
-   Support for [ipywidgets](https://github.com/jupyter-widgets/ipywidgets)
-   Support for mkdocs TOC
-   Option to include notebook source

<a
href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png"><img
src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/mkdocs-theme.png"
alt="mkdocs-jupyter default theme"  width="300"></a> <a
href="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png"><img
src="https://raw.githubusercontent.com/danielfrg/mkdocs-jupyter/master/docs/material-theme.png"
alt="mkdocs-jupyter material theme"  width="300"></a>

## Installation

```shell
pip install mkdocs-jupyter
```

## Configuration

In the `mkdocs.yml` use Jupyter notebooks (`.ipynb`) or Python scripts (`.py`)
as pages:

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

This can be turned off in the configuration (in which case the filename will be
used as title):

```yaml
plugins:
    - mkdocs-jupyter:
          ignore_h1_titles: True
```

In order to see the table of contents you need to maintain a hierarchical
headers structure in your notebooks. You must use h2 headers (`##`) and not h1
(`#`)

```md
## This H2 title will show in the table of contents
```

If you want to **nest headers** in the TOC you need to add additional levels
later in the same markdown cell or new bottom markdown cells:

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
          include: ["*.ipynb"] # Default: ["*.py", "*.ipynb"]
          ignore: ["some-irrelevant-files/*.ipynb"]
```

### Execute Notebook

You can tell the plugin to execute the notebook before converting, default is
`False`:

```yaml
plugins:
    - mkdocs-jupyter:
          execute: true
```

You can tell the plugin to ignore the execution of some files (with glob
matching):

```yaml
plugins:
    - mkdocs-jupyter:
          execute_ignore:
              - "my-secret-files/*.ipynb"
```

To fail when notebook execution fails set `allow_errors` to `false`:

```yaml
plugins:
    - mkdocs-jupyter:
          execute: true
          allow_errors: false
```

#### Kernel

By default the plugin will use the kernel specified in the notebook to execute
it. You can specify a custom kernel name to use for all the notebooks:

```yaml
plugins:
    - mkdocs-jupyter:
          kernel_name: python3
```

### Ingore Code Input

By default the plugin will show full code and regular cell output details. You
can hide cell code input for all the notebooks:

```yaml
plugins:
    - mkdocs-jupyter:
          show_input: False
```

You can also decide to hide the `Out[#]` output notation and other cell metadata
for all the notebooks:

```yaml
plugins:
    - mkdocs-jupyter:
          no_input: True
```

### Remove Cell Using Tags

By default the plugin will show full code and regular cell output details. You
can hide cell code input for specific cells using tags:

```yaml
plugins:
    - mkdocs-jupyter:
          remove_tag_config:
              remove_input_tags:
                  - hide_code
```

More detailed on removing cell based on tag, see [NbConvert
Customization](https://nbconvert.readthedocs.io/en/latest/removing_cells.html))

### Jupyter themes

You can configure the different Jupyter themes. For example if using material
with `slate` color scheme you can use the Jupyter Lab `dark` theme:

```yml
plugins:
    - mkdocs-jupyter:
          theme: dark

theme:
    name: material
    palette:
        scheme: slate
```

### Extra CSS classes

This option will add a custom CSS class to the `div` container that highlights
the code cells. This can be useful to add custom styles to the code cells.

```yml
plugins:
  - mkdocs-jupyter:
      highlight_extra_classes: "custom-css-classes
```

### RequireJS

By default RequireJS is not loaded. You can enable it with:

```yml
plugins:
    - mkdocs-jupyter:
          include_requirejs: true
```

### Download notebook link

You can tell the plugin to include the notebook source to make it easy to show a
download button in the theme, default is `False`:

```yml
plugins:
    - mkdocs-jupyter:
          include_source: True
```

This setting will also create a `page.nb_url` value that you can use in your
theme to make a link in each page.

For example in `mkdocs-material` (see
[customization](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks)),
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

## Styles

This extensions includes the Jupyter Lab nbconvert CSS styles and does some
modifications to make it as generic as possible in order for it to work with a
variety of mkdocs themes. This is not always possible and the theme we test the
most is [mkdocs-material](https://squidfunk.github.io/mkdocs-material).

It's possible you might need to do some CSS changes to make it look as good as
you want, for example for the material theme take a look at their [customization
docs](https://squidfunk.github.io/mkdocs-material/customization/#overriding-template-blocks).

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

## Mkdocs Material notes

Any markdown specific features such as
[admonitions](https://squidfunk.github.io/mkdocs-material/reference/admonitions/)
wont work with mkdocs-jupyter because those features are not supported by
Jupyter itself and we use [nbconvert](https://nbconvert.readthedocs.io/) to make
the conversion.

To use this type of features you have to define the HTML directly in the
markdown cells:

```html
<div class="admonition note">
    <p class="admonition-title">Note</p>
    <p>
        If two distributions are similar, then their entropies are similar,
        implies the KL divergence with respect to two distributions will be
        smaller...
    </p>
</div>
```
