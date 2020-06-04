from IPython.display import HTML
from markdown import Markdown

import mkapi

converter = Markdown()


def render(obj):
    node = mkapi.get_node(obj)
    markdown = node.get_markdown()
    html = converter.convert(markdown)
    node.set_html(html)
    html = node.render()
    return HTML(html)
