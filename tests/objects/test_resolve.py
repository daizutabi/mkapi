# def test_get_object():
#     from mkapi.objects import Class, Function, create_module, get_object

#     module = create_module("mkapi.objects")
#     a = get_object("mkapi.objects")
#     assert module is a
#     c = get_object("mkapi.objects.Object")
#     f = get_object("mkapi.objects.Module.__post_init__")
#     assert isinstance(c, Class)
#     assert c.module == "mkapi.objects"
#     assert isinstance(f, Function)
#     assert f.module == "mkapi.objects"
#     c2 = get_object("mkapi.objects.Object")
#     f2 = get_object("mkapi.objects.Module.__post_init__")
#     assert c is c2
#     assert f is f2
#     m1 = create_module("mkdocs.structure.files")
#     m2 = create_module("mkdocs.structure.files")
#     assert m1 is m2
#     assert get_object("examples.styles.ExampleClassGoogle")

# def test_resolve_examples():
#     from mkapi.objects import resolve

#     name = "examples.styles.google"
#     x = resolve(name)
#     assert x
#     assert x[0] == name
#     assert x[1] is None
#     name = "examples.styles.google.ExampleClass"
#     x = resolve(name)
#     assert x
#     assert x[0] == "ExampleClass"
#     assert x[1] == "examples.styles.google"
#     name = "examples.styles.ExampleClassGoogle"
#     x = resolve(name)
#     assert x
#     assert x[0] == "ExampleClassGoogle"
#     assert x[1] == "examples.styles"
#     name = "examples.styles.ExampleClassGoogle.attr1"
#     x = resolve(name)
#     assert x
#     assert x[0] == "ExampleClassGoogle.attr1"
#     assert x[1] == "examples.styles"
#     assert not resolve("x")
#     assert not resolve("examples.styles.X")
#     assert not resolve("examples.styles.ExampleClassGoogle.attrX")


# def test_resolve_tqdm():
#     from mkapi.objects import resolve

#     x = resolve("tqdm.tqdm")
#     assert x
#     assert x[0] == "tqdm"
#     assert x[1] == "tqdm"
#     assert x[2].fullname == "tqdm.std.tqdm"


# def test_resolve_jinja2():
#     from mkapi.objects import resolve

#     x = resolve("jinja2.Template")
#     assert x
#     assert x[0] == "Template"
#     assert x[1] == "jinja2"
#     assert x[2].fullname == "jinja2.environment.Template"


# def test_resolve_mkdocs():
#     from mkapi.objects import resolve

#     x = resolve("mkdocs.config.Config")
#     assert x
#     assert x[0] == "Config"
#     assert x[1] == "mkdocs.config"
#     assert x[2].fullname == "mkdocs.config.base.Config"


# def test_resolve_mkapi():
#     from mkapi.objects import resolve

#     x = resolve("mkapi.objects.ast")
#     assert x
#     assert x[0] == "ast"
#     assert x[1] == "mkapi.objects"
#     assert x[2].fullname == "ast"

#     assert not resolve("mkapi.objects.ast.ClassDef")


# def test_resolve_from_object():
#     from mkapi.objects import get_object, resolve_from_object

#     x = get_object("mkapi.objects")
#     assert x
#     r = resolve_from_object("Object", x)
#     assert r == "mkapi.objects.Object"
#     x = get_object(r)
#     assert x
#     r = resolve_from_object("__repr__", x)
#     assert r
#     x = get_object(r)
#     assert x
#     r = resolve_from_object("__post_init__", x)
#     assert r
#     x = get_object(r)
#     assert x
#     r = resolve_from_object("Object", x)
#     assert r

# def test_iter():
#     from mkapi.objects import create_module

#     a = create_module("examples.styles")
#     assert a
#     b = create_module("examples.styles.google")
#     assert b

#     x = a.get("ExampleClassGoogle")
#     assert x
#     print(x, id(x), x.node)

#     x = b.get("ExampleClass")
#     assert x
#     print(x, id(x), x.node)
#     assert 0

# def test_iter_objects_predicate():


#     module = create_module("mkapi.plugins")
#     assert module
#     cls = module.get("MkAPIPlugin")
#     assert isinstance(cls, Class)
#     x = list(iter_objects(cls))
#     members = ["MkAPIPlugin", "on_nav", "pages"]
#     others = ["load_config", "config"]
#     for name in members:
#         assert get_by_name(x, name)
#     for name in others:
#         assert get_by_name(x, name)

#     def predicate(obj, parent):
#         if parent is None:
#             return True

#         return obj.module is parent.module

#     x = list(iter_objects(cls, predicate=predicate))
#     for name in members:
#         assert get_by_name(x, name)
#     for name in others:
#         assert not get_by_name(x, name)


# def test_iter_object_package():
#     module = create_module("examples.styles")
#     assert module
#     for x in iter_objects(module):
#         print(x)
