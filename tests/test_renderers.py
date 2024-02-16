from mkapi.importlib import get_object
from mkapi.link import set_markdown
from mkapi.renderers import (
    _get_source,
    load_templates,
    render_document,
    render_header,
    render_heading,
    render_object,
    render_source,
    templates,
)


def test_load_templates():
    load_templates()

    assert "heading" in templates
    assert "header" in templates
    assert "object" in templates
    assert "document" in templates
    assert "source" in templates


def test_render_heading():
    obj = get_object("examples.styles.google.module_level_function")
    assert obj
    set_markdown(obj)
    x = render_heading(obj, 2)
    assert '<h2 class="mkapi-heading" id="examples.styles.google.module_level_function"' in x
    assert r'markdown="1">examples.styles.google.module\_level\_function</h2>' in x


def test_render_header():
    obj = get_object("examples.styles.google")
    assert obj
    set_markdown(obj)
    x = render_header(obj, "object")
    assert ".styles].[google][__mkapi__.examples.styles.google]" in x
    assert ">[object][__mkapi__.__object__.examples.styles.google]" in x


def test_render_object_function():
    obj = get_object("mkapi.items.create_parameters")
    assert obj
    set_markdown(obj)
    x = render_object(obj)
    assert 'object-kind">function</span>\n<span class="mkapi-object-name">' in x
    assert 'class="mkapi-ann">[Iterable][__mkapi__.collections.abc.Iterable' in x
    assert 'return">[Parameters][__mkapi__.mkapi.items.Parameters]<' in x


def test_render_object_class():
    obj = get_object("mkapi.objects.Class")
    assert obj
    set_markdown(obj)
    x = render_object(obj)
    assert 'base">[Callable][__mkapi__.mkapi.objects.Callable]</span></p>' in x


def test_render_object_module():
    obj = get_object("examples.styles.google")
    assert obj
    set_markdown(obj)
    x = render_object(obj)
    assert 'name">examples</span><span class="mkapi-dot">.</span>' in x


def test_render_document():
    obj = get_object("examples.styles.google.module_level_function")
    assert obj
    set_markdown(obj)
    x = render_document(obj)
    print(x)


def test_render_source():
    obj = get_object("examples.styles.google.ExampleClass")
    assert obj
    x = render_source(obj, attr=".test")
    assert x.startswith("``` {.python .mkapi-source .test}\n")
    assert x.endswith("    pass\n```\n")


def test_get_source_class():
    obj = get_object("examples.styles.google")
    assert obj
    x = _get_source(obj)
    assert "docstrings.## __mkapi__.examples.styles.google" not in x
    assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" in x
    assert "attr2: int## __mkapi__.examples.styles.google.ExamplePEP526Class.attr2" in x
    x = _get_source(obj, skip_self=False)
    assert "docstrings.## __mkapi__.examples.styles.google" in x
    assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" in x
    assert "attr2: int## __mkapi__.examples.styles.google.ExamplePEP526Class.attr2" in x


def test_get_source_module():
    obj = get_object("examples.styles.google.ExampleClass")
    assert obj
    x = _get_source(obj)
    assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" not in x
    assert "self.attr1 = param1## __mkapi__.examples.styles.google.ExampleClass.attr1" in x
    x = _get_source(obj, skip_self=False)
    assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" in x
    assert "self.attr1 = param1## __mkapi__.examples.styles.google.ExampleClass.attr1" in x


# def test_render_sourcelink():
#     obj = get_object("examples")
#     assert obj
#     h = '<h2 class="mkapi-header" id="examples" markdown="1">'
#     n = '<span class="mkapi-header-name">[examples][__mkapi__.examples]</span>'
#     s = '<span class="mkapi-source-link">[source][__mkapi__.__source__.examples]</span>'
#     x = render(obj, 2, [])
#     m = f"{h}\n{n}\n{s}\n</h2>\n"
#     assert m in x


# def test_render_module():
#     obj = get_object("examples.styles")
#     assert obj
#     m = render(obj, 2, [])
#     s = '<p class="mkapi-object" markdown="1">\n<'
#     assert s in m
#     assert '>\n<span class="mkapi-object-kind">package</span>\n<' in m
#     assert "styles</span></span></p>" in m


# def test_render_method():
#     obj = get_object("examples.styles.google.ExampleClass.example_method")
#     assert obj
#     m = render(obj, 2, [])
#     s = '<p class="mkapi-object" markdown="1">\n<'
#     assert s in m
#     assert '>\n<span class="mkapi-object-kind">method</span>\n<' in m
#     assert '>\n<span class="mkapi-object-name"><span' in m
#     assert '><span class="mkapi-paren">)</span></span></p>' in m


# def test_render_attribute():
#     obj = get_object("examples.styles.google.module_level_variable1")
#     assert obj
#     m = render(obj, 2, [])
#     s = '<p class="mkapi-object" markdown="1">\n<'
#     assert s in m
#     assert '>\n<span class="mkapi-object-kind">attribute</span>\n<' in m
#     assert '</span></span>\n    <span class="mkapi-colon">:</span>\n' in m
#     assert ':</span>\n    <span class="mkapi-object-type">int</span></p>' in m


# def test_render_class():
#     obj = get_object("mkapi.objects.Class")
#     assert isinstance(obj, Class)
#     bases = obj.bases
#     obj.bases = bases * 2
#     m = render(obj, 2, [])
#     s = "</span></span></p>\n"
#     assert s in m
#     assert '.Callable]</span><span class="mkapi-comma">, </span>\n' in m
#     obj.bases = bases


# def test_source():
#     cache_clear()
#     module = get_object("mkapi.objects")
#     assert isinstance(module, Module)
#     cls = get_by_name(module.classes, "Object")
#     assert isinstance(cls, Class)
#     f = get_object_filter_for_source(cls, module)
#     assert f
#     m = render(module, 1, [f], is_source=True)
#     assert "\nclass Object(Names):## __mkapi__.mkapi.objects.Object\n" in m
