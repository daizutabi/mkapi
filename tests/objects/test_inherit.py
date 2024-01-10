from mkapi.objects import Class, get_object


def test_inherit():
    cls = get_object("mkapi.objects.Member")
    assert isinstance(cls, Class)
    print(cls)
    print(cls.bases)
    print(cls.attributes)
    print(cls.functions)


def test_it():
    def f(it):
        next(it)

    it = iter(range(11))
    for x in it:
        f(it)
        print(x)
    assert 0
