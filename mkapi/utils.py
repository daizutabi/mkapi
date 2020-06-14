from markdown import Markdown

converter = Markdown()


def get_indent(line: str) -> int:
    indent = 0
    for x in line:
        if x != " ":
            return indent
        indent += 1
    return -1


def join(lines):
    indent = get_indent(lines[0])
    return "\n".join(line[indent:] for line in lines).strip()


def get_html(node):
    from mkapi.core.node import Node, get_node

    if not isinstance(node, Node):
        node = get_node(node)
    markdown = node.get_markdown()
    html = converter.convert(markdown)
    node.set_html(html)
    return node.get_html()


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
