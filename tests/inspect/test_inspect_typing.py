from collections.abc import Callable

from mkapi.inspect.signature import Signature
from mkapi.inspect.typing import type_string


def test_to_string():
    assert type_string(list) == "list"
    assert type_string(tuple) == "tuple"
    assert type_string(dict) == "dict"
    assert type_string(Callable) == "[Callable](!collections.abc.Callable)"
    assert type_string(Signature) == "[Signature](!mkapi.inspect.signature.Signature)"
