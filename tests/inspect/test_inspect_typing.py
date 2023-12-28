from collections.abc import Callable
from typing import Self

from mkapi.inspect.signature import Signature
from mkapi.inspect.typing import type_string


def test_type_string():
    assert type_string(list) == "list"
    assert type_string(tuple) == "()"
    assert type_string(dict) == "dict"
    assert type_string(Callable) == "[Callable](!collections.abc.Callable)"
    assert type_string(Signature) == "[Signature](!mkapi.inspect.signature.Signature)"
    assert type_string(Self) == "[Self](!typing.Self)"
