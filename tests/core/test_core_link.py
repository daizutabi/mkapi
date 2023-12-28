from mkapi.core import link


def test_get_link_private():
    class A:
        def func(self):
            pass

        def _private(self):
            pass

    q = "test_get_link_private.<locals>.A"
    m = "test_core_link"
    assert link.get_link(A) == f"[{q}](!{m}.{q})"
    assert link.get_link(A, include_module=True) == f"[{m}.{q}](!{m}.{q})"
    assert link.get_link(A.func) == f"[{q}.func](!{m}.{q}.func)"
    assert link.get_link(A._private) == f"{q}._private"


def test_resolve_link():
    assert link.resolve_link("[A](!!a)", "", []) == "[A](a)"
    assert link.resolve_link("[A](!a)", "", []) == "A"
    assert link.resolve_link("[A](a)", "", []) == "[A](a)"


def test_resolve_object():
    html = "<p><a href='a'>p</a></p>"
    context = link.resolve_object(html)
    assert context == {"heading_id": "", "level": 0, "prefix_url": "", "name_url": "a"}
    html = "<p><a href='./a'>p</a><a href='b'>n</a></p>"
    context = link.resolve_object(html)
    assert context == {"heading_id": "", "level": 0, "prefix_url": "a", "name_url": "b"}
