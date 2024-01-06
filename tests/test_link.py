# import typing

# from mkapi.link import get_link, resolve_link, resolve_object


# def test_get_link_private():
#     class A:
#         def func(self):
#             pass

#         def _private(self):
#             pass

#     q = "test_get_link_private.<locals>.A"
#     m = "test_link"
#     assert get_link(A) == f"[{q}](!{m}.{q})"
#     assert get_link(A, include_module=True) == f"[{m}.{q}](!{m}.{q})"
#     assert get_link(A.func) == f"[{q}.func](!{m}.{q}.func)"  # type: ignore
#     assert get_link(A._private) == f"{q}._private"  # type: ignore  # noqa: SLF001


# def test_get_link_typing():
#     assert get_link(typing.Self) == "[Self](!typing.Self)"


# def test_resolve_link():
#     assert resolve_link("[A](!!a)", "", []) == "[A](a)"
#     assert resolve_link("[A](!a)", "", []) == "A"
#     assert resolve_link("[A](a)", "", []) == "[A](a)"


# def test_resolve_object():
#     html = "<p><a href='a'>p</a></p>"
#     context = resolve_object(html)
#     assert context == {"heading_id": "", "level": 0, "prefix_url": "", "name_url": "a"}
#     html = "<p><a href='./a'>p</a><a href='b'>n</a></p>"
#     context = resolve_object(html)
#     assert context == {"heading_id": "", "level": 0, "prefix_url": "a", "name_url": "b"}
