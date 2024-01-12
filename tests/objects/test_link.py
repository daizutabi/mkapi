import re

from mkapi.objects import LINK_PATTERN, load_module


def test_set_markdown_objects():
    module = load_module("mkapi.objects")
    assert module
    x = [t.markdown for t in module.types]
    assert "list[[Item][__mkapi__.mkapi.docstrings.Item]]" in x
    assert "[Path][__mkapi__.pathlib.Path] | None" in x
    assert "NotImplementedError" in x
    assert "[InitVar][__mkapi__.dataclasses.InitVar][str | None]" in x


def test_set_markdown_plugins():
    module = load_module("mkapi.plugins")
    assert module
    x = [t.markdown for t in module.types]
    assert "[MkDocsConfig][__mkapi__.mkdocs.config.defaults.MkDocsConfig]" in x
    assert "[MkDocsPage][__mkapi__.mkdocs.structure.pages.Page]" in x
    assert "[MkAPIConfig][__mkapi__.mkapi.plugins.MkAPIConfig]" in x
    assert "[TypeGuard][__mkapi__.typing.TypeGuard][str]" in x
    assert "[Callable][__mkapi__.collections.abc.Callable] | None" in x


def test_set_markdown_bases():
    module = load_module("mkapi.plugins")
    assert module
    cls = module.get_class("MkAPIConfig")
    assert cls
    assert cls.bases
    cls = cls.bases[0]
    module = cls.module
    assert module
    x = [t.markdown for t in module.types]
    assert "[Config][__mkapi__.mkdocs.config.base.Config]" in x
    assert "[T][__mkapi__.mkdocs.config.base.T]" in x
    assert "[ValidationError][__mkapi__.mkdocs.config.base.ValidationError]" in x
    assert "[IO][__mkapi__.typing.IO]" in x
    assert "[PlainConfigSchema][__mkapi__.mkdocs.config.base.PlainConfigSchema]" in x
    assert "str | [IO][__mkapi__.typing.IO] | None" in x
    assert "[Iterator][__mkapi__.typing.Iterator][[IO][__mkapi__.typing.IO]]" in x


def test_link_pattern():
    def f(m: re.Match) -> str:
        name = m.group(1)
        if name == "abc":
            return f"[{name}][_{name}]"
        return m.group()

    assert re.search(LINK_PATTERN, "X[abc]Y")
    assert not re.search(LINK_PATTERN, "X[ab c]Y")
    assert re.search(LINK_PATTERN, "X[abc][]Y")
    assert not re.search(LINK_PATTERN, "X[abc](xyz)Y")
    assert not re.search(LINK_PATTERN, "X[abc][xyz]Y")
    assert re.sub(LINK_PATTERN, f, "X[abc]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc[abc]]Y") == "X[abc[abc][_abc]]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab]Y") == "X[ab]Y"
    assert re.sub(LINK_PATTERN, f, "X[ab c]Y") == "X[ab c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc] c]Y") == "X[abc][_abc] c]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][]Y") == "X[abc][_abc]Y"
    assert re.sub(LINK_PATTERN, f, "X[abc](xyz)Y") == "X[abc](xyz)Y"
    assert re.sub(LINK_PATTERN, f, "X[abc][xyz]Y") == "X[abc][xyz]Y"


def test_set_markdown_text():
    module = load_module("mkapi.objects")
    assert module
    x = [t.markdown for t in module.texts]
    assert "Add a [Type][__mkapi__.mkapi.objects.Type] instance." in x
