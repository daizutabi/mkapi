import yaml

from mkapi.nav import (
    _split_path_name_filters,
    create_nav,
    gen_apinav,
    get_apinav,
    update_apinav,
    update_nav,
)
from mkapi.utils import is_package


def test_get_apinav():
    assert get_apinav("mkdocs") == ["mkdocs"]
    assert get_apinav("invalid name") == []
    nav = get_apinav("mkdocs.*")
    assert len(nav) == 13
    assert nav[0] == "mkdocs"
    assert nav[1] == "mkdocs.commands"
    assert nav[-2] == "mkdocs.plugins"
    assert nav[-1] == "mkdocs.theme"
    nav = get_apinav("mkdocs.**")
    x = len(nav)
    assert x > 50
    assert nav[0] == "mkdocs"
    assert nav[1] == "mkdocs.commands"
    assert nav[2] == "mkdocs.commands.build"
    assert (i := nav.index("mkdocs.config"))
    assert nav[i + 1] == "mkdocs.config.base"
    nav = get_apinav("mkdocs.***")
    assert len(nav) == 1
    assert nav[0]["mkdocs"][0] == "mkdocs"
    assert nav[0]["mkdocs"][1]["mkdocs.commands"][0] == "mkdocs.commands"


def test_get_nav():
    nav = get_apinav("mkdocs.**")
    n = len(nav)
    nav = get_apinav("mkdocs.***")
    assert len([x for x in gen_apinav(nav) if not x[1]]) == n  # type: ignore


def test_update_apinav():
    def section(name: str, depth: int) -> str:
        return name.replace(".", "-" * depth)

    def page(name: str, depth: int) -> str | dict[str, str]:
        if is_package(name):
            return name.upper() + ".md"
        return {name: f"api{depth}/{name}.md"}

    nav = get_apinav("mkdocs.**")
    update_apinav(nav, page)
    assert "MKDOCS.COMMANDS.md" in nav
    assert {"mkdocs.config.base": "api0/mkdocs.config.base.md"} in nav
    nav = get_apinav("mkdocs.***")
    update_apinav(nav, page, section)
    assert "MKDOCS.md" in nav[0]["mkdocs"][0]
    assert "mkdocs-commands" in nav[0]["mkdocs"][1]


src = """
- index.md
- <api1>/mkapi.objects|f1|f2
- A:
  - 1.md
  - <api2>/mkapi.**|f3
  - 2.md
  - <api2>/mkapi.***|f3
  - 3.md
- B: <api3>/mkdocs.**|f4
- C: <api3>/mkdocs.***|f4
"""


def test_nav_empty():
    def create_apinav(_):
        return []

    nav = yaml.safe_load(src)
    nav = create_nav(nav, create_apinav)
    assert nav == ["index.md", {"A": ["1.md", "2.md", "3.md"]}, {"B": []}, {"C": []}]


def test_nav_single():
    def create_apinav(_):
        return ["a.md"]

    nav = yaml.safe_load(src)
    nav = create_nav(nav, create_apinav)
    assert nav[:2] == ["index.md", "a.md"]
    assert nav[2] == {"A": ["1.md", "a.md", "2.md", "a.md", "3.md"]}
    assert nav[3] == {"B": "a.md"}
    assert nav[4] == {"C": "a.md"}


def test_nav_dict():
    def create_apinav(_):
        return ["m.md", {"X": "x.md"}, "n.md"]

    nav = yaml.safe_load(src)
    nav = create_nav(nav, create_apinav)
    assert {"C": ["m.md", {"X": "x.md"}, "n.md"]} in nav


def test_split_path_name_filters():
    path, name, filters = _split_path_name_filters("<a/b/c>/d.e.f|g|h|i")
    assert path == "a/b/c"
    assert name == "d.e.f"
    assert filters == ["g", "h", "i"]


def test_update_nav():
    def create_page(name: str, depth: int, path: str, filters: list[str]) -> str:
        return name.upper() + ".".join(filters) + path + f".{depth}"

    nav = yaml.safe_load(src)
    nav = update_nav(nav, create_page)
    assert "MKAPI.OBJECTSf1.f2api1/mkapi.objects.md.0" in nav[1]
