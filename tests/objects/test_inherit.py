from mkapi.objects import get_object


def test_inherit():
    cls = get_object("mkapi.objects.Class")
    print(cls)
    # assert 0
