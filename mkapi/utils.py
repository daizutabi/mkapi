from IPython.display import HTML
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
    return HTML(get_html(name))
