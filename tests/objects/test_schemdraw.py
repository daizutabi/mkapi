from mkapi.objects import aliases, get_fullname, get_object


def test_get_object():
    assert get_object("schemdraw")
    x = get_object("schemdraw.svgconfig")
    assert x
    assert get_fullname(x) == "schemdraw.backends.svg.config"
    x = get_object("schemdraw.Drawing")
    assert x
    assert get_fullname(x) == "schemdraw.schemdraw.Drawing"

    assert aliases["schemdraw.schemdraw.Drawing"]
