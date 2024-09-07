def test_parse_module_mkdocs():
    from mkapi.node import parse_module

    objects = parse_module("mkdocs")
    assert len(objects) == 1
    assert objects[0][0] == "__version__"


def test_parse_module_jinja2():
    from mkapi.node import parse_module

    objects = parse_module("jinja2")
    assert len(objects) > 30
    names = [name for name, _ in objects]
    assert "Template" in names
    assert "Environment" in names
