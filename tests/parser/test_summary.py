def test_classes_fom_module():
    from mkapi.parser import create_classes_from_module

    name = "mkapi.node"
    section = create_classes_from_module(name)
    assert section
    assert section.name == "Classes"
    name = "[Node][__mkapi__.mkapi.node.Node]"
    assert section.items[0].name == name


def test_classes_from_module_alias():
    from mkapi.parser import create_classes_from_module

    name = "examples._styles"
    section = create_classes_from_module(name)
    assert section
    assert section.name == "Classes"
    name = "[ExampleClassGoogle][__mkapi__.examples._styles.ExampleClassGoogle]"
    assert section.items[0].name == name
    assert section.items[0].text.startswith("The summary")


def test_functions_from_module():
    from mkapi.parser import create_functions_from_module

    name = "mkapi.node"
    section = create_functions_from_module(name)
    assert section
    assert section.name == "Functions"
    names = [i.name for i in section.items]
    name = "[iter\\_child\\_nodes][__mkapi__.mkapi.node.iter_child_nodes]"
    assert any(name in n for n in names)


def test_methods_from_class():
    from mkapi.parser import create_methods_from_class

    section = create_methods_from_class("MkApiPlugin", "mkapi.plugin")
    assert section
    assert section.name == "Methods"
    names = [i.name for i in section.items]
    name = "[on\\_nav][__mkapi__.mkapi.plugin.MkApiPlugin.on_nav]"
    assert any(name in n for n in names)


def test_methods_from_class_property():
    from mkapi.parser import create_methods_from_class

    assert not create_methods_from_class("Object", "mkapi.object")


def test_modules_from_module_file():
    from mkapi.parser import create_modules_from_module_file

    section = create_modules_from_module_file("examples.sub")
    assert section
    assert section.name == "Modules"
    names = [i.name for i in section.items]
    assert len(names) == 3
    name = "[examples.sub.subsub][__mkapi__.examples.sub.subsub]"
    assert any(name in n for n in names)
    assert all("_pmod" not in n for n in names)


def test_modules_from_module_file_not_package():
    from mkapi.parser import create_modules_from_module_file

    section = create_modules_from_module_file("examples.mod_a")
    assert not section
