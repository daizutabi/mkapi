import ast

import mkapi.ast
from mkapi.objects import load_module


def test_set_markdown():
    module = load_module("mkapi.objects")
    assert module
    module.set_markdown()
    x = [t.markdown for t in module.types]
    assert "list[[Item][__mkapi__.mkapi.docstrings.Item]]" in x
    assert "[Path][__mkapi__.pathlib.Path] | None" in x
    assert "NotImplementedError" in x
    assert "[InitVar][__mkapi__.dataclasses.InitVar][str | None]" in x

    for type in module.types:
        assert isinstance(type.markdown, str)
        print(type.markdown)

    assert 0
