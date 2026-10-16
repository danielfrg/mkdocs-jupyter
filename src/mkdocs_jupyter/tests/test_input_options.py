from html.parser import HTMLParser

import nbformat
import pytest
import yaml
from mkdocs.commands.build import build
from mkdocs.config import load_config


class InputParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.inputs = 0
        self.prompts = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        classes = dict(attrs).get("class", "").split()
        self.inputs += "highlight-ipynb" in classes
        self.prompts += (
            "jp-InputPrompt" in classes or "jp-OutputPrompt" in classes
        )

    def handle_data(self, data):
        self.text.append(data.strip())


@pytest.mark.parametrize(
    "options,show_input",
    [
        ({"show_input": False, "no_prompt": True}, False),
        ({"no_input": True, "no_prompt": True}, False),
        ({"no_prompt": True}, True),
    ],
)
def test_no_prompt_preserves_input_options(
    tmp_path, monkeypatch, options, show_input
):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JUPYTER_NO_CONFIG", "1")
    docs = tmp_path / "docs"
    docs.mkdir()
    notebook = nbformat.v4.new_notebook(
        cells=[
            nbformat.v4.new_code_cell(
                "2 + 3",
                execution_count=1,
                outputs=[
                    nbformat.v4.new_output(
                        "execute_result",
                        data={"text/plain": "5"},
                        execution_count=1,
                    )
                ],
            )
        ]
    )
    nbformat.write(notebook, docs / "example.ipynb")
    config_file = tmp_path / "mkdocs.yml"
    config_file.write_text(
        yaml.safe_dump(
            {
                "site_name": "Input options",
                "plugins": [{"mkdocs-jupyter": options}],
                "nav": [{"Example": "example.ipynb"}],
            }
        ),
        encoding="utf-8",
    )
    build(load_config(str(config_file)))
    html = (tmp_path / "site/example/index.html").read_text(encoding="utf-8")
    parser = InputParser()
    parser.feed(html)
    assert bool(parser.inputs) == show_input
    assert parser.prompts == 0
    assert "5" in parser.text
