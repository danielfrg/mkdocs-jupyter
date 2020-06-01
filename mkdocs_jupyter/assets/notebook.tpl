{# This is basically our on version of full.tpl #}

{%- extends "basic.tpl" -%}
{% from 'mathjax.tpl' import mathjax %}

{%- block header -%}
<style type="text/css">
    {% include "jupyter-fixes.min.css" %}
</style>

<script src="https://cdnjs.cloudflare.com/ajax/libs/require.js/2.1.10/require.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery/2.0.3/jquery.min.js"></script>

{% block ipywidgets %}
{%- if "widgets" in nb.metadata -%}
<script>
(function() {
  function addWidgetsRenderer() {
    var mimeElement = document.querySelector('script[type="application/vnd.jupyter.widget-view+json"]');
    var scriptElement = document.createElement('script');
    var widgetRendererSrc = '{{ resources.ipywidgets_base_url }}@jupyter-widgets/html-manager@*/dist/embed-amd.js';
    var widgetState;
    // Fallback for older version:
    try {
      widgetState = mimeElement && JSON.parse(mimeElement.innerHTML);
      if (widgetState && (widgetState.version_major < 2 || !widgetState.version_major)) {
        widgetRendererSrc = '{{ resources.ipywidgets_base_url }}jupyter-js-widgets@*/dist/embed.js';
      }
    } catch(e) {}
    scriptElement.src = widgetRendererSrc;
    document.body.appendChild(scriptElement);
  }
  document.addEventListener('DOMContentLoaded', addWidgetsRenderer);
}());
</script>
{%- endif -%}
{% endblock ipywidgets %}

<!-- Loading mathjax macro -->
{{ mathjax() }}

{%- endblock header -%}

{% block input %}
{# We overwrite this to show the tags on the cell toolbar #}
    <div class="inner_cell">
        {% set cell_tags = cell["metadata"].get("tags", [])%}
        {% if cell_tags %}
            <div class="celltoolbar">
                {% for cell in cell_tags %}
                <div class="button_container tags_button_container">
                    <span class="tag-container">
                        <span class="cell-tag">{{ cell }}</span>
                    </span>
                </div>
                {% endfor %}
            </div>
        {% endif %}
        <div class="input_area">
            {{ cell.source | highlight_code(metadata=cell.metadata) }}
        </div>
    </div>
{% endblock %}
