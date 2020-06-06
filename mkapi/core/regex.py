import re

LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")

MKAPI_PATTERN = re.compile(r"^!\[mkapi\]\((.+?)\)$", re.MULTILINE)

NODE_PATTERN = re.compile(
    r"<!-- mkapi:(\d+):begin -->(.*?)<!-- mkapi:end -->", re.MULTILINE | re.DOTALL
)


def node_markdown(index: int, markdown: str) -> str:
    return f"<!-- mkapi:{index}:begin -->\n\n{markdown}\n\n<!-- mkapi:end -->"
