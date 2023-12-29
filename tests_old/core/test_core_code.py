from mkapi.core.code import get_code


def test_code_repr():
    code = get_code('mkapi.core.base')
    assert repr(code) == "Code('mkapi.core.base')"
