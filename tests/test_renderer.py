import pytest

from mkapi.parser import Parser


@pytest.fixture(autouse=True)
def _load_templates():
    from mkapi.renderer import load_templates

    load_templates()


def test_load_templates():
    from mkapi.renderer import templates

    assert "heading" in templates
    assert "object" in templates
    assert "document" in templates
    assert "source" in templates


def test_render_heading_module():
    from mkapi.renderer import render_heading

    parser = Parser.create("examples.styles.google")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set.node.id, name_set.node.fullname, 1)
    assert '<h1 class="mkapi-heading" id="examples.styles.google" markdown="1">' in m
    assert "[examples][__mkapi__.examples].[styles][__mkapi__.examples.styles]" in m


def test_render_heading_export():
    from mkapi.renderer import render_heading

    parser = Parser.create("jinja2.Template")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set.node.id, name_set.node.fullname, 1)
    assert '<h1 class="mkapi-heading" id="jinja2.Template" markdown="1">' in m


def test_render_heading_alias():
    from mkapi.renderer import render_heading

    parser = Parser.create("examples.styles.ExampleClassGoogle")
    assert parser
    name_set = parser.parse_name_set()
    m = render_heading(name_set.node.id, name_set.node.fullname, 1)
    assert 'id="examples.styles.ExampleClassGoogle"' in m
    assert "[ExampleClassGoogle][__mkapi__.examples.styles.ExampleClassGoogle]" in m


# def test_render_object_module():
#     from mkapi.renderer import render_object

#     obj = get_object("examples.styles.google")
#     parser = Parser.create("examples.styles.google")
#     assert parser
#     signature = parser.parse_signature()
#     assert not signature
#     m = render_object(obj, name, namespace, signature)


#     set_markdown(obj)
#     x = render_heading(obj.fullname.str, 2)
#     assert (
#         '<h2 class="mkapi-heading" id="examples.styles.google.module_level_function"'
#         in x
#     )
#     assert r'markdown="1">examples.styles.google.module\_level\_function</h2>' in x


# def test_render_header():
#     obj = get_object_from_module("examples.styles.google")
#     assert obj
#     set_markdown(obj)
#     x = render_header(obj.fullname, "object")
#     assert ".styles].[google][__mkapi__.examples.styles.google]" in x
#     assert ">[object][__mkapi__.__object__.examples.styles.google]" in x


# def test_render_object_function():
#     obj = get_object_from_module("mkapi.items.create_parameters")
#     assert obj
#     set_markdown(obj)
#     x = render_object(obj)
#     assert 'object-kind">function</span>\n<span class="mkapi-object-name">' in x
#     assert 'class="mkapi-ann">[Iterable][__mkapi__.collections.abc.Iterable' in x
#     assert 'return">[Parameters][__mkapi__.mkapi.items.Parameters]<' in x


# def test_render_object_class():
#     obj = get_object_from_module("mkapi.object.Class")
#     assert obj
#     set_markdown(obj)
#     x = render_object(obj)
#     assert 'base">[Callable][__mkapi__.mkapi.object.Callable]</span></p>' in x


# def test_render_object_module():
#     obj = get_object_from_module("examples.styles.google")
#     assert obj
#     set_markdown(obj)
#     x = render_object(obj)
#     assert 'name">examples</span><span class="mkapi-dot">.</span>' in x


# def test_render_document():
#     obj = get_object_from_module("examples.styles.google.module_level_function")
#     assert obj
#     set_markdown(obj)
#     assert isinstance(obj, Function)
#     x = render_document(obj.doc)
#     assert '<span class="mkapi-item-name">**kwargs</span>' in x
#     assert '<span class="mkapi-item-type">ValueError</span>&mdash;' in x


# def test_render_source():
#     obj = get_object_from_module("examples.styles.google.ExampleClass")
#     assert obj
#     x = render_source(obj, attr=".test")
#     assert x.startswith("``` {.python .mkapi-source .test}\n")
#     assert x.endswith("    pass\n```\n")


# def test_get_source_class():
#     obj = get_object_from_module("examples.styles.google")
#     assert obj
#     x = _get_source(obj)
#     assert "docstrings.## __mkapi__.examples.styles.google" not in x
#     assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" in x
#     assert "attr2: int## __mkapi__.examples.styles.google.ExamplePEP526Class.attr2" in x
#     x = _get_source(obj, skip_self=False)
#     assert "docstrings.## __mkapi__.examples.styles.google" in x
#     assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" in x
#     assert "attr2: int## __mkapi__.examples.styles.google.ExamplePEP526Class.attr2" in x


# def test_get_source_module():
#     obj = get_object_from_module("examples.styles.google.ExampleClass")
#     assert obj
#     x = _get_source(obj)
#     assert (
#         "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" not in x
#     )
#     assert (
#         "self.attr1 = param1## __mkapi__.examples.styles.google.ExampleClass.attr1" in x
#     )
#     x = _get_source(obj, skip_self=False)
#     assert "class ExampleClass:## __mkapi__.examples.styles.google.ExampleClass" in x
#     assert (
#         "self.attr1 = param1## __mkapi__.examples.styles.google.ExampleClass.attr1" in x
#     )


# def test_summary():
#     obj = get_object_from_module("examples.styles.google.ExampleClass")
#     assert isinstance(obj, Class)
#     doc = _create_summary_docstring(obj)
#     assert doc
#     set_markdown(obj, doc)
#     m = render_document(doc)
#     assert (
#         '<p class="mkapi-section"><span class="mkapi-section-name">Methods</span></p>'
#         in m
#     )
#     assert "&mdash;\nClass methods are similar to regular functions.\n</li>" in m

#     obj = get_object_from_module("examples.styles.google")
#     assert isinstance(obj, Module)
#     doc = _create_summary_docstring(obj)
#     assert doc
#     set_markdown(obj, doc)
#     m = render_document(doc)
#     assert '<span class="mkapi-section-name">Classes</span>' in m
#     assert '<span class="mkapi-section-name">Functions</span>' in m


# def test_summary_alias():
#     obj = get_object_from_module("examples.styles")
#     assert isinstance(obj, Module)
#     assert obj.aliases
#     doc = _create_summary_docstring(obj)
#     assert doc
#     set_markdown(obj, doc)
#     m = render_document(doc)
#     assert '<span class="mkapi-section-name">Classes</span>' in m
#     assert "[ExampleClassGoogle][__mkapi__.examples.styles.ExampleClassGoogle]" in m
#     assert "[ExampleClassNumPy][__mkapi__.examples.styles.ExampleClassNumPy]" in m
