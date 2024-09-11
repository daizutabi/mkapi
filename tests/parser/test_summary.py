def test_classes_fom_module():
    from mkapi.parser import create_classes_from_module

    name = "mkapi.node"
    section = create_classes_from_module(name)
    assert section
    assert section.name == "Classes"
    assert section.items[0].name == "[Node][mkapi.node.Node]"


def test_classes_from_module_alias():
    from mkapi.parser import create_classes_from_module

    name = "examples.styles"
    section = create_classes_from_module(name)
    assert section
    assert section.name == "Classes"
    name = "[ExampleClassGoogle][examples.styles.ExampleClassGoogle]"
    assert section.items[0].name == name
    assert section.items[0].text.startswith("The summary")


def test_functions_from_module():
    from mkapi.parser import create_functions_from_module

    name = "mkapi.node"
    section = create_functions_from_module(name)
    assert section
    assert section.name == "Functions"
    it = (i.name for i in section.items)
    assert any(r"[iter\_child\_nodes][mkapi.node.iter_child_nodes]" in n for n in it)


def test_methods_from_class():
    from mkapi.parser import create_methods_from_class

    section = create_methods_from_class("MkApiPlugin", "mkapi.plugin")
    assert section
    assert section.name == "Methods"
    it = (i.name for i in section.items)
    assert any(r"[on\_nav][mkapi.plugin.MkApiPlugin.on_nav]" in n for n in it)
