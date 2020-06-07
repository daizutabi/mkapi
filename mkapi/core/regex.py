import re

LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")

MKAPI_PATTERN = re.compile(r"^(#*) *?!\[mkapi\]\((.+?)\)$", re.MULTILINE)

NODE_PATTERN = re.compile(
    r"<!-- mkapi:begin:(\d+):(\w+) -->(.*?)<!-- mkapi:end -->", re.MULTILINE | re.DOTALL
)


def node_markdown(index: int, markdown: str, upper: bool = False) -> str:
    return f"<!-- mkapi:begin:{index}:{upper} -->\n\n{markdown}\n\n<!-- mkapi:end -->"
