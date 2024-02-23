from mkapi.objects import get_object


def test_get_object():
    assert get_object("schemdraw.svgconfig")
    assert get_object("schemdraw.Drawing")
