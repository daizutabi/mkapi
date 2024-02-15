import re

from mkapi.globals import get_fullname
from mkapi.link import LINK_PATTERN, get_markdown, get_markdown_from_docstring_text, get_markdown_from_type_string


def test_get_markdown():
    x = get_markdown("abc")
    assert x == "[abc][__mkapi__.abc]"
    x = get_markdown("a_._b.c")
    assert r"[a\_][__mkapi__.a_]." in x
    assert r".[\_b][__mkapi__.a_._b]." in x
    assert ".[c][__mkapi__.a_._b.c]" in x


def test_get_markdown_from_fullname_replace():
    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.objects")

    x = get_markdown("Object", replace)
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_markdown("Object.__repr__", replace)
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.objects.Object.__repr__]" in x

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.plugins")

    x = get_markdown("MkDocsPage", replace)
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkdocs.plugins")

    x = get_markdown("jinja2.Template", replace)
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x

    assert get_markdown("str", replace) == "str"
    assert get_markdown("None", replace) == "None"
    assert get_markdown("_abc", replace) == "\\_abc"


def test_get_markdown_from_type_string():
    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.objects")

    type_string = "1 Object or Class."
    x = get_markdown_from_type_string(type_string, replace)
    assert "1 [Object][__mkapi__.mkapi.objects.Object] " in x
    assert "or [Class][__mkapi__.mkapi.objects.Class]." in x


def test_link_pattern():
    def f(m: re.Match) -> str:
        name = m.group(1)
        if name == "abc":
            return f"[{name}][_{name}]"
        return m.group()

    assert re.search(LINK_PATTERN, "X[abc]Y")
    assert not re.search(LINK_PATTERN, "X[ab c]Y")
    assert re.search(LINK_PATTERN, "X[abc][]Y")
    assert not re.search(LINK_PATTERN, "X[abc](xyz)Y")
    assert not re.search(LINK_PATTERN, "X[abc][xyz]Y")
    assert re.sub(LINK_PATTERN, f, "X[abc]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc[abc]]Y") == "X[abc[abc][_abc]]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab]Y") == "X[ab]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab c]Y") == "X[ab c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc] c]Y") == "X[abc][_abc] c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc](xyz)Y") == "X[abc](xyz)Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][xyz]Y") == "X[abc][xyz]Y"


def test_get_markdown_from_docstring_text():
    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.objects")

    x = get_markdown_from_docstring_text("Class", replace)
    assert x == "Class"
    x = get_markdown_from_docstring_text("a [Class] b", replace)
    assert x == "a [Class][__mkapi__.mkapi.objects.Class] b"
    x = get_markdown_from_docstring_text("a [Class][] b", replace)
    assert x == "a [Class][__mkapi__.mkapi.objects.Class] b"
    x = get_markdown_from_docstring_text("a [Class][a] b", replace)
    assert x == "a [Class][a] b"
    m = "a \n```\n[Class][a]\n```\n b"
    assert get_markdown_from_docstring_text(m, replace) == m

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.plugins")

    x = get_markdown_from_docstring_text("a [MkAPIPlugin][] b", replace)
    assert x == "a [MkAPIPlugin][__mkapi__.mkapi.plugins.MkAPIPlugin] b"
    x = get_markdown_from_docstring_text("a [BasePlugin][] b", replace)
    assert x == "a [BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin] b"
    x = get_markdown_from_docstring_text("a [MkDocsConfig][] b", replace)
    assert x == "a [MkDocsConfig][__mkapi__.mkdocs.config.defaults.MkDocsConfig] b"

    x = get_markdown_from_docstring_text("a [__mkapi__.b] c", replace)
    assert x == "a b c"
    x = get_markdown_from_docstring_text("a [b] c", replace)
    assert x == "a [b] c"


# def test_set_markdown():
#     name = "mkapi.plugins"
#     node = get_module_node(name)
#     assert node
#     module = create_module(name, node)
#     assert module
#     x = module.name.markdown
#     assert x == "[mkapi][__mkapi__.mkapi].[plugins][__mkapi__.mkapi.plugins]"
#     obj = get_by_name(module.classes, "MkAPIPlugin")
#     assert isinstance(obj, Class)
#     m = obj.fullname.markdown
#     assert "[mkapi][__mkapi__.mkapi]." in m
#     assert ".[plugins][__mkapi__.mkapi.plugins]." in m
#     m = obj.bases[0].type.markdown
#     assert "[BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin]" in m
#     assert "[[MkAPIConfig][__mkapi__.mkapi.plugins.MkAPIConfig]]" in m
#     name = "mkapi.items"
#     node = get_module_node(name)
#     assert node
#     module = create_module(name, node)
#     obj = get_by_name(module.functions, "iter_raises")
#     assert isinstance(obj, Function)
#     m = obj.doc.text.markdown
#     assert m == "Yield [Raise][__mkapi__.mkapi.items.Raise] instances."


# def test_set_markdown_class():
#     name = "mkapi.ast"
#     node = get_module_node(name)
#     assert node
#     module = create_module(name, node)
#     assert module
#     cls = get_by_name(module.classes, "Transformer")
#     assert isinstance(cls, Class)
#     for x in cls.functions:
#         m = x.name.markdown
#         if x.name.str == "_rename":
#             assert m == r"[\_rename][__mkapi__.mkapi.ast.Transformer._rename]"
#         if x.name.str == "visit_Name":
#             assert m == r"[visit\_Name][__mkapi__.mkapi.ast.Transformer.visit_Name]"
#         if x.name.str == "unparse":
#             assert m == r"[unparse][__mkapi__.mkapi.ast.Transformer.unparse]"


# def test_set_markdown_class_doc():
#     name = "mkapi.ast"
#     node = get_module_node(name)
#     assert node
#     module = create_module(name, node)
#     assert module
#     cls = get_by_name(module.classes, "Transformer")
#     assert isinstance(cls, Class)
#     for x in cls.functions:
#         m = x.name.markdown
#         if x.name.str == "_rename":
#             assert m == r"[\_rename][__mkapi__.mkapi.ast.Transformer._rename]"
#         if x.name.str == "visit_Name":
#             assert m == r"[visit\_Name][__mkapi__.mkapi.ast.Transformer.visit_Name]"
#         if x.name.str == "unparse":
#             assert m == r"[unparse][__mkapi__.mkapi.ast.Transformer.unparse]"


# def test_set_markdown_attribute():
#     name = "examples.styles.google"
#     node = get_module_node(name)
#     assert node
#     module = create_module(name, node)
#     assert module
#     for x in module.attributes:
#         assert "][__mkapi__.examples.styles.google.module_level_v" in x.name.markdown
