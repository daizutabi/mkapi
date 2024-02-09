import sys
from pathlib import Path

from mkapi.importlib import cache_clear, get_object, load_module
from mkapi.objects import Class, Module, objects
from mkapi.renderers import (
    get_object_filter_for_source,
    load_templates,
    render,
    templates,
)
from mkapi.utils import get_by_name, get_module_node_source

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
    c = '<div class="mkapi-content" markdown="1">\n'
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
    obj.bases = bases


def test_source():
    cache_clear()
    module = get_object("mkapi.objects")
    assert isinstance(module, Module)
    cls = get_by_name(module.classes, "Object")
    assert isinstance(cls, Class)
    f = get_object_filter_for_source(cls, module)
    assert f
    m = render(module, 2, ["source", f])
    print(m)
    assert "\nclass Object:## __mkapi__.mkapi.objects.Object\n" in m
