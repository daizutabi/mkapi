from markdown import Markdown

converter = Markdown()


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
