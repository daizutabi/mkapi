from mkapi.objects import Class, get_object


def test_inherit():
    cls = get_object("mkapi.objects.Member")
    assert isinstance(cls, Class)
    print(cls)
    print(cls.bases)
    print(cls.attributes)
    print(cls.functions)
    assert 0
