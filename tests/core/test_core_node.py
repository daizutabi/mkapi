from mkapi.core.module import get_module
from mkapi.core.node import get_kind, get_node, get_node_from_module, is_member


def test_generator():
    node = get_node("examples.styles.google.gen")
    assert node.object.kind == "generator"


def test_class():
    node = get_node("examples.styles.google.ExampleClass")
    assert node.object.prefix == "examples.styles.google"
    assert node.object.name == "ExampleClass"
    assert node.object.kind == "class"
    assert len(node) == 3
    p = node.members[-1]
    assert p.object.type.name == "list[int]"
    assert p.docstring.sections[0].markdown.startswith("Read-write property")


def test_dataclass():
    node = get_node("examples.styles.google.ExampleDataClass")
    assert node.object.prefix == "examples.styles.google"
    assert node.object.name == "ExampleDataClass"
    assert node.object.kind == "dataclass"


def test_is_member_private():
    class A:
        def _private(self):
            pass

        def func(self):
            pass

    class B(A):
        def _private(self):
            pass

    assert is_member(A._private) == -1  # noqa: SLF001
    assert is_member(A.func) == 0
    assert is_member(B.func) == 0


def test_is_member_source_file_index():
    node = get_node("mkapi.core.node.Node")
    assert node["__getitem__"].sourcefile_index == 1

    node = get_node("mkapi.core.base")
    assert node["Inline"].sourcefile_index == 0


def test_get_markdown():
    node = get_node("mkapi.core.base.Base")
    markdown = node.get_markdown()
    parts = [x.strip() for x in markdown.split("<!-- mkapi:sep -->")]
    x = "[mkapi.core.base](!mkapi.core.base).[Base](!mkapi.core.base.Base)"
    assert parts[0] == x
    assert parts[1] == "Base class."
    markdown = node.get_markdown(level=2)
    parts = [x.strip() for x in markdown.split("<!-- mkapi:sep -->")]
    x = "[mkapi.core.base](!mkapi.core.base).[Base](!mkapi.core.base.Base)"
    assert parts[0] == "## " + x

    def callback(_):
        return "123"

    markdown = node.get_markdown(callback=callback)
    parts = [x.strip() for x in markdown.split("<!-- mkapi:sep -->")]
    assert all(x == "123" for x in parts)


def test_set_html_and_render():
    node = get_node("mkapi.core.base.Base")
    markdown = node.get_markdown()
    sep = "<!-- mkapi:sep -->"
    n = len(markdown.split(sep))
    html = sep.join(str(x) for x in range(n))
    node.set_html(html)
    for k, x in enumerate(node):
        assert x.html == str(k)

    html = node.get_html()

    assert html.startswith('<div class="mkapi-node" id="mkapi.core.base.Base">')
    assert 'mkapi-object-kind dataclass top">dataclass</div>' in html
    assert '<div class="mkapi-object-body dataclass top">' in html
    assert '<code class="mkapi-object-prefix">mkapi.core.base.</code>' in html
    assert '<code class="mkapi-object-name">Base</code>' in html
    assert '<code class="mkapi-object-parenthesis">(</code>' in html
    assert '<code class="mkapi-object-signature">name=&#39;&#39;</code>, ' in html
    assert '<code class="mkapi-object-signature">markdown=&#39;&#39;</code>' in html
    assert '<div class="mkapi-section-body">1</div>' in html
    assert '<span class="mkapi-item-description">2</span></li>' in html
    assert '<code class="mkapi-object-name">set_html</code>' in html
    assert '<li><code class="mkapi-item-name">html</code>' in html


def test_package():
    node = get_node("mkapi.core")
    assert node.object.kind == "package"


def test_repr():
    node = get_node("mkapi.core.base")
    assert repr(node) == "Node('mkapi.core.base', num_sections=2, num_members=6)"


def test_get_kind():
    class A:
        def __getattr__(self, name):
            raise KeyError

    assert get_kind(A()) == ""


def test_get_node_from_module():
    _ = get_module("mkapi.core")
    x = get_node("mkapi.core.base.Base.__iter__")
    y = get_node("mkapi.core.base.Base.__iter__")
    assert x is not y
    x = get_node_from_module("mkapi.core.base.Base.__iter__")
    y = get_node_from_module("mkapi.core.base.Base.__iter__")
    assert x is y


def test_get_markdown_bases():
    node = get_node("examples.cls.inherit.Sub")
    markdown = node.get_markdown()
    parts = [x.strip() for x in markdown.split("<!-- mkapi:sep -->")]
    x = "[examples.cls.inherit.Base]"
    assert parts[1].startswith(x)


def test_set_html_and_render_bases():
    node = get_node("examples.cls.inherit.Sub")
    markdown = node.get_markdown()
    sep = "<!-- mkapi:sep -->"
    n = len(markdown.split(sep))
    html = sep.join(str(x) for x in range(n))
    node.set_html(html)
    html = node.get_html()
    assert "mkapi-section bases" in html


def test_decorated_member():
    from mkapi.inspect import attribute
    from mkapi.inspect.signature import Signature

    node = get_node(attribute)
    assert node.members[-1].object.kind == "function"
    assert get_node(Signature)["arguments"].object.kind == "readonly property"


def test_colon_in_docstring():
    """Issue#17"""

    class A:
        def func(self):
            """this: is not type."""

        @property
        def prop(self):
            """this: is type."""

    def func(self):
        """this: is not type."""

    node = get_node(A)
    assert node["func"].docstring[""].markdown == "this: is not type."
    assert node["prop"].docstring[""].markdown == "is type."
    assert node["prop"].object.type.name == "this"
    assert not node["prop"].docstring.type.name

    node = get_node(func)
    assert node.docstring[""].markdown == "this: is not type."
    assert not node.object.type


def test_short_filter():
    node = get_node("mkapi.core.base.Base")
    markdown = node.get_markdown()
    sep = "<!-- mkapi:sep -->"
    n = len(markdown.split(sep))
    html = sep.join(str(x) for x in range(n))
    node.set_html(html)
    html = node.get_html(filters=["short"])
    sub = '"mkapi-object-body dataclass top"><code class="mkapi-object-name">Base'
    assert sub in html
    assert "prefix" not in html
