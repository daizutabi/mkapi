from mkapi.globals import get_all_from_importlib
from mkapi.items import Returns
from mkapi.objects import create_module
from mkapi.utils import get_by_name, get_by_type, get_module_node


def test_get_all_from_importlib():
    assert get_all_from_importlib("altair")


def test_docstring_return():
    name = "altair.utils.core"
    node = get_module_node(name)
    assert node
    module = create_module(name, node)
    assert module
    func = get_by_name(module.functions, "parse_shorthand")
    assert func
    assert func.returns[0].name
    assert func.returns[0].type.markdown
    assert func.returns[0].text.markdown
    section = get_by_type(func.doc.sections, Returns)
    assert section
    assert len(section.items) == 1
    item = section.items[0]
    assert item.name
    assert item.type.markdown
    assert item.text.markdown
