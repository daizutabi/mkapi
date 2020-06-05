from IPython.display import HTML
from markdown import Markdown

from mkapi.core.node import get_node

converter = Markdown()


def get_html(name):
    node = get_node(name)
    markdown = node.get_markdown()
    html = converter.convert(markdown)
    node.set_html(html)
    return node.render()


def display(name):
    return HTML(get_html(name))
