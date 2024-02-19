def test_a():
    class A:
        a: int = 1
        b, c = 1, 2

    print(A.a)
    print(A.b)
    assert 0
