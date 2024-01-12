from mkapi.objects import load_module


def test_set_markdown_objects():
    module = load_module("mkapi.objects")
    assert module
    module.set_markdown()
    x = [t.markdown for t in module.types]
    assert "list[[Item][__mkapi__.mkapi.docstrings.Item]]" in x
    assert "[Path][__mkapi__.pathlib.Path] | None" in x
    assert "NotImplementedError" in x
    assert "[InitVar][__mkapi__.dataclasses.InitVar][str | None]" in x


def test_set_markdown_plugins():
    module = load_module("mkapi.plugins")
    assert module
    module.set_markdown()
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
    module.set_markdown()
    x = [t.markdown for t in module.types]
    assert "[Config][__mkapi__.mkdocs.config.base.Config]" in x
    assert "[T][__mkapi__.mkdocs.config.base.T]" in x
    assert "[ValidationError][__mkapi__.mkdocs.config.base.ValidationError]" in x
    assert "[IO][__mkapi__.typing.IO]" in x
    assert "[PlainConfigSchema][__mkapi__.mkdocs.config.base.PlainConfigSchema]" in x
    assert "str | [IO][__mkapi__.typing.IO] | None" in x
    assert "[Iterator][__mkapi__.typing.Iterator][[IO][__mkapi__.typing.IO]]" in x
