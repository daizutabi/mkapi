import re


def test_link_pattern():
    from mkapi.converters import LINK_PATTERN

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


def test_get_markdown_name_noreplace():
    from mkapi.converters import get_markdown_name

    x = get_markdown_name("abc")
    assert x == "[abc][__mkapi__.abc]"
    x = get_markdown_name("a_._b.c")
    assert r"[a\_][__mkapi__.a_]." in x
    assert r".[\_b][__mkapi__.a_._b]." in x
    assert ".[c][__mkapi__.a_._b.c]" in x


def test_get_markdown_name():
    from mkapi.converters import get_markdown_name
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.objects")

    x = get_markdown_name("Object", replace)
    assert x == "[Object][__mkapi__.mkapi.objects.Object]"
    x = get_markdown_name("Object.__repr__", replace)
    assert r".[\_\_repr\_\_][__mkapi__.mkapi.objects.Object.__repr__]" in x

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.plugins")

    x = get_markdown_name("MkDocsPage", replace)
    assert x == "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]"

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkdocs.plugins")

    x = get_markdown_name("jinja2.Template", replace)
    assert "[jinja2][__mkapi__.jinja2]." in x
    assert "[Template][__mkapi__.jinja2.environment.Template]" in x

    assert get_markdown_name("str", replace) == "str"
    assert get_markdown_name("None", replace) == "None"
    assert get_markdown_name("_abc", replace) == "\\_abc"


def test_get_markdown_str():
    from mkapi.converters import get_markdown_str
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.objects")

    type_string = "1 Object or Class."
    x = get_markdown_str(type_string, replace)
    assert "1 [Object][__mkapi__.mkapi.objects.Object] " in x
    assert "or [Class][__mkapi__.mkapi.objects.Class]." in x


def test_get_markdown_text():
    from mkapi.converters import get_markdown_text
    from mkapi.nodes import get_fullname

    def replace(name: str) -> str | None:  # type: ignore
        return get_fullname(name, "mkapi.objects")

    x = get_markdown_text("Class", replace)
    assert x == "Class"
    x = get_markdown_text("a [Class] b", replace)
    assert x == "a [Class][__mkapi__.mkapi.objects.Class] b"
    x = get_markdown_text("a [Class][] b", replace)
    assert x == "a [Class][__mkapi__.mkapi.objects.Class] b"
    x = get_markdown_text("a [Class][a] b", replace)
    assert x == "a [Class][a] b"
    m = "a \n```\n[Class][a]\n```\n b"
    assert get_markdown_text(m, replace) == m

    def replace(name: str) -> str | None:
        return get_fullname(name, "mkapi.plugins")

    x = get_markdown_text("a [MkAPIPlugin][] b", replace)
    assert x == "a [MkAPIPlugin][__mkapi__.mkapi.plugins.MkAPIPlugin] b"
    x = get_markdown_text("a [BasePlugin][] b", replace)
    assert x == "a [BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin] b"
    x = get_markdown_text("a [MkDocsConfig][] b", replace)
    assert x == "a [MkDocsConfig][__mkapi__.mkdocs.config.defaults.MkDocsConfig] b"

    x = get_markdown_text("a [__mkapi__.b] c", replace)
    assert x == "a b c"
    x = get_markdown_text("a [b] c", replace)
    assert x == "a [b] c"


# def test_set_markdown_module():
#     name = "mkapi.plugins"
#     module = create_module(name)
#     assert module
#     set_markdown(module)
#     x = module.name.markdown
#     assert x == "[mkapi][__mkapi__.mkapi].[plugins][__mkapi__.mkapi.plugins]"
#     obj = get_by_name(module.classes, "MkAPIPlugin")
#     assert isinstance(obj, Class)
#     set_markdown(obj)
#     m = obj.fullname.markdown
#     assert "[mkapi][__mkapi__.mkapi]." in m
#     assert ".[plugins][__mkapi__.mkapi.plugins]." in m
#     m = obj.bases[0].type.markdown
#     assert "[BasePlugin][__mkapi__.mkdocs.plugins.BasePlugin]" in m
#     assert "[[MkAPIConfig][__mkapi__.mkapi.plugins.MkAPIConfig]]" in m


# def test_set_markdown_text():
#     name = "mkapi.items"
#     module = create_module(name)
#     assert module
#     func = get_by_name(module.functions, "iter_raises")
#     assert isinstance(func, Function)
#     set_markdown(func)
#     m = func.doc.text.markdown
#     assert m == "Yield [Raise][__mkapi__.mkapi.items.Raise] instances."


# def test_set_markdown_class():
#     name = "mkapi.ast"
#     module = create_module(name)
#     assert module
#     cls = get_by_name(module.classes, "Transformer")
#     assert isinstance(cls, Class)
#     for func in cls.functions:
#         set_markdown(func)
#         m = func.name.markdown
#         if func.name.str == "_rename":
#             assert m == r"[\_rename][__mkapi__.mkapi.ast.Transformer._rename]"
#         if func.name.str == "visit_Name":
#             assert m == r"[visit\_Name][__mkapi__.mkapi.ast.Transformer.visit_Name]"
#         if func.name.str == "unparse":
#             assert m == r"[unparse][__mkapi__.mkapi.ast.Transformer.unparse]"
#         if func.name.str == "visit":
#             assert m == r"[visit][__mkapi__.ast.NodeVisitor.visit]"
#         if func.name.str == "generic_visit":
#             assert m == r"[generic\_visit][__mkapi__.ast.NodeTransformer.generic_visit]"
#         if func.name.str == "visit_Constant":
#             assert m == r"[visit\_Constant][__mkapi__.ast.NodeVisitor.visit_Constant]"


# def test_set_markdown_attribute():
#     name = "examples.styles.google"
#     module = create_module(name)
#     assert module
#     for attr in module.attributes:
#         set_markdown(attr)
#         assert "][__mkapi__.examples.styles.google.module_level_v" in attr.name.markdown


# def test_set_markdown_default():
#     src = 'def f(x:int=0,y:str="x",z:str=""): pass'
#     node = ast.parse(src).body[0]
#     assert isinstance(node, ast.FunctionDef)
#     func = create_function(node)
#     set_markdown(func)
#     assert func.parameters[0].default.markdown == "0"
#     assert func.parameters[1].default.markdown == "'x'"
#     assert func.parameters[2].default.markdown == "''"


# def test_set_markdown_alias():
#     name = "examples.styles"
#     module = load_module(name)
#     assert module
#     x = module.aliases[0]
#     set_markdown(x)
#     assert "][__mkapi__.examples.styles.ExampleClassGoogle" in x.name.markdown
#     x = module.aliases[1]
#     set_markdown(x)
#     assert "][__mkapi__.examples.styles.ExampleClassNumPy" in x.name.markdown


# def test_create_attribute_without_module(google):
#     module = _create_empty_module()
#     assigns = list(iter_assigns(google))
#     assert len(assigns) == 2
#     assign = get_by_name(assigns, "module_level_variable1")
#     assert assign
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "module_level_variable1"
#     assert not attr.type.expr
#     assert not attr.doc.text.str
#     assign = get_by_name(assigns, "module_level_variable2")
#     assert assign
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "module_level_variable2"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'int'"
#     assert attr.doc.text.str.startswith("Module level")
#     assert attr.doc.text.str.endswith("a colon.")


# def test_create_property_without_module(get):
#     node = get("ExampleClass")
#     assert node
#     assigns = list(iter_assigns(node))
#     assign = get_by_name(assigns, "readonly_property")
#     assert assign

#     module = _create_empty_module()
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "readonly_property"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'str'"
#     assert attr.doc.text.str.startswith("Properties should")
#     assert attr.doc.text.str.endswith("getter method.")
#     assign = get_by_name(assigns, "readwrite_property")
#     assert assign

#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "readwrite_property"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'list(str)'"
#     assert attr.doc.text.str.startswith("Properties with")
#     assert attr.doc.text.str.endswith("here.")


# def test_create_attribute_pep526_without_module(get):
#     node = get("ExamplePEP526Class")
#     assert node
#     assigns = list(iter_assigns(node))
#     assign = get_by_name(assigns, "attr1")
#     assert assign

#     module = _create_empty_module()
#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "attr1"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "str"
#     assert not attr.doc.text.str
#     assign = get_by_name(assigns, "attr2")
#     assert assign

#     attr = create_attribute(assign, module, None)
#     assert attr.name.str == "attr2"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "int"
#     assert not attr.doc.text.str


# def test_class_attribute(google, source, get):
#     module = _create_module("google", google, source)
#     node = get("ExampleClass")
#     assert node
#     cls = create_class(node, module, None)
#     assert not get_by_type(cls.doc.sections, Assigns)
#     attrs = cls.attributes
#     assert len(attrs) == 7
#     names = ["attr1", "attr2", "attr3", "attr4", "attr5", "readonly_property", "readwrite_property"]
#     section = get_by_type(cls.doc.sections, Attributes)
#     assert section
#     for x in [section.items, cls.attributes]:
#         for k, name in enumerate(names):
#             assert x[k].name.str == name
#     assert not get_by_name(cls.functions, "__init__")


# def test_create_module_attribute_with_module(google, source):
#     module = _create_module("google", google, source)
#     attrs = module.attributes
#     assert len(attrs) == 2
#     attr = attrs[0]
#     assert attr.name.str == "module_level_variable1"
#     assert attr.type.expr
#     assert ast.unparse(attr.type.expr) == "'int'"
#     assert attr.doc.text.str
#     assert attr.doc.text.str.startswith("Module level")
#     assert attr.doc.text.str.endswith("with it.")
#     assert not get_by_type(module.doc.sections, Assigns)


# def test_merge_items():
#     """'''test'''
#     def f(x: int = 0, y: str = 's') -> bool:
#         '''function.

#         Args:
#             x: parameter x.
#             z: parameter z.

#         Returns:
#             Return True.'''
#     """
#     src = inspect.getdoc(test_merge_items)
#     assert src
#     node = ast.parse(src).body[1]
#     assert isinstance(node, ast.FunctionDef)
#     func = create_function(node)
#     assert get_by_name(func.parameters, "x")
#     assert get_by_name(func.parameters, "y")
#     assert not get_by_name(func.parameters, "z")
#     items = get_by_name(func.doc.sections, "Parameters").items  # type: ignore
#     assert get_by_name(items, "x")
#     assert not get_by_name(items, "y")
#     assert get_by_name(items, "z")
#     assert [item.name.str for item in items] == ["x", "z"]
#     assert func.returns[0].type
#     items = get_by_name(func.doc.sections, "Returns").items  # type: ignore
#     assert items[0].text.str == "Return True."
#     assert items[0].type.expr.id == "bool"  # type: ignore
