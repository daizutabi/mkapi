from typing import Iterator, Tuple


def split_type(markdown: str) -> Tuple[str, str]:
    line = markdown.split("\n")[0]
    if ":" in line:
        index = line.index(":")
        type = line[:index].strip()
        markdown = markdown[index + 1 :].strip()
        return type, markdown
    else:
        return "", markdown


def strip_ptags(html: str) -> str:
    html = html.replace("<p>", "").replace("</p>", "<br>")
    if html.endswith("<br>"):
        html = html[:-4]
    return html


def convert(text: str) -> str:
    blocks = []
    for block in split(text):
        if block.startswith(">>>"):
            block = f"~~~python\n{block}\n~~~\n"
        blocks.append(block)
    return "\n".join(blocks).strip()


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


def admonition(name: str, markdown: str) -> str:
    if name.startswith("Note"):
        type = "note"
    elif name.startswith("Warning"):
        type = "warning"
    else:
        type = name.lower()
    lines = ["    " + line if line else "" for line in markdown.split("\n")]
    lines.insert(0, f'!!! {type} "{name}"')
    return "\n".join(lines)
