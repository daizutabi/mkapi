import markdown

from mkapi.importlib import get_object
from mkapi.renderers import load_templates, render, templates


def test_load_templates():
    load_templates()
    assert "object" in templates
    assert "source" in templates


def test_render():
    name = "polars.config.Config.set_tbl_cell_alignment"
    obj = get_object(name)
    assert obj
    m = render(obj, 1, [])
    print(m)
    print("-" * 100)
    h = markdown.markdown(m, extensions=["md_in_html"])
    print(h)
    # assert 0
