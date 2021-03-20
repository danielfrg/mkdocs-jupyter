# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.11.0
#   kernelspec:
#     display_name: Python 3
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Demo notebook
#
# ## Header 2
#
# Lorem ipsum dolor sit amet, consectetur adipiscing elit. Curabitur purus mi, sollicitudin ac justo a, dapibus ultrices dolor. Curabitur id eros mattis, tincidunt ligula at, condimentum urna.
#
# ### Header 3
#
# A regular markdown code block
#
# ```python
# id_ = 0
# for directory in directories:
#     rootdir = os.path.join('/Users/drodriguez/Downloads/aclImdb', directory)
#     for subdir, dirs, files in os.walk(rootdir):
#         for file_ in files:
#             with open(os.path.join(subdir, file_), 'r') as f:
#                 doc_id = '_*%i' % id_
#                 id_ = id_ + 1
#
#                 text = f.read()
#                 text = text.decode('utf-8')
#                 tokens = nltk.word_tokenize(text)
#                 doc = ' '.join(tokens).lower()
#                 doc = doc.encode('ascii', 'ignore')
#                 input_file.write('%s %s\n' % (doc_id, doc))
# ```
#
# ### More markdown things
#
# > Pellentesque pretium euismod laoreet. Nullam eget mauris ut tellus vehicula consequat. In sed molestie metus. Nulla at varius nunc, sit amet semper arcu. Integer tristique augue eget auctor aliquam. Donec ornare consectetur lectus et viverra. Duis vel elit ac lectus accumsan gravida non ac erat.
#
# Ut in ipsum id neque pellentesque iaculis. Pellentesque massa erat, rhoncus id auctor vel, tempor id neque. Nunc nec iaculis enim. Duis eget tincidunt tellus. Proin vitae ultrices velit.
#
# 1. Item 1
# 2. Curabitur vel enim at mi dictum venenatis eget eu nulla. Suspendisse potenti. Etiam vitae nibh a odio dictum aliquam. Sed sit amet adipiscing leo, vitae euismod arcu.
# 3. Item 3
#
# Sed vestibulum justo et turpis ullamcorper, a interdum sapien tristique. Donec ullamcorper ipsum ac scelerisque lacinia. Quisque et eleifend odio. Curabitur vel enim at mi dictum venenatis eget eu nulla. Suspendisse potenti. Etiam vitae nibh a odio dictum aliquam. Sed sit amet adipiscing leo, vitae euismod arcu.
#
# - Item 1
# - Curabitur vel enim at mi dictum venenatis eget eu nulla. Suspendisse potenti. Etiam vitae nibh a odio dictum aliquam. Sed sit amet adipiscing leo, vitae euismod arcu.
# - Item 3
#
# ![Alt text](http://img3.wikia.nocookie.net/__cb20130524024810/logopedia/images/f/fa/Apple_logo_black.svg "Image")
#
# <hr>
#
# Sed vestibulum justo et turpis ullamcorper, a interdum sapien tristique. Donec ullamcorper ipsum ac scelerisque lacinia. Quisque et eleifend odio. Curabitur vel enim at mi dictum venenatis eget eu nulla. Suspendisse potenti. Etiam vitae nibh a odio dictum aliquam. Sed sit amet adipiscing leo, vitae euismod arcu.

# %% [markdown]
# ## Code cells
#
# This first code cells have some tags

# %% tags=["tag1"]
a = 1

# %% tags=["tag1", "tag2"]
a

# %% tags=["tag1", "tag2", "tag3"]
b = "pew"

# %%
b

# %%
import re

# %%
text = "foo bar\t baz \tqux"

# %%
re.split("\s+", text)

# %% language="latex"
# \begin{align}
# \nabla \times \vec{\mathbf{B}} -\, \frac1c\, \frac{\partial\vec{\mathbf{E}}}{\partial t} & = \frac{4\pi}{c}\vec{\mathbf{j}} \\
# \nabla \cdot \vec{\mathbf{E}} & = 4 \pi \rho \\
# \nabla \times \vec{\mathbf{E}}\, +\, \frac1c\, \frac{\partial\vec{\mathbf{B}}}{\partial t} & = \vec{\mathbf{0}} \\
# \nabla \cdot \vec{\mathbf{B}} & = 0
# \end{align}

# %%
import numpy as np
import pandas as pd

# %%
dates = pd.date_range("20130101", periods=6)
df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list("ABCD"))
df

# %%
# %matplotlib inline

# %%
import matplotlib.pyplot as plt

# %%
from pylab import *

# %%
x = linspace(0, 5, 10)
y = x ** 2

# %%
figure()
plot(x, y, "r")
xlabel("x")
ylabel("y")
title("title")
show()

# %%
num_points = 130
y = np.random.random(num_points)
plt.plot(y)

# %% [markdown]
# This is some text, here comes some latex

# %% [markdown]
# ## Javascript plots

# %% [markdown]
# ### plotly

# %%
import plotly.express as px

# %%
df = px.data.iris()
fig = px.scatter(df, x="sepal_width", y="sepal_length")
fig.show()

# %% [markdown]
# ### bokeh

# %%
from bokeh.plotting import figure, output_notebook, show

# %%
output_notebook()

# %%
p = figure()
p.line([1, 2, 3, 4, 5], [6, 7, 2, 4, 5], line_width=2)
show(p)

# %%
