from mkapi.core.code import get_code
from mkapi.core.module import get_module
from mkapi.core.renderer import renderer


def test_module_empty_filters():
    module = get_module("mkapi.core.base")
    m = renderer.render_module(module).split("\n")
    assert m[0] == "# ![mkapi](mkapi.core.base|plain|link|sourcelink)"
    assert m[2] == "## ![mkapi](mkapi.core.base.Base||link|sourcelink)"
    assert m[3] == "## ![mkapi](mkapi.core.base.Inline||link|sourcelink)"
    assert m[4] == "## ![mkapi](mkapi.core.base.Type||link|sourcelink)"
    assert m[5] == "## ![mkapi](mkapi.core.base.Item||link|sourcelink)"


def test_code_empty_filters():
    code = get_code("mkapi.core.base")
    m = renderer.render_code(code)
    assert '<span class="mkapi-object-prefix">mkapi.core.</span>' in m
    assert '<span class="mkapi-object-name">base</span>' in m
    assert '<span id="mkapi.core.base"></span>' in m
    assert '<a class="mkapi-docs-link" href="../../mkapi.core.base">DOCS</a>' in m
