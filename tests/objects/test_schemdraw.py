from mkapi.objects import _get_fullname, aliases, get_object


def test_get_object():
    assert get_object("schemdraw")
    x = get_object("schemdraw.svgconfig")
    assert x
    assert _get_fullname(x) == "schemdraw.backends.svg.config"
    x = get_object("schemdraw.Drawing")
    assert x
    assert _get_fullname(x) == "schemdraw.schemdraw.Drawing"

    a = aliases["schemdraw.schemdraw.Drawing"]
    assert len(a) >= 2
