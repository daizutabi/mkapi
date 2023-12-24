import re
from typing import List

LINK_PATTERN = re.compile(r"\[(.+?)\]\((.+?)\)")

MKAPI_PATTERN = re.compile(r"^(#*) *?!\[mkapi\]\((.+?)\)$", re.MULTILINE)

NODE_PATTERN = re.compile(
    r"<!-- mkapi:begin:(\d+):\[(.*?)\] -->(.*?)<!-- mkapi:end -->",
    re.MULTILINE | re.DOTALL,
)


def node_markdown(index: int, markdown: str, filters: List[str] = None) -> str:
    if filters:
        fs = "|".join(filters)
    else:
        fs = ""
    return f"<!-- mkapi:begin:{index}:[{fs}] -->\n\n{markdown}\n\n<!-- mkapi:end -->"
