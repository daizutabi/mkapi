import pytest

from mkapi.renderers import (
    _split_name_depth,
    load_templates,
    render_markdown,
    templates,
)


def test_load_templates():
    load_templates()
    assert "bases" in templates
    assert "code" in templates
    assert "docstring" in templates
    assert "items" in templates
    assert "macros" in templates
    assert "member" in templates
    assert "node" in templates
    assert "object" in templates


@pytest.fixture(scope="module")
def template():
    load_templates()
    return templates["module"]


def test_split_name_depth():
    assert _split_name_depth("a.b.c") == ("a.b.c", 0)
    assert _split_name_depth("a.b.c.*") == ("a.b.c", 1)
    assert _split_name_depth("a.b.c.**") == ("a.b.c", 2)


def test_render_markdown():
    x = render_markdown("polars.dataframe", 0, [])
    assert x == "::: polars.dataframe\n"
    x = render_markdown("polars.dataframe", 1, ["a", "b"])
    assert x == "# ::: polars.dataframe|a|b\n"
    x = render_markdown("polars.dataframe.frame.*", 1, ["a", "b"])
    assert "# ::: polars.dataframe.frame|a|b\n" in x
    assert "## ::: polars.dataframe.frame.DataFrame|a|b" in x

    def predicate(obj):
        return not obj.name.startswith("_")

    name = "polars.dataframe.frame.**"
    x = render_markdown(name, 2, [], predicate)
    assert "#### ::: polars.dataframe.frame.DataFrame.item\n" in x
    assert "#### ::: polars.dataframe.frame.DataFrame._replace\n" not in x


# def test_render_module(google):
#     markdown = renderer.render_module(google)
#     assert "# ![mkapi](examples.styles.example_google" in markdown
#     assert "## ![mkapi](examples.styles.example_google.ExampleClass" in markdown
#     assert "## ![mkapi](examples.styles.example_google.example_generator" in markdown


# def test_module_empty_filters():
#     module = load_module("mkapi.core.base")
#     m = renderer.render_module(module).split("\n")
#     assert m[0] == "# ![mkapi](mkapi.core.base|plain|link|sourcelink)"
#     assert m[2] == "## ![mkapi](mkapi.core.base.Base||link|sourcelink)"
#     assert m[3] == "## ![mkapi](mkapi.core.base.Inline||link|sourcelink)"
#     assert m[4] == "## ![mkapi](mkapi.core.base.Type||link|sourcelink)"
#     assert m[5] == "## ![mkapi](mkapi.core.base.Item||link|sourcelink)"


# def test_code_empty_filters():
#     code = get_code("mkapi.core.base")
#     m = renderer.render_code(code)
#     assert '<span class="mkapi-object-prefix">mkapi.core.</span>' in m
#     assert '<span class="mkapi-object-name">base</span>' in m
#     assert '<span id="mkapi.core.base"></span>' in m
#     assert '<a class="mkapi-docs-link" href="../../mkapi.core.base">DOCS</a>' in m
