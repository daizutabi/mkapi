def test_get_object():
    from mkapi.objects import aliases, get_object

    assert get_object("schemdraw")
    assert "schemdraw.Drawing" in aliases["schemdraw.schemdraw.Drawing"]
    x = get_object("schemdraw.svgconfig")
    assert x
    assert x.fullname == "schemdraw.backends.svg.config"
    x = get_object("schemdraw.Drawing")
    assert x
    assert x.fullname == "schemdraw.schemdraw.Drawing"
