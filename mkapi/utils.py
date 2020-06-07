from markdown import Markdown

from mkapi.core.node import Node, get_node

converter = Markdown()


def get_html(node):
    if not isinstance(node, Node):
        node = get_node(node)
    markdown = node.get_markdown()
    html = converter.convert(markdown)
    node.set_html(html)
    return node.render()


def display(name):
    from IPython.display import HTML

    return HTML(get_html(name))


def filter(name):
    """
    Examples:
        >>> filter("a.b.c")
        ('a.b.c', [])
        >>> filter("a.b.c|upper|strict")
        ('a.b.c', ['upper', 'strict'])
    """
    index = name.find("|")
    if index == -1:
        return name, []
    name, filters = name[:index], name[index + 1 :]
    return name, filters.split("|")
