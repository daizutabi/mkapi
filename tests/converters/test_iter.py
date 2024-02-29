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
