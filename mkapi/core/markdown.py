from typing import Iterator

from markdown import Markdown

from mkapi.core.renderer import Renderer

converter = Markdown()
renderer = Renderer()


def convert(text: str, inline: bool) -> str:
    blocks = []
    for block in split(text):
        if block.startswith(">>>"):
            block = renderer.render_code(block)
        else:
            block = converter.convert(block).strip()
        blocks.append(block)
    text = "\n\n".join(blocks)
    html = converter.convert(text).strip()
    if inline:
        html = html.replace("<p>", "")
        html = html.replace("</p>", "<br>")
        if html.endswith("<br>"):
            html = html[:-4]
    return html


def delete_indent(lines, start, stop):
    from mkapi.core.docstring import get_indent

    indent = get_indent(lines[start])
    return "\n".join(x[indent:] for x in lines[start:stop]).strip()


def split(text: str) -> Iterator[str]:

    start = 0
    in_code = False
    lines = text.split("\n")
    for stop, line in enumerate(lines, 1):
        if ">>>" in line and not in_code:
            if start < stop - 1:
                yield "\n".join(lines[start : stop - 1])
            start = stop - 1
            in_code = True
        elif not line.strip() and in_code:
            yield delete_indent(lines, start, stop)
            start = stop
            in_code = False
    if start < len(lines):
        yield delete_indent(lines, start, len(lines))
