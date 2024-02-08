import sys
from pathlib import Path

from mkapi.importlib import get_object
from mkapi.objects import Class
from mkapi.renderers import load_templates, render, templates

path = str(Path(__file__).parent)
if path not in sys.path:
    sys.path.insert(0, str(path))


def test_load_templates():
    load_templates()
    assert "object" in templates
    assert "source" in templates


def test_render_sourcelink():
    obj = get_object("examples")
    assert obj
    c = '<div class="mkapi-container" markdown="1">\n'
    h = '<h2 class="mkapi-heading" id="examples" markdown="1">'
    n = '<span class="mkapi-heading-name">examples</span>'
    s = '<span class="mkapi-source-link">[source][__mkapi__.__source__.examples]</span>'
    x = render(obj, 2, ["sourcelink"])
    m = f"{c}\n{h}\n{n}\n{s}\n</h2>\n"
    assert x.startswith(m)
    x = render(obj, 2, [])
    m = f"{c}\n{h}\n{n}\n</h2>\n"
    assert x.startswith(m)


def test_render_moduled():
    obj = get_object("examples.styles")
    assert obj
    m = render(obj, 2, [])
    s = '<p class="mkapi-object" markdown="1">\n  <'
    assert s in m
    assert '>\n  <span class="mkapi-object-kind">package</span>\n  <' in m
    assert "styles</span></span></p>" in m


def test_render_method():
    obj = get_object("examples.styles.google.ExampleClass.example_method")
    assert obj
    m = render(obj, 2, [])
    s = '<p class="mkapi-object" markdown="1">\n  <'
    assert s in m
    assert '>\n  <span class="mkapi-object-kind">method</span>\n  <' in m
    assert '>\n  <span class="mkapi-object-name"><span' in m
    assert '><span class="mkapi-paren">)</span></span></p>' in m


def test_render_attribute():
    obj = get_object("examples.styles.google.module_level_variable1")
    assert obj
    m = render(obj, 2, [])
    s = '<p class="mkapi-object" markdown="1">\n  <'
    assert s in m
    assert '>\n  <span class="mkapi-object-kind">attribute</span>\n  <' in m
    assert '</span></span>\n    <span class="mkapi-colon">:</span>\n' in m
    assert ':</span>\n    <span class="mkapi-object-type">int</span></p>' in m


def test_render_class():
    obj = get_object("mkapi.objects.Class")
    assert isinstance(obj, Class)
    bases = obj.bases
    obj.bases = bases * 2
    m = render(obj, 2, [])
    s = "</span></span></p>\n"
    assert s in m
    assert '.Callable]</span><span class="mkapi-comma">, </span>\n' in m
    # assert '.Callable]</span>\n</p>\n\n<div class="mkapi-doc-text"' in m
    obj.bases = bases


# def test_render_doc_text():
#     obj = get_object("examples.styles.google.ExampleClass")
#     assert obj
#     m = render(obj, 2, [])
#     s = '<div class="mkapi-doc-text" markdown="1">\nThe summary'
#     assert s in m


# def test_render_section():
#     obj = get_object("examples.styles.google.ExampleClass")
#     assert obj
#     m = render(obj, 2, [])
#     print(m)
#     assert '</div>\n\n<div class="mkapi-section"' in m
#     assert '</div>\n\n<ul class="mkapi-section-items" markdown="1">' in m
#     assert "\n  </li>\n\n  <li" in m
#     assert "\n  </li>\n\n</ul>\n" in m


# def test_render_sourcelink():
#     obj = get_object("examples.styles.google.ExampleClass")
#     assert obj
#     m = render(obj, 2, ["sourcelink"])
#     print(m[:400])
#     print("-" * 40)
#     m = render(obj, 2, [])
#     print(m[:400])
#     assert 0
#     # name = "polars.config.Config.set_tbl_cell_alignment"
# obj = get_object(name)
# assert obj
# m = render(obj, 1, [])
# print(m)
# print("-" * 100)
# h = markdown.markdown(m, extensions=["md_in_html"])
# print(h)
# # assert 0
