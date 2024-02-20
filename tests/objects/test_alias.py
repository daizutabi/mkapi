def test_a():
    class B:
        pass

    class A:
        a: int = 1

        def f(self):
            pass

    import collections.abc

    print(collections.abc.__file__)
    assert 0
