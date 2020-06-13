from mkapi.core import linker


def test_get_link_private():
    class A:
        def func(self):
            pass

        def _private():
            pass

    q = "test_get_link_private.<locals>.A"
    m = "test_core_linker"
    assert linker.get_link(A) == f"[{q}](!{m}.{q})"
    assert linker.get_link(A, include_module=True) == f"[{m}.{q}](!{m}.{q})"
    assert linker.get_link(A.func) == f"[{q}.func](!{m}.{q}.func)"
    assert linker.get_link(A._private) == f"{q}._private"


def test_resolve_link():
    assert linker.resolve_link("[A](!!a)", "", []) == "[A](a)"
    assert linker.resolve_link("[A](!a)", "", []) == "A"
    assert linker.resolve_link("[A](a)", "", []) == "[A](a)"


def test_resolve_href():
    assert linker.resolve_href("", "", []) == ""


def test_resolve_object():
    html = "<p><a href='a'>p</a></p>"
    context = linker.resolve_object(html)
    assert context == {"heading_id": "", "level": 0, "prefix_url": "", "name_url": "a"}
    html = "<p><a href='./a'>p</a><a href='b'>n</a></p>"
    context = linker.resolve_object(html)
    assert context == {"heading_id": "", "level": 0, "prefix_url": "a", "name_url": "b"}
