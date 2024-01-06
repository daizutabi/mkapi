# from mkapi.objects import get_module
# from mkapi.renderer import renderer


# def test_render_module(google):
#     markdown = renderer.render_module(google)
#     assert "# ![mkapi](examples.styles.example_google" in markdown
#     assert "## ![mkapi](examples.styles.example_google.ExampleClass" in markdown
#     assert "## ![mkapi](examples.styles.example_google.example_generator" in markdown


# def test_module_empty_filters():
#     module = get_module("mkapi.core.base")
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
