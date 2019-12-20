{%- extends "basic.tpl" -%}

{% block header %}
    <script src="https://ajax.googleapis.com/ajax/libs/jquery/3.3.1/jquery.min.js"></script>
    {% include "ipywidgets.html" %}

    <style type="text/css">
        {% include "jupyter-fixes.min.css" %}
    </style>
{%- endblock header %}


{% block input %}
    {# Add tags to the cell #}
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
