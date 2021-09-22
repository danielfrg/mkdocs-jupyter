import os


def test_import():
    import mkdocs_jupyter

    assert mkdocs_jupyter.__version__ is not None
    assert mkdocs_jupyter.__version__ != "0.0.0"
    assert len(mkdocs_jupyter.__version__) > 0


def test_styles_included():
    import mkdocs_jupyter

    module_dir = os.path.dirname(mkdocs_jupyter.__file__)

    assert os.path.exists(
        os.path.join(module_dir, "templates", "mkdocs_html", "conf.json")
    )
    assert os.path.exists(
        os.path.join(
            module_dir, "templates", "mkdocs_html", "notebook.html.j2"
        )
    )
    assert os.path.exists(
        os.path.join(
            module_dir, "templates", "mkdocs_html", "styles", "jupyter-lab.css"
        )
    )
    assert os.path.exists(
        os.path.join(
            module_dir,
            "templates",
            "mkdocs_html",
            "styles",
            "jupyter-lab.css.map",
        )
    )
    assert os.path.exists(
        os.path.join(module_dir, "templates", "mkdocs_md", "conf.json")
    )
    assert os.path.exists(
        os.path.join(
            module_dir, "templates", "mkdocs_md", "md-no-codecell.md.j2"
        )
    )
