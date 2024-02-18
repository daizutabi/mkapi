from mkapi.inspect import get_members_all_inspect
from mkapi.items import Returns
from mkapi.link import set_markdown
from mkapi.objects import _create_module
from mkapi.utils import get_by_name, get_by_type, get_module_node


def test_get_members_all_inspect():
    m = get_members_all_inspect("altair")
    assert "core" in m
    assert "layer" in m
    assert "Url" in m


def test_docstring_return():
    name = "altair.utils.core"
    node = get_module_node(name)
    assert node
    module = _create_module(name, node)
    assert module
    func = get_by_name(module.functions, "parse_shorthand")
    assert func
    set_markdown(func)
    assert func.returns[0].name
    assert func.returns[0].type.markdown
    assert not func.returns[0].text.markdown
    section = get_by_type(func.doc.sections, Returns)
    assert section
    assert len(section.items) == 1
    item = section.items[0]
    assert item.name
    assert item.type.markdown
    assert item.text.markdown
