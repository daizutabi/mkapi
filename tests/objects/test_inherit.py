from mkapi.objects import Class, get_module, get_object
from mkapi.utils import get_by_name


def test_inherit():
    cls = get_object("mkapi.objects.Class")
    assert isinstance(cls, Class)
    assert cls.bases[0]
    assert cls.bases[0].name == "Callable"
    assert cls.bases[0].fullname == "mkapi.objects.Callable"
    a = cls.attributes
    assert len(a) == 15
    assert get_by_name(a, "_node")
    assert get_by_name(a, "qualname")
    assert get_by_name(a, "fullname")
    assert get_by_name(a, "modulename")
    assert get_by_name(a, "classnames")
    p = cls.parameters
    assert len(p) == 11
    assert get_by_name(p, "_node")
    assert not get_by_name(p, "qualname")
    assert not get_by_name(p, "fullname")
    assert not get_by_name(p, "modulename")
    assert not get_by_name(p, "classnames")


def test_inherit_other_module():
    cls = get_object("mkapi.plugins.MkAPIConfig")
    assert isinstance(cls, Class)
    assert cls.bases[0].fullname == "mkdocs.config.base.Config"
    a = cls.attributes
    x = get_by_name(a, "config_file_path")
    assert x
    assert x.fullname == "mkdocs.config.base.Config.config_file_path"


def test_inherit_other_module2():
    cls = get_object("mkapi.plugins.MkAPIPlugin")
    assert isinstance(cls, Class)
    f = cls.functions
    x = get_by_name(f, "on_pre_template")
    assert x
    p = x.parameters[1]
    assert p.unparse() == "template: jinja2.Template"
    m = p.get_module()
    assert m
    assert m.name == "mkdocs.plugins"
    assert m.get("get_plugin_logger")


def test_inherit_other_module3():
    m1 = get_module("mkdocs.plugins")
    assert m1
    a = "mkdocs.utils.templates.TemplateContext"
    assert m1.get_fullname("TemplateContext") == a
    assert m1.get_fullname("jinja2") == "jinja2"
    a = "jinja2.environment.Template"
    assert m1.get_fullname("jinja2.Template") == a
    m2 = get_module("jinja2")
    assert m2
    x = m2.get("Template")
    assert x
    assert x.fullname == a
