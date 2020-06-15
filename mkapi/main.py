import os
import sys

import click
from markdown import Markdown

from mkapi import __version__

pgk_dir = os.path.dirname(os.path.abspath(__file__))
version_msg = f"{__version__} from {pgk_dir} (Python {sys.version[:3]})."


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(version_msg, "-V", "--version")
def cli(ctx):
    pass


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
