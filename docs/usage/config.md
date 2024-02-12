# Configuration

## Exclude modules

You can skip generation of documentation for some
specific modules with the plugin's `exclude` setting:

```yaml title="mkdocs.yml"
plugins:
  - mkapi:
      exclude:
        - altair.vegalite
```

For example, in the above setting,
`altair.vegalite` package and its submodules are excluded.
This feature is useful to skip test modules,
unnecessary modules, or huge modules.

## Configuration script

You can customize the plugin behaviors with
the plugin's `config` setting:

```yaml title="mkdocs.yml"
plugins:
  - mkapi:
      config: config.py
```

`config.py` script file should be located in the same
directory of `mkdocs.yml` like below:

``` sh
.
├─ docs/
│  └─ index.md
├─ config.py
└─ mkdocs.yml
```

!!! Note
    - You can chage the script name.
    - If the config file is a module and importable,
      you can write as `config: modulename`
      without `.py` extension.

Currently, five funtions can be called from MkAPI plugin.
You can define your own functions to customize plugin behaviors
or Navigation title for section, page, and/or toc.

<!-- ```python title="config.py"
--8<-- "config.py"
``` -->

```python title="config.py"
"""Config functions."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig

    from mkapi.plugins import MkAPIPlugin


def before_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    """Called before `on_config` event of MkAPI plugin."""


def after_on_config(config: MkDocsConfig, plugin: MkAPIPlugin) -> None:
    """Called after `on_config` event of MkAPI plugin."""


def page_title(name: str, depth: int) -> str:
    """Return a page title."""
    return name


def section_title(name: str, depth: int) -> str:
    """Return a section title."""
    return name


def toc_title(name: str, depth: int) -> str:
    """Return a toc title."""
    return name.split(".")[-1]  # Remove prefix. Default behavior.
```

## Features setting

MkAPI can be used any MkDocs theme.
However
[Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
is the best choice because of its navigation features.
Recommended settings are as below:

<div class="annotate" markdown="1">

```yaml title="mkdocs.yml"
theme:
  name: material (1)
  features:
    - content.tooltips (2)
    - navigation.expand (3)
    - navigation.indexes (4)
    - navigation.sections (5)
    - navigation.tabs (6)
```

</div>

1. Use [material theme](https://squidfunk.github.io/mkdocs-material/getting-started/).

2. MkAPI display object fullnames as tooltips. See
   [Improved tooltips](https://squidfunk.github.io/mkdocs-material/reference/tooltips/?h=too#improved-tooltips).

3. Subpackages or submodules are automatically expanded.
   See [Navigation expansion](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#navigation-expansion).

4. Package section can have its own summary or overview page.
   See [Section index pages](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#section-index-pages).

5. Packages are rendered as groups in the sidebar.
   See [Navigation sections](<https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#navigation-sections>).

6. API section can be placed in a menu layer. See
   [Navigation tabs](<https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/?h=navigation#navigation-tabs>).
