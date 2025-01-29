import yaml
from astdoc.utils import is_package


def test_pattern():
    from mkapi.nav import API_URI_PATTERN

    m = API_URI_PATTERN.match("<a/b/c>/d.e.f")
    assert m
    assert m.groups() == ("<a/b/c>", "d.e.f")
    m = API_URI_PATTERN.match("<a/b/c.d>/e.f")
    assert m
    assert m.groups() == ("<a/b/c.d>", "e.f")
    assert not API_URI_PATTERN.match("<a/b/c>d.e.f")
    m = API_URI_PATTERN.match("$a/b/c/d.e.f")
    assert m
    assert m.groups() == ("$a/b/c", "d.e.f")
    m = API_URI_PATTERN.match("$a/b.c/d.e.f")
    assert m
    assert m.groups() == ("$a/b.c", "d.e.f")
    m = API_URI_PATTERN.match("$a/b.c/d.e/f")
    assert m
    assert m.groups() == ("$a/b.c/d.e", "f")


def test_get_apinav():
    from mkapi.nav import get_apinav

    assert get_apinav("mkdocs", 0) == ["mkdocs"]
    assert get_apinav("invalid name", 0) == []
    nav = get_apinav("mkdocs", 1)
    assert 12 <= len(nav) <= 13
    assert nav[0] == "mkdocs"
    assert nav[1] == "mkdocs.commands"
    assert nav[-2] == "mkdocs.plugins"
    assert nav[-1] == "mkdocs.theme"
    nav = get_apinav("mkdocs", 2)
    x = len(nav)
    assert x > 30
    assert nav[0] == "mkdocs"
    assert nav[1] == "mkdocs.commands"
    assert nav[2] == "mkdocs.commands.build"
    i = nav.index("mkdocs.config")
    assert i
    assert nav[i + 1] == "mkdocs.config.base"
    nav = get_apinav("mkdocs", 3)
    assert len(nav) == 1
    assert nav[0]["mkdocs"][0] == "mkdocs"
    assert nav[0]["mkdocs"][1]["mkdocs.commands"][0] == "mkdocs.commands"


def test_gen_apinav():
    from mkapi.nav import gen_apinav, get_apinav

    nav = get_apinav("mkdocs", 2)
    n = len(nav)
    nav = get_apinav("mkdocs", 3)
    assert len([x for x in gen_apinav(nav) if not x[1]]) == n  # type: ignore


def test_update_apinav():
    from mkapi.nav import get_apinav, update_apinav

    def section(name: str, depth: int) -> str:
        return name.replace(".", "-" * depth)

    def page(name: str, depth: int) -> str | dict[str, str]:
        if is_package(name):
            return name.upper() + ".md"
        return {name: f"api{depth}/{name}.md"}

    nav = get_apinav("mkdocs", 2)
    update_apinav(nav, page)
    assert "MKDOCS.COMMANDS.md" in nav
    assert {"mkdocs.config.base": "api0/mkdocs.config.base.md"} in nav
    nav = get_apinav("mkdocs", 3)
    update_apinav(nav, page, section)
    assert "MKDOCS.md" in nav[0]["mkdocs"][0]
    assert "mkdocs-commands" in nav[0]["mkdocs"][1]


src = """
- index.md
- <api1>/mkapi.page
- A:
  - 1.md
  - <api2>/mkapi.**
  - 2.md
  - <api2>/mkapi.***
  - 3.md
- B: $api3/mkdocs.**
- C: $api3/mkdocs.***
"""


def test_build_apinav_empty():
    from mkapi.nav import build_apinav

    def create_apinav(*_):
        return []

    nav = yaml.safe_load(src)
    nav = build_apinav(nav, create_apinav)
    assert nav == ["index.md", {"A": ["1.md", "2.md", "3.md"]}, {"B": []}, {"C": []}]


def test_build_apinav_single():
    from mkapi.nav import build_apinav

    def create_apinav(*_):
        return ["a.md"]

    nav = yaml.safe_load(src)
    nav = build_apinav(nav, create_apinav)
    assert nav[:2] == ["index.md", "a.md"]
    assert nav[2] == {"A": ["1.md", "a.md", "2.md", "a.md", "3.md"]}
    assert nav[3] == {"B": "a.md"}
    assert nav[4] == {"C": "a.md"}


def test_build_apinav_dict():
    from mkapi.nav import build_apinav

    def create_apinav(*_):
        return ["m.md", {"X": "x.md"}, "n.md"]

    nav = yaml.safe_load(src)
    nav = build_apinav(nav, create_apinav)
    assert {"C": ["m.md", {"X": "x.md"}, "n.md"]} in nav


def test_update_nav():
    from mkapi.nav import update_nav

    def create_page(name: str, path: str) -> str:
        return f"{path}/{name}.md"

    def page_title(name: str, depth) -> str:
        return name.upper() + f".{depth}"

    nav = yaml.safe_load(src)
    update_nav(nav, create_page, page_title=page_title)
    assert "MKAPI.PAGE.0" in nav[1]
    assert nav[1]["MKAPI.PAGE.0"] == "api1/mkapi.page.md"
