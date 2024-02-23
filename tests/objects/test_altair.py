from mkapi.objects import get_fullname, get_object


def test_get_object():
    assert get_object("altair")
    assert get_object("altair.to_csv")
    assert get_object("altair.pd")
    obj = get_object("altair.Type")
    assert obj
    assert get_fullname(obj) == "altair.vegalite.v5.schema.core.Type"
