def test_import():
    import mkdocs_jupyter

    assert mkdocs_jupyter.__version__ is not None
    assert mkdocs_jupyter.__version__ != "0.0.0"
    assert len(mkdocs_jupyter.__version__) > 0
